use serde::{Deserialize, Serialize};
use std::path::PathBuf;

#[derive(Clone, Debug, Deserialize, PartialEq, Serialize)]
pub struct DialogFilter {
    pub name: String,
    pub extensions: Vec<String>,
}

#[derive(Clone, Debug, Deserialize)]
pub struct DialogOptions {
    pub mode: String,
    pub title: Option<String>,
    pub default_path: Option<String>,
    #[serde(default)]
    pub filters: Vec<DialogFilter>,
    #[serde(default)]
    pub multiple: bool,
}

pub fn normalize_dialog_filters(filters: Vec<DialogFilter>) -> Vec<DialogFilter> {
    filters
        .into_iter()
        .filter_map(|filter| {
            let extensions: Vec<String> = filter
                .extensions
                .into_iter()
                .map(|ext| ext.trim().trim_start_matches('.').to_ascii_lowercase())
                .filter(|ext| !ext.is_empty())
                .collect();
            if extensions.is_empty() {
                return None;
            }
            Some(DialogFilter {
                name: filter.name,
                extensions,
            })
        })
        .collect()
}

#[tauri::command]
pub fn pick_path(options: DialogOptions) -> Result<Option<Vec<String>>, String> {
    let dialog = build_dialog(&options);
    let paths = match options.mode.as_str() {
        "file" if options.multiple => dialog.pick_files(),
        "file" => dialog.pick_file().map(|path| vec![path]),
        "directory" => dialog.pick_folder().map(|path| vec![path]),
        "save" => dialog.save_file().map(|path| vec![path]),
        other => return Err(format!("unknown dialog mode: {other}")),
    };
    Ok(paths.map(paths_to_strings))
}

fn build_dialog(options: &DialogOptions) -> rfd::FileDialog {
    let mut dialog = rfd::FileDialog::new();
    if let Some(title) = options
        .title
        .as_deref()
        .filter(|title| !title.trim().is_empty())
    {
        dialog = dialog.set_title(title);
    }
    if let Some(default_path) = options
        .default_path
        .as_deref()
        .filter(|path| !path.trim().is_empty())
    {
        dialog = dialog.set_directory(default_path);
    }
    for filter in normalize_dialog_filters(options.filters.clone()) {
        let extensions: Vec<&str> = filter.extensions.iter().map(String::as_str).collect();
        dialog = dialog.add_filter(&filter.name, &extensions);
    }
    dialog
}

fn paths_to_strings(paths: Vec<PathBuf>) -> Vec<String> {
    paths
        .into_iter()
        .map(|path| path.to_string_lossy().to_string())
        .collect()
}
