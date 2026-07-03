pub mod dialogs;
mod shell;
mod sidecar;

#[tauri::command]
fn greet(name: &str) -> String {
    format!("Hello, {}! You've been greeted from Rust!", name)
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_opener::init())
        .manage(sidecar::ToolSessionStore::default())
        .invoke_handler(tauri::generate_handler![
            greet,
            dialogs::pick_path,
            shell::load_support_image,
            shell::logout_current_user,
            sidecar::run_tool,
            sidecar::start_tool_session,
            sidecar::poll_tool_session,
            sidecar::control_tool_session,
            sidecar::cleanup_tool_session,
            sidecar::load_settings_snapshot,
            sidecar::save_settings_patch
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
