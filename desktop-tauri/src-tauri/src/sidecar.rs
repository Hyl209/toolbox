use serde_json::Value;
use std::collections::BTreeSet;
use std::env;
use std::ffi::OsString;
use std::path::{Path, PathBuf};
use std::time::{SystemTime, UNIX_EPOCH};
use tokio::io::{AsyncBufReadExt, AsyncReadExt, BufReader};
use tokio::process::Command;

#[tauri::command]
pub async fn run_tool(tool_id: String, input: Value) -> Result<Value, String> {
    run_sidecar(tool_id, input).await
}

#[tauri::command]
pub async fn load_settings_snapshot() -> Result<Value, String> {
    run_sidecar_command(vec![
        OsString::from("settings"),
        OsString::from("--snapshot"),
    ])
    .await
}

#[tauri::command]
pub async fn save_settings_patch(input: Value) -> Result<Value, String> {
    run_settings_update(input, None, None).await
}

async fn run_sidecar(tool_id: String, input: Value) -> Result<Value, String> {
    let input_path = temp_input_path();

    let input_json = serde_json::to_vec(&input).map_err(|err| err.to_string())?;
    std::fs::write(&input_path, input_json)
        .map_err(|err| format!("failed to write temp input {}: {err}", input_path.display()))?;

    let result = run_sidecar_command(vec![
        OsString::from("run"),
        OsString::from("--tool"),
        OsString::from(tool_id),
        OsString::from("--input"),
        input_path.clone().into_os_string(),
    ])
    .await;
    cleanup_temp(&input_path);
    result
}

async fn run_settings_update(
    input: Value,
    settings_path: Option<&Path>,
    plugins_dir: Option<&Path>,
) -> Result<Value, String> {
    let input_path = temp_input_path();

    let input_json = serde_json::to_vec(&input).map_err(|err| err.to_string())?;
    std::fs::write(&input_path, input_json)
        .map_err(|err| format!("failed to write temp input {}: {err}", input_path.display()))?;

    let mut args = vec![
        OsString::from("settings"),
        OsString::from("--update"),
        OsString::from("--input"),
        input_path.clone().into_os_string(),
    ];
    if let Some(path) = settings_path {
        args.push(OsString::from("--settings"));
        args.push(path.as_os_str().to_os_string());
    }
    if let Some(path) = plugins_dir {
        args.push(OsString::from("--plugins-dir"));
        args.push(path.as_os_str().to_os_string());
    }

    let result = run_sidecar_command(args).await;
    cleanup_temp(&input_path);
    result
}

#[cfg(test)]
async fn run_settings_update_with_paths(
    input: Value,
    settings_path: &Path,
    plugins_dir: &Path,
) -> Result<Value, String> {
    run_settings_update(input, Some(settings_path), Some(plugins_dir)).await
}

async fn run_sidecar_command(args: Vec<OsString>) -> Result<Value, String> {
    let invocation = resolve_sidecar_invocation()?;

    let mut command = Command::new(&invocation.program);
    command
        .args(&invocation.args)
        .args(&args)
        .current_dir(&invocation.current_dir)
        .env("PYTHONUTF8", "1")
        .env("PYTHONIOENCODING", "utf-8")
        .stdout(std::process::Stdio::piped())
        .stderr(std::process::Stdio::piped());

    let mut child = command.spawn().map_err(|err| {
        format!(
            "failed to spawn {} sidecar {}; current_dir={}; args_prefix={:?}; error={err}",
            invocation.mode,
            invocation.program.display(),
            invocation.current_dir.display(),
            invocation.args
        )
    })?;

    let stdout = child
        .stdout
        .take()
        .ok_or_else(|| "failed to capture sidecar stdout".to_string())?;
    let stderr = child
        .stderr
        .take()
        .ok_or_else(|| "failed to capture sidecar stderr".to_string())?;
    let stderr_task = tokio::spawn(async move {
        let mut text = String::new();
        let _ = BufReader::new(stderr).read_to_string(&mut text).await;
        text
    });

    let mut result = None;
    let mut progress = Vec::new();
    let mut lines = BufReader::new(stdout).lines();
    while let Some(line) = lines.next_line().await.map_err(|err| err.to_string())? {
        if line.trim().is_empty() {
            continue;
        }
        let event: Value = serde_json::from_str(&line).map_err(|err| {
            format!(
                "invalid sidecar stdout JSON: {}; line={}",
                err,
                summarize(&line)
            )
        })?;
        match event.get("type").and_then(Value::as_str) {
            Some("progress") => progress.push(event),
            Some("result") => result = Some(event.get("data").cloned().unwrap_or(event)),
            Some("error") => {
                let _ = child.wait().await;
                let _ = stderr_task.await;
                return Err(sidecar_error(&event));
            }
            other => {
                let _ = child.kill().await;
                let _ = stderr_task.await;
                return Err(format!("unknown sidecar event type: {other:?}"));
            }
        }
    }

    let status = child.wait().await.map_err(|err| err.to_string())?;
    let stderr = stderr_task.await.unwrap_or_default();

    if let Some(data) = result {
        return Ok(data);
    }

    Err(format!(
        "sidecar exited without result; status={status}; progress_events={}; stderr={}",
        progress.len(),
        summarize(&stderr)
    ))
}

