use serde_json::Value;
use tauri::State;

use crate::sidecar::SidecarManager;

/// Универсальная RPC-команда: фронт → sidecar.
///   invoke('rpc', { method, params })
#[tauri::command]
pub async fn rpc(
    state: State<'_, SidecarManager>,
    method: String,
    params: Option<Value>,
) -> Result<Value, String> {
    state
        .send_request(method, params.unwrap_or(Value::Null))
        .await
}
