use std::collections::HashMap;
use std::path::PathBuf;
use std::process::Stdio;
use std::sync::atomic::{AtomicU64, Ordering};
use std::sync::Arc;

use serde::Deserialize;
use serde_json::{json, Value};
use tauri::{AppHandle, Emitter};
use tokio::io::{AsyncBufReadExt, AsyncWriteExt, BufReader};
use tokio::process::{Child, ChildStdin, Command};
use tokio::sync::{mpsc, oneshot, Mutex};

/// Как запускать sidecar: bundled native binary (prod) или `node script.js` (dev/override).
pub enum SidecarInvocation {
    Native(PathBuf),
    Node(PathBuf),
}

impl SidecarInvocation {
    /// Определить вариант по расширению переданного пути (.js → Node, иначе Native).
    pub fn from_path(path: PathBuf) -> Self {
        if path.extension().and_then(|s| s.to_str()) == Some("js") {
            Self::Node(path)
        } else {
            Self::Native(path)
        }
    }

    fn path(&self) -> &PathBuf {
        match self {
            Self::Native(p) | Self::Node(p) => p,
        }
    }
}

/// Менеджер Nest sidecar'а: spawn, отправка JSON-RPC, маршрутизация ответов и notification → Tauri events.
pub struct SidecarManager {
    next_id: AtomicU64,
    writer_tx: mpsc::UnboundedSender<String>,
    pending: Arc<Mutex<HashMap<u64, oneshot::Sender<RpcResult>>>>,
    _child: Arc<Mutex<Child>>,
}

#[derive(Debug)]
pub enum RpcResult {
    Ok(Value),
    Err { code: i64, message: String, data: Option<Value> },
}

#[derive(Debug, Deserialize)]
struct JsonRpcResponse {
    id: Option<Value>,
    method: Option<String>,
    params: Option<Value>,
    result: Option<Value>,
    error: Option<RpcErrorPayload>,
}

#[derive(Debug, Deserialize)]
struct RpcErrorPayload {
    code: i64,
    message: String,
    data: Option<Value>,
}

impl SidecarManager {
    /// Spawn sidecar и запустить фоновые задачи writer + reader.
    /// initial_handshake — опциональный notification, отправляется сразу после spawn
    /// (используется для settings:loaded передачи provider/keys из Rust SQLite).
    pub async fn start(
        app: AppHandle,
        invocation: SidecarInvocation,
        initial_handshake: Option<(String, Value)>,
    ) -> Result<Self, String> {
        log::info!(
            "starting sidecar: {} {}",
            match &invocation {
                SidecarInvocation::Native(_) => "native",
                SidecarInvocation::Node(_) => "node",
            },
            invocation.path().display()
        );

        let mut cmd = match &invocation {
            SidecarInvocation::Native(p) => Command::new(p),
            SidecarInvocation::Node(p) => {
                let mut c = Command::new("node");
                c.arg(p);
                // Set CWD to backend root (<path>/dist/../) so NestConfigModule finds .env
                if let Some(backend_root) = p.parent().and_then(|d| d.parent()) {
                    c.current_dir(backend_root);
                }
                c
            }
        };

        let mut child = cmd
            .stdin(Stdio::piped())
            .stdout(Stdio::piped())
            .stderr(Stdio::inherit())
            .kill_on_drop(true)
            .spawn()
            .map_err(|e| format!("failed to spawn sidecar: {e}"))?;

        let stdin = child.stdin.take().ok_or("sidecar stdin unavailable")?;
        let stdout = child.stdout.take().ok_or("sidecar stdout unavailable")?;

        let pending: Arc<Mutex<HashMap<u64, oneshot::Sender<RpcResult>>>> =
            Arc::new(Mutex::new(HashMap::new()));

        let (writer_tx, writer_rx) = mpsc::unbounded_channel::<String>();
        tokio::spawn(writer_task(stdin, writer_rx));
        tokio::spawn(reader_task(stdout, app, pending.clone()));

        if let Some((method, params)) = initial_handshake {
            let line = json!({ "jsonrpc": "2.0", "method": method, "params": params });
            let serialized = format!("{}\n", line);
            if let Err(e) = writer_tx.send(serialized) {
                log::warn!("initial handshake failed: {e}");
            }
        }

        Ok(Self {
            next_id: AtomicU64::new(1),
            writer_tx,
            pending,
            _child: Arc::new(Mutex::new(child)),
        })
    }