struct SidecarInvocation {
    mode: &'static str,
    program: PathBuf,
    args: Vec<OsString>,
    current_dir: PathBuf,
}

fn resolve_sidecar_invocation() -> Result<SidecarInvocation, String> {
    if cfg!(debug_assertions) {
        resolve_dev_python()
    } else {
        resolve_release_exe()
    }
}

fn resolve_dev_python() -> Result<SidecarInvocation, String> {
    let roots = repo_root_candidates();
    for root in &roots {
        let script = root.join("sidecar").join("hyl_sidecar.py");
        if !script.is_file() {
            continue;
        }

        if let Ok(python) = env::var("HYL_SIDECAR_PYTHON") {
            let python = python.trim();
            if !python.is_empty() {
                return Ok(SidecarInvocation {
                    mode: "Python",
                    program: PathBuf::from(python),
                    args: vec![script.into_os_string()],
                    current_dir: root.clone(),
                });
            }
        }

        for python in [
            root.join(".venv").join("Scripts").join("python.exe"),
            root.join(".codex-test-venv")
                .join("Scripts")
                .join("python.exe"),
        ] {
            if python.is_file() {
                return Ok(SidecarInvocation {
                    mode: "Python",
                    program: python,
                    args: vec![script.into_os_string()],
                    current_dir: root.clone(),
                });
            }
        }

        if command_available("python", &["--version"]) {
            return Ok(SidecarInvocation {
                mode: "Python",
                program: PathBuf::from("python"),
                args: vec![script.into_os_string()],
                current_dir: root.clone(),
            });
        }

        if cfg!(windows) && command_available("py", &["-3", "--version"]) {
            return Ok(SidecarInvocation {
                mode: "Python launcher",
                program: PathBuf::from("py"),
                args: vec![OsString::from("-3"), script.into_os_string()],
                current_dir: root.clone(),
            });
        }
    }

    Err(format!(
        "Python sidecar not found; checked {}",
        roots
            .iter()
            .map(|root| {
                format!(
                    "[env=HYL_SIDECAR_PYTHON, .venv={}, .codex-test-venv={}, python={}, py={}, script={}]",
                    root.join(".venv")
                        .join("Scripts")
                        .join("python.exe")
                        .display(),
                    root.join(".codex-test-venv")
                        .join("Scripts")
                        .join("python.exe")
                        .display(),
                    PathBuf::from("python").display(),
                    PathBuf::from("py").display(),
                    root.join("sidecar").join("hyl_sidecar.py").display()
                )
            })
            .collect::<Vec<_>>()
            .join("; ")
    ))
}

fn command_available(program: &str, args: &[&str]) -> bool {
    std::process::Command::new(program)
        .args(args)
        .stdout(std::process::Stdio::null())
        .stderr(std::process::Stdio::null())
        .status()
        .map(|status| status.success())
        .unwrap_or(false)
}

fn resolve_release_exe() -> Result<SidecarInvocation, String> {
    let candidates = release_exe_candidates();
    for exe in &candidates {
        if exe.is_file() {
            let current_dir = exe
                .parent()
                .map(Path::to_path_buf)
                .unwrap_or_else(|| PathBuf::from("."));
            return Ok(SidecarInvocation {
                mode: "release",
                program: exe.clone(),
                args: Vec::new(),
                current_dir,
            });
        }
    }

    Err(format!(
        "release sidecar hyl_sidecar.exe not found; checked {}",
        candidates
            .iter()
            .map(|path| path.display().to_string())
            .collect::<Vec<_>>()
            .join("; ")
    ))
}

fn repo_root_candidates() -> Vec<PathBuf> {
    let mut candidates = BTreeSet::new();
    if let Ok(cwd) = env::current_dir() {
        candidates.extend(cwd.ancestors().map(normalize_path));
    }
    candidates.extend(
        PathBuf::from(env!("CARGO_MANIFEST_DIR"))
            .ancestors()
            .map(normalize_path),
    );
    candidates.into_iter().collect()
}

