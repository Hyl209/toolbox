@echo off
setlocal

cd /d "%~dp0"

where npm >nul 2>nul
if errorlevel 1 (
  echo [ERROR] npm not found. Please install Node.js first.
  pause
  exit /b 1
)

if not exist "node_modules" (
  echo [INFO] Installing frontend dependencies...
  call npm install
  if errorlevel 1 (
    echo [ERROR] npm install failed.
    pause
    exit /b 1
  )
)

where cargo >nul 2>nul
if errorlevel 1 (
  echo [WARN] cargo not found. Starting web preview only: http://127.0.0.1:1420/
  echo [TIP] Install Rust/cargo if you want the real Tauri desktop window.
  call npm run dev -- --host 127.0.0.1
) else (
  echo [INFO] Starting Tauri desktop UI...
  call npm run tauri -- dev
)

pause