    /// Отправить JSON-RPC request и дождаться ответа.
    pub async fn send_request(&self, method: String, params: Value) -> Result<Value, String> {
        let id = self.next_id.fetch_add(1, Ordering::SeqCst);
        let (tx, rx) = oneshot::channel::<RpcResult>();
        self.pending.lock().await.insert(id, tx);

        let line = json!({
            "jsonrpc": "2.0",
            "id": id,
            "method": method,
            "params": params,
        });

        let serialized = format!("{}\n", line);
        self.writer_tx
            .send(serialized)
            .map_err(|e| format!("sidecar writer channel closed: {e}"))?;

        match rx.await {
            Ok(RpcResult::Ok(value)) => Ok(value),
            Ok(RpcResult::Err { code, message, .. }) => Err(format!("[{code}] {message}")),
            Err(_) => Err("sidecar dropped the response channel".to_string()),
        }
    }

    /// Отправить JSON-RPC notification (без id) — например settings:loaded handshake.
    pub async fn send_notification(&self, method: String, params: Value) -> Result<(), String> {
        let line = json!({
            "jsonrpc": "2.0",
            "method": method,
            "params": params,
        });
        let serialized = format!("{}\n", line);
        self.writer_tx
            .send(serialized)
            .map_err(|e| format!("sidecar writer channel closed: {e}"))
    }
}

async fn writer_task(mut stdin: ChildStdin, mut rx: mpsc::UnboundedReceiver<String>) {
    while let Some(line) = rx.recv().await {
        if let Err(e) = stdin.write_all(line.as_bytes()).await {
            log::error!("sidecar stdin write failed: {e}");
            break;
        }
        if let Err(e) = stdin.flush().await {
            log::error!("sidecar stdin flush failed: {e}");
            break;
        }
    }
    log::info!("sidecar writer task exited");
}

async fn reader_task<R>(
    stdout: R,
    app: AppHandle,
    pending: Arc<Mutex<HashMap<u64, oneshot::Sender<RpcResult>>>>,
) where
    R: tokio::io::AsyncRead + Unpin + Send + 'static,
{
    let mut lines = BufReader::new(stdout).lines();
    while let Ok(Some(line)) = lines.next_line().await {
        let trimmed = line.trim();
        if trimmed.is_empty() {
            continue;
        }
        let parsed: Result<JsonRpcResponse, _> = serde_json::from_str(trimmed);
        let msg = match parsed {
            Ok(m) => m,
            Err(e) => {
                log::warn!("sidecar emitted non-JSON line: {e}: {trimmed}");
                continue;
            }
        };

        if let Some(id_val) = msg.id.as_ref() {
            let id = id_val.as_u64();
            if let Some(id) = id {
                let tx = pending.lock().await.remove(&id);
                if let Some(tx) = tx {
                    let result = if let Some(err) = msg.error {
                        RpcResult::Err {
                            code: err.code,
                            message: err.message,
                            data: err.data,
                        }
                    } else {
                        RpcResult::Ok(msg.result.unwrap_or(Value::Null))
                    };
                    let _ = tx.send(result);
                } else {
                    log::warn!("sidecar response for unknown id={id}");
                }
                continue;
            }
        }

        if let Some(method) = msg.method {
            let payload = msg.params.unwrap_or(Value::Null);
            if let Err(e) = app.emit(&method, payload) {
                log::warn!("failed to emit event {method}: {e}");
            }
        }
    }
    log::info!("sidecar reader task exited (stdout closed)");
}
