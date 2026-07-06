# Hyl Toolbox

Hyl Toolbox 现在以 **Tauri + React** 新版 UI 为主要开发方向。旧版 PyQt / PySide6 前端已进入归档维护状态，仅用于保留历史功能和兼容验证，不再作为主要界面迭代入口。

## 当前主线：新版 Tauri UI

新版界面位于：

```text
desktop-tauri/
```

启动方式：

```powershell
cd "desktop-tauri"
.\start-new-ui.bat
```

这个脚本会自动判断环境：

- 已安装 `cargo`：启动真正的 Tauri 桌面窗口。
- 未安装 `cargo`：启动 Web 预览，地址为 `http://127.0.0.1:1420/`。

手动启动也可以：

```powershell
cd "desktop-tauri"
npm run tauri -- dev
```

只看网页预览：

```powershell
cd "desktop-tauri"
npm run dev -- --host 127.0.0.1
```

## 旧版 PyQt / PySide6 前端

旧版入口仍保留在仓库中，但定位为归档版本：

```text
hyl_toolbox.py
toolbox_app/
modules/*/tab.py
modules/**/GUI 文件
```

旧版用于：

- 查询历史实现
- 回归对照
- 临时使用尚未迁移到 Tauri 的工具

默认不再改旧版 PyQt / PySide6 前端。新增 UI、视觉优化、主流程接入优先落到 `desktop-tauri/`。

## 新版目录结构

```text
desktop-tauri/
├─ src/                  # React 前端
│  ├─ api/               # Tauri / Web 调用适配
│  ├─ components/        # 新版 UI 壳和通用组件
│  └─ tools/             # 已迁移工具界面
├─ src-tauri/            # Tauri Rust 桌面壳
└─ start-new-ui.bat      # 新版 UI 启动脚本

sidecar/                 # 新版 UI 调用的本地 sidecar 能力
```

## 开发与验证

```powershell
cd "desktop-tauri"

# 前端类型检查与构建
npm run build

# Tauri Debug 构建，不打包安装器
npm run tauri -- build --debug --no-bundle
```

当前已验证新版 UI 可完成：

- React/Vite 构建
- Tauri Debug 构建
- Base64 工具在桌面端和 Web 预览下运行
- 玻璃拟态无边框 UI 渲染
- AI 生图在前端和 sidecar 两侧限制为后端支持尺寸：`auto`、`1024x1024`、`1536x1024`、`1024x1536`
- 设置页支持本地背景图，桌面端通过 Tauri asset protocol 读取绝对路径

## 技术栈

| 区域 | 技术 |
| --- | --- |
| 新版桌面 UI | Tauri 2 + React + TypeScript + Vite |
| 新版本地能力 | Rust Tauri command + sidecar |
| 旧版归档 UI | PyQt / PySide6 |
| 旧版打包 | PyInstaller |
| Python 测试 | pytest |

## 维护原则

- 新 UI 相关开发优先修改 `desktop-tauri/src/**`。
- 需要桌面能力时再联动 `desktop-tauri/src-tauri/**`。
- 需要本地工具链时再联动 `sidecar/**`。
- 默认不碰旧版 PyQt / PySide6 前端文件。
- 所有完成结论必须基于实际构建、测试或可复查输出。
