# 格式转换工具 · Hyl Toolbox

PySide6 桌面格式转换工具箱，支持 11 种工具，暗色/亮色主题切换，自定义无边框窗口。

## 项目结构

```
hyl tools/
├── hyl_toolbox.py          # 主入口，依赖注入 + 启动循环
├── toolbox_app/            # 核心框架
│   ├── auth.py             # 认证逻辑（纯函数，无 Qt 依赖）
│   ├── auth_dialog.py      # 登录对话框
│   ├── dynamic_modules.py  # 动态模块注册表
│   ├── loaders.py          # 模块缓存加载器（线程安全）
│   ├── tool_tabs.py        # 分类/命名/视频下载 三个 tab 的接入
│   ├── utils.py            # 共享工具函数（save_setting、缓存键、文件分类等）
│   ├── widgets.py          # 通用 UI 组件（BaseToolTab、DropZoneCard、弹窗等）
│   └── window.py           # 主窗口（ToolboxWindow builder）
├── themes/
│   ├── dark.qss            # 暗色主题样式
│   └── light.qss           # 亮色主题样式
│
├── music/                  # NCM 转 MP3
│   ├── ncm_to_mp3.py       # 转换逻辑
│   ├── tab.py              # GUI 页签
│   └── tests_ncm_*.py      # 测试
├── zipandpng/              # 文件伪装（PNG/JPG/GIF/WEBP 封面）
│   ├── zipandpng.py        # 命令行工具 + 核心逻辑
│   ├── tab.py              # GUI 页签
│   └── tests/
├── mp4-mp3/                # MP4 转 MP3
│   ├── converter.py        # ffmpeg 转换
│   ├── config_store.py     # 配置持久化
│   ├── tab.py              # GUI 页签
│   └── app.py              # 独立 CLI
├── image-convert/          # 图片格式互转
│   ├── converter.py        # Pillow 转换逻辑
│   ├── tab.py              # GUI 页签
│   └── tests_image_convert.py
├── pdf-tools/              # PDF 工具（合并/拆分/转图/提取文字）
│   ├── converter.py        # pypdf + PyMuPDF 逻辑
│   ├── tab.py              # GUI 页签
│   └── tests_pdf_tools.py
├── video-downloader/       # 网页视频下载（TG + 通用网页）
│   ├── converter.py        # yt-dlp + aria2c + ffmpeg 下载引擎
│   ├── tab.py              # GUI 页签（含 TG API 集成）
│   └── tests_video_downloader.py
├── name/                   # 批量文件命名
│   ├── converter.py        # 命名规则引擎
│   └── tab.py              # GUI 页签
├── 分类/                    # 文件自动分类（按扩展名归类）
│   ├── converter.py        # 分类逻辑
│   └── tab.py              # GUI 页签
├── same/                   # 重复文件查找
│   ├── converter.py        # 哈希比对 + 视频指纹
│   └── tab.py              # GUI 页签
├── base64/                 # Base64 编解码
│   ├── converter.py        # 编解码逻辑
│   ├── tab.py              # GUI 页签
│   └── tests_base64_tools.py
│
├── pyproject.toml          # pytest 配置
├── HylToolbox.spec         # PyInstaller 打包配置
└── tests_*.py              # 根目录集成测试
```

## 架构设计

### Builder / Deps 注入模式

每个工具模块采用 **builder 函数 + deps 字典** 的依赖注入模式：

```python
# tab.py — 每个工具的 GUI 页签
def build_xxx_tab_class(deps: dict):
    QWidget = deps['QWidget']
    QPushButton = deps['QPushButton']
    # ... 从 deps 获取所有 Qt 类和工具函数
    
    class XxxTab(BaseToolTab):
        def __init__(self, settings):
            # 构建 UI
            ...
    
    return XxxTab
```

```python
# hyl_toolbox.py — 主入口组装所有依赖
XxxTab = _load_xxx_tab_module().build_xxx_tab_class({
    'QWidget': QWidget,
    'QPushButton': QPushButton,
    'QProgressBar': QProgressBar,
    # ... 传入所有需要的依赖
})
```

**好处：** 工具模块不直接 import PySide6，通过 deps 注入，方便测试和解耦。

### 模块加载

`toolbox_app/loaders.py` 提供 `load_module_once(name, path)`：
- 首次加载时通过 `importlib` 动态导入
- 加载成功后缓存，后续调用直接返回
- 线程安全（`RLock` 保护），缓存在 `exec_module` 成功后才写入

### 认证系统

- `auth.py`：纯函数，SHA-256 哈希 + salt 存储密码
- `auth_dialog.py`：登录对话框，支持记住密码、自动登录
- 默认账号 `admin`，首次登录后建议修改密码

### 主题系统

- `themes/dark.qss` + `themes/light.qss` 全局样式
- `window.py` 的 `toggle_theme()` 遍历所有 tab 调用 `apply_theme()`
- 每个 tab 通过 `apply_theme()` 协议管理自己的 combo 弹出层样式

### 通用组件 (`widgets.py`)

| 组件 | 说明 |
|------|------|
| `BaseToolTab` | 工具页签基类，提供输出目录行、日志、进度条等通用 UI |
| `DropZoneCard` | 拖拽区域卡片，支持文件/文件夹拖入 |
| `DragTitleBar` | 自定义无边框窗口标题栏 |
| `ThemedMessageDialog` | 主题一致的消息弹窗 |
| `show_themed_success/error/warning` | 统一弹窗入口 |

## 开发约定

1. **新功能先建子目录**，至少包含 `converter.py`；有界面再补 `tab.py`
2. **禁止根目录新增零散脚本**
3. **子目录不改旧模块**，只改明确要求的部分
4. **GUI 背景统一**：外层卡片 → 中间容器透明 → 控件本体 + viewport()

## 运行

```bash
# 安装依赖
pip install PySide6 pypdf PyMuPDF Pillow mutagen ncmdump python-docx

# 启动
python hyl_toolbox.py

# 打包
pyinstaller HylToolbox.spec
```

## 测试

```bash
# 全量测试
python -m pytest --tb=short -q

# 单模块测试
python -m pytest video-downloader/tests_video_downloader.py -q
python -m pytest music/tests_ncm_to_mp3.py -q
```

## 子模块独立 CLI

```bash
# 文件伪装
python zipandpng/zipandpng.py disguise cover.png payload.exe out.png
python zipandpng/zipandpng.py recover out.png recovered.exe
python zipandpng/zipandpng.py info out.png
```
