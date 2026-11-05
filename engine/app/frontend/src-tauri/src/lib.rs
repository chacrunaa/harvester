mod commands;
mod db;
mod sidecar;

use std::path::PathBuf;
use std::sync::Mutex;

use db::DbState;
use serde_json::json;
use sidecar::{SidecarInvocation, SidecarManager};
use tauri::Manager;

fn resolve_sidecar_invocation() -> Result<SidecarInvocation, String> {
    if let Ok(p) = std::env::var("HARVESTER_SIDECAR_PATH") {
        return Ok(SidecarInvocation::from_path(PathBuf::from(p)));
    }

    if cfg!(debug_assertions) {
        // dev fallback: node ../../backend/dist/main.js — позволяет работать без bundle:sidecar
        let manifest = env!("CARGO_MANIFEST_DIR");
        let path = PathBuf::from(manifest)
            .join("..")
            .join("..")
            .join("backend")
            .join("dist")
            .join("main.js");
        return Ok(SidecarInvocation::Node(path));
    }

    // prod: bundled native binary рядом с tauri exe (Tauri externalBin).
    // Tauri при упаковке отрезает {rust-triple} суффикс: исходник
    // `bin/harvester-sidecar-{triple}{ext}` копируется в bundle как
    // `harvester-sidecar{ext}`.
    let exe = tauri::utils::platform::current_exe()
        .map_err(|e| format!("current_exe: {e}"))?;
    let dir = exe
        .parent()
        .ok_or_else(|| "exe has no parent".to_string())?
        .to_path_buf();
    let bin = format!("harvester-sidecar{}", std::env::consts::EXE_SUFFIX);
    Ok(SidecarInvocation::Native(dir.join(bin)))
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .setup(|app| {
            if cfg!(debug_assertions) {
                app.handle().plugin(
                    tauri_plugin_log::Builder::default()
                        .level(log::LevelFilter::Info)
                        .build(),
                )?;
            }

            let data_dir = app
                .path()
                .app_data_dir()
                .expect("failed to resolve app_data_dir");

            std::fs::create_dir_all(&data_dir)
                .expect("failed to create app data directory");

            let db_path = data_dir.join("harvester.db");
            let conn = db::open(&db_path).expect("failed to open database");

            // Snapshot настроек для handshake — пока ещё держим conn.
            let (provider, keys) = db::load_full_settings(&conn);
            app.manage(DbState(Mutex::new(conn)));

            let handshake = (
                "settings:loaded".to_string(),
                json!({ "provider": provider, "keys": keys }),
            );

            let invocation = resolve_sidecar_invocation().expect("failed to resolve sidecar path");
            let app_handle = app.handle().clone();
            let manager = tauri::async_runtime::block_on(SidecarManager::start(app_handle, invocation, Some(handshake)))
                .expect("failed to start Nest sidecar");
            app.manage(manager);

            Ok(())
        })
        .invoke_handler(tauri::generate_handler![
            commands::settings::get_settings,
            commands::settings::update_settings,
            commands::rpc::rpc,
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