fn release_exe_candidates() -> Vec<PathBuf> {
    let mut candidates = BTreeSet::new();
    let mut add_for_root = |root: &Path| {
        candidates.insert(normalize_path(root.join("hyl_sidecar.exe")));
        candidates.insert(normalize_path(
            root.join("resources").join("hyl_sidecar.exe"),
        ));
        candidates.insert(normalize_path(
            root.join("dist")
                .join("hyl_sidecar")
                .join("hyl_sidecar.exe"),
        ));
    };

    if let Ok(exe) = env::current_exe() {
        if let Some(dir) = exe.parent() {
            for root in dir.ancestors() {
                add_for_root(root);
            }
        }
    }
    if let Ok(cwd) = env::current_dir() {
        for root in cwd.ancestors() {
            add_for_root(root);
        }
    }

    candidates.insert(normalize_path(
        PathBuf::from(env!("CARGO_MANIFEST_DIR"))
            .join("..")
            .join("..")
            .join("dist")
            .join("hyl_sidecar")
            .join("hyl_sidecar.exe"),
    ));
    candidates.into_iter().collect()
}

fn normalize_path(path: impl AsRef<Path>) -> PathBuf {
    path.as_ref()
        .canonicalize()
        .unwrap_or_else(|_| path.as_ref().to_path_buf())
}

fn temp_input_path() -> PathBuf {
    let nanos = SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .map(|duration| duration.as_nanos())
        .unwrap_or_default();
    env::temp_dir().join(format!("hyl-sidecar-{}-{nanos}.json", std::process::id()))
}

fn cleanup_temp(path: &Path) {
    let _ = std::fs::remove_file(path);
}

fn sidecar_error(event: &Value) -> String {
    let code = event
        .get("code")
        .and_then(Value::as_str)
        .unwrap_or("SIDECAR_ERROR");
    let message = event
        .get("message")
        .and_then(Value::as_str)
        .unwrap_or("sidecar error");
    format!("{code}: {message}")
}

fn summarize(text: &str) -> String {
    let text = text.trim();
    if text.is_empty() {
        return "<empty>".to_string();
    }
    text.chars().take(200).collect()
}

#[cfg(test)]
mod tests {
    use super::{load_settings_snapshot, run_settings_update_with_paths, run_tool};
    use serde_json::json;
    use std::path::PathBuf;
    use std::time::{SystemTime, UNIX_EPOCH};

    #[test]
    fn base64_encode_returns_data_text() {
        let result = tauri::async_runtime::block_on(run_tool(
            "base64".to_string(),
            json!({"task_id":"rust-base64-001","action":"encode_text","payload":{"text":"hello"}}),
        ))
        .expect("run_tool should return result data");

        assert_eq!(result, json!({"text":"aGVsbG8="}));
    }

    #[test]
    fn settings_snapshot_returns_legacy_tools() {
        let result = tauri::async_runtime::block_on(load_settings_snapshot())
            .expect("settings snapshot should return data");

        assert_eq!(result["ui"]["theme"], "dark");
        assert!(result["tools"]
            .as_array()
            .expect("tools should be an array")
            .iter()
            .any(|item| item["id"] == "base64"));
    }

    #[test]
    fn settings_update_uses_supplied_ini_and_returns_snapshot() {
        let temp_dir = unique_temp_dir("hyl-sidecar-settings-test");
        std::fs::create_dir_all(&temp_dir).expect("temp dir should be created");
        let settings_path = temp_dir.join("hyl_toolbox.ini");
        let plugins_dir = temp_dir.join("plugins");
        std::fs::write(&settings_path, "[ui]\ntheme=dark\ncustom_theme_enabled=0\n")
            .expect("seed settings should be written");

        let result = tauri::async_runtime::block_on(run_settings_update_with_paths(
            json!({"task_id":"rust-settings-001","updates":{"ui/theme":"light"}}),
            &settings_path,
            &plugins_dir,
        ))
        .expect("settings update should return fresh snapshot");

        assert_eq!(
            result["settings_path"].as_str(),
            Some(settings_path.to_string_lossy().as_ref())
        );
        assert_eq!(result["ui"]["theme"], "light");
        assert!(std::fs::read_to_string(&settings_path)
            .expect("settings should still exist")
            .contains("theme=light"));

        let _ = std::fs::remove_dir_all(temp_dir);
    }

    fn unique_temp_dir(prefix: &str) -> PathBuf {
        let nanos = SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .map(|duration| duration.as_nanos())
            .unwrap_or_default();
        std::env::temp_dir().join(format!("{prefix}-{}-{nanos}", std::process::id()))
    }
}
