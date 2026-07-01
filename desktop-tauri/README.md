# Hyl Toolbox Tauri UI

这里是 Hyl Toolbox 的新版主线界面：**Tauri + React + TypeScript + Vite**。

旧版 PyQt / PySide6 前端已归档维护，新界面开发优先落在本目录。

## 启动

双击：

```text
start-new-ui.bat
```

或手动运行：

```powershell
npm run tauri -- dev
```

如果只需要网页预览：

```powershell
npm run dev -- --host 127.0.0.1
```

## 构建验证

```powershell
npm run build
npm run tauri -- build --debug --no-bundle
```

Debug 产物默认输出到：

```text
src-tauri/target/debug/desktop-tauri.exe
```

## 目录

```text
src/           React 前端
src-tauri/     Tauri Rust 桌面壳
start-new-ui.bat
```

## 维护范围

- UI 视觉、交互和工具页：`src/**`
- Tauri 桌面能力：`src-tauri/**`
- 本地工具调用链：仓库根目录 `sidecar/**`

默认不修改旧版 PyQt / PySide6 前端。