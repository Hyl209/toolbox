use std::collections::BTreeSet;
use std::env;
use std::fs;
use std::path::{Path, PathBuf};

const AUTH_AUTO_LOGIN_KEY: &str = "auth/auto_login";

fn normalize_path(path: impl AsRef<Path>) -> PathBuf {
    path.as_ref()
        .canonicalize()
        .unwrap_or_else(|_| path.as_ref().to_path_buf())
}

fn repo_root() -> Result<PathBuf, String> {
    let mut candidates = BTreeSet::new();
    if let Ok(cwd) = env::current_dir() {
        candidates.extend(cwd.ancestors().map(normalize_path));
    }
    candidates.extend(
        PathBuf::from(env!("CARGO_MANIFEST_DIR"))
            .ancestors()
            .map(normalize_path),
    );
    candidates
        .into_iter()
        .find(|path| path.join("hyl_toolbox.ini").exists() || path.join("hyl_toolbox.py").exists())
        .ok_or_else(|| "repo root not found".to_string())
}

#[tauri::command]
pub fn load_support_image() -> Result<String, String> {
    let base64_path = repo_root()?
        .join("modules")
        .join("ncm-converter")
        .join("weixin_base64.txt");
    let text = fs::read_to_string(base64_path).unwrap_or_default();
    let clean = text.trim();
    if clean.is_empty() {
        Ok(String::new())
    } else {
        Ok(format!("data:image/png;base64,{clean}"))
    }
}

#[tauri::command]
pub fn logout_current_user() -> Result<(), String> {
    let _settings_key = AUTH_AUTO_LOGIN_KEY;
    let settings_path = repo_root()?.join("hyl_toolbox.ini");
    let original = fs::read_to_string(&settings_path).unwrap_or_default();
    let mut lines = original.lines().map(str::to_string).collect::<Vec<_>>();
    let mut in_auth = false;
    let mut saw_auth = false;
    let mut wrote_auto_login = false;
    let mut insert_at = lines.len();

    for (index, line) in lines.iter_mut().enumerate() {
        let trimmed = line.trim();
        if trimmed.starts_with('[') && trimmed.ends_with(']') {
            if in_auth && !wrote_auto_login {
                insert_at = index;
            }
            in_auth = trimmed.eq_ignore_ascii_case("[auth]");
            saw_auth |= in_auth;
            continue;
        }
        if in_auth && trimmed.starts_with("auto_login=") {
            *line = "auto_login=0".to_string();
            wrote_auto_login = true;
        }
    }

    if !wrote_auto_login {
        if saw_auth {
            lines.insert(insert_at, "auto_login=0".to_string());
        } else {
            if !lines.is_empty() {
                lines.push(String::new());
            }
            lines.push("[auth]".to_string());
            lines.push("auto_login=0".to_string());
        }
    }

    fs::write(settings_path, format!("{}\n", lines.join("\n"))).map_err(|err| err.to_string())
}
