use std::collections::HashMap;

use serde::Serialize;
use tauri::State;

use crate::db::{get_setting, set_setting, DbState};

const PROVIDERS: &[&str] = &["claude", "codex", "deepseek", "gemini", "copilot", "kimi"];

#[derive(Serialize)]
pub struct SettingsDto {
    provider: String,
    #[serde(rename = "keyStatus")]
    key_status: HashMap<String, bool>,
}

fn read_dto(conn: &rusqlite::Connection) -> SettingsDto {
    let provider = get_setting(conn, "provider")
        .unwrap_or_else(|| "deepseek".to_string());

    let key_status = PROVIDERS
        .iter()
        .map(|&p| {
            let has_key = get_setting(conn, &format!("api_key.{}", p))
                .map(|v| !v.is_empty())
                .unwrap_or(false);
            (p.to_string(), has_key)
        })
        .collect();

    SettingsDto { provider, key_status }
}

#[tauri::command]
pub fn get_settings(state: State<DbState>) -> Result<SettingsDto, String> {
    let conn = state.0.lock().map_err(|e| e.to_string())?;
    Ok(read_dto(&conn))
}

#[tauri::command]
pub fn update_settings(
    state: State<DbState>,
    provider: Option<String>,
    api_key: Option<String>,
) -> Result<SettingsDto, String> {
    let conn = state.0.lock().map_err(|e| e.to_string())?;

    if let Some(ref p) = provider {
        if !PROVIDERS.contains(&p.as_str()) {
            return Err(format!("Unknown provider: {}", p));
        }
        set_setting(&conn, "provider", p).map_err(|e| e.to_string())?;
    }

    if let Some(ref key) = api_key {
        let target = provider.clone().unwrap_or_else(|| {
            get_setting(&conn, "provider").unwrap_or_else(|| "deepseek".to_string())
        });
        set_setting(&conn, &format!("api_key.{}", target), key)
            .map_err(|e| e.to_string())?;
    }

    Ok(read_dto(&conn))
}
