// Prevents additional console window on Windows in release, DO NOT REMOVE!!
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

mod dialogs;
mod sidecar;

#[tauri::command]
fn greet(name: &str) -> String {
    format!("Hello, {}! You've been greeted from Rust!", name)
}

fn main() {
    tauri::Builder::default()
        .plugin(tauri_plugin_opener::init())
        .invoke_handler(tauri::generate_handler![
            greet,
            dialogs::pick_path,
            sidecar::run_tool,
            sidecar::load_settings_snapshot,
            sidecar::save_settings_patch
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
