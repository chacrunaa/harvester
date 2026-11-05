use rusqlite::{Connection, Result};
use std::sync::Mutex;

pub struct DbState(pub Mutex<Connection>);

pub fn open(path: &std::path::Path) -> Result<Connection> {
    let conn = Connection::open(path)?;
    conn.execute_batch("
        PRAGMA journal_mode = WAL;
        PRAGMA foreign_keys = ON;

        CREATE TABLE IF NOT EXISTS user_settings (
            key        TEXT PRIMARY KEY,
            value      TEXT NOT NULL,
            updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
        );

        INSERT OR IGNORE INTO user_settings (key, value)
        VALUES ('provider', 'deepseek');
    ")?;
    Ok(conn)
}

pub fn get_setting(conn: &Connection, key: &str) -> Option<String> {
    conn.query_row(
        "SELECT value FROM user_settings WHERE key = ?1",
        [key],
        |row| row.get(0),
    )
    .ok()
}

pub fn set_setting(conn: &Connection, key: &str, value: &str) -> Result<()> {
    conn.execute(
        "INSERT INTO user_settings (key, value, updated_at)
         VALUES (?1, ?2, strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
         ON CONFLICT(key) DO UPDATE SET
           value = excluded.value,
           updated_at = excluded.updated_at",
        [key, value],
    )?;
    Ok(())
}

/// Загрузить provider + все API-ключи (api_key.*) одним вызовом — для sidecar handshake.
pub fn load_full_settings(conn: &Connection) -> (String, std::collections::HashMap<String, String>) {
    let provider = get_setting(conn, "provider").unwrap_or_else(|| "deepseek".to_string());
    let mut keys = std::collections::HashMap::new();
    let mut stmt = match conn.prepare("SELECT key, value FROM user_settings WHERE key LIKE 'api_key.%'") {
        Ok(s) => s,
        Err(_) => return (provider, keys),
    };
    let rows = stmt.query_map([], |row| {
        let key: String = row.get(0)?;
        let value: String = row.get(1)?;
        Ok((key, value))
    });
    if let Ok(iter) = rows {
        for entry in iter.flatten() {
            if let Some(provider_name) = entry.0.strip_prefix("api_key.") {
                if !entry.1.is_empty() {
                    keys.insert(provider_name.to_string(), entry.1);
                }
            }
        }
    }
    (provider, keys)
}
