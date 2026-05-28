# Hyl Toolbox

[![Tests](https://github.com/Hyl209/toolbox/actions/workflows/tests.yml/badge.svg)](https://github.com/Hyl209/toolbox/actions/workflows/tests.yml)
[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/downloads/)
[![Platform](https://img.shields.io/badge/platform-Windows-lightgrey.svg)]()

PySide6 桌面工具箱，集成 11 种常用文件处理工具，支持暗色/亮色主题切换，自定义无边框窗口。

## 功能一览

| 工具 | 说明 |
|------|------|
| NCM 转 MP3 | 网易云音乐格式转换 |
| 图片伪装 | 将文件隐藏到 PNG 图片中 |
| MP4 转 MP3 | 视频提取音频 |
| 图片格式互转 | PNG / JPG / WEBP / BMP / ICO 等 |
| PDF 工具 | 合并、拆分、转图片等 |
| TG 下载 | Telegram 频道/群组视频下载 |
| 网页视频下载 | 支持 yt-dlp / aria2c 加速 |
| 批量命名 | 正则、序号、模板批量重命名 |
| 文件分类 | 按类型/扩展名自动归档 |
| 重复文件 | 精确哈希 + 视频指纹检测 |
| 图片 Base64 | 编解码互转 |

## 快速开始

```bash
# 克隆仓库
git clone https://github.com/Hyl209/toolbox.git
cd toolbox

# 安装依赖
pip install -r requirements.txt

# 启动
python hyl_toolbox.py
```

Windows 用户也可双击 `启动工具箱.bat` 直接运行。

## 打包发布

```bash
python generate_spec.py   # 从工具注册表自动生成 HylToolbox.spec
pyinstaller HylToolbox.spec
```

## 测试

```bash
pip install -r requirements-dev.txt

# 全量 (329 个用例)
python -m pytest --tb=short -q

# 单模块
python -m pytest tests/tests_toolbox.py -q        # 应用主流程
python -m pytest tests/tests_core.py -q           # 核心模块
python -m pytest tests/tests_tool_registry.py -q  # 注册表 + spec 一致性
python -m pytest tests/tests_services.py -q       # 服务层
```

## 项目结构

```
hyl-toolbox/
├── hyl_toolbox.py              # 主入口
├── toolbox_app/                # 核心框架
│   ├── tool_registry.py        # 工具注册表 (唯一来源)
│   ├── core/                   # 日志、路径、异常、Worker
│   ├── task_framework/         # 统一任务框架
│   ├── services/               # 服务层 (PDF、图片、视频等)
│   ├── widgets/                # 通用 UI 组件
│   ├── plugins/                # 插件系统
│   └── window.py               # 主窗口
│
├── modules/                    # 11 个工具模块
│   ├── ncm-converter/
│   ├── file-disguise/
│   ├── audio-extractor/
│   ├── image-converter/
│   ├── pdf-tools/
│   ├── video-downloader/       # 含 TG + 网页下载
│   ├── batch-rename/
│   ├── file-sorter/
│   ├── duplicate-finder/
│   └── base64/
│
├── config/                     # 配置管理
├── themes/                     # dark.qss / light.qss
├── tests/                      # pytest 测试套件
└── resources/                  # 图标、资源文件
```

## 架构设计

### 工具注册表

`toolbox_app/tool_registry.py` 是工具定义的唯一来源。`window.py` 从注册表动态构建侧栏和 Tab，新增工具只需在注册表中添加一条 `ToolDef`。

### Builder + 依赖注入

每个工具模块采用 builder 函数 + deps 字典模式，不直接 import PySide6，方便测试和解耦：

```python
def build_xxx_tab_class(deps: dict):
    QWidget = deps['QWidget']
    class XxxTab(BaseToolTab): ...
    return XxxTab
```

### 认证系统

- `password_policy.py` — 密码策略 (6-64 位 + 含字母 + 含数字)
- `auth_store.py` — SHA-256 哈希 + salt 存储
- `auth_preferences.py` — 记住密码、自动登录
- 默认账号 `admin`，默认密码 `123`

### 主题系统

全局 QSS 样式 (`themes/dark.qss` + `light.qss`)，主窗口 `toggle_theme()` 遍历所有 tab 调用 `apply_theme()` 协议。

## 技术栈

| 组件 | 技术 |
|------|------|
| GUI 框架 | PySide6 (Qt for Python) |
| PDF 处理 | PyMuPDF, pypdf, pdf2image |
| 图片处理 | Pillow |
| 音频处理 | mutagen, ncmdump |
| 视频下载 | yt-dlp, aria2c, Telethon |
| OCR | pytesseract |
| 打包 | PyInstaller |
| 测试 | pytest |

## 依赖

- **运行**: `pip install -r requirements.txt`
- **开发**: `pip install -r requirements-dev.txt` (额外包含 pytest)

## 许可证

本项目仅供个人学习使用。
