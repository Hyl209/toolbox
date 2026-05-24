@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
    echo 未找到 .venv\Scripts\python.exe
    echo 请先确认虚拟环境存在。
    pause
    exit /b 1
)
.\.venv\Scripts\python.exe -c "import PySide6" >nul 2>nul
if errorlevel 1 (
    echo 当前 .venv 缺少 PySide6，请先执行：
    echo .\.venv\Scripts\python.exe -m pip install PySide6
    echo.
    pause
    exit /b 1
)
.\.venv\Scripts\python.exe .\hyl_toolbox.py
if errorlevel 1 (
    echo.
    echo 工具启动失败，请检查 .venv 环境配置。
    pause
)
endlocal
