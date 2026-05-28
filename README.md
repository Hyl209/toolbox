# 格式转换工具 · Hyl Toolbox

PySide6 桌面格式转换工具箱，支持 11 种工具，暗色/亮色主题切换，自定义无边框窗口。

## 项目结构

```
hyl tools/
├── hyl_toolbox.py              # 主入口，依赖注入 + 启动循环
├── conftest.py                 # pytest 全局 fixture (QApplication/offscreen)
├── generate_spec.py            # 从 tool_registry 自动生成 HylToolbox.spec
│
├── toolbox_app/                # 核心框架
│   ├── tool_registry.py        # 工具注册表 (唯一来源)
│   ├── core/                   # 核心基础设施层
│   │   ├── logger.py           # 公共日志 API (get_logger)
│   │   ├── config.py           # [deprecated] 旧版配置 → config.manager
│   │   ├── task_manager.py     # [deprecated] 旧版任务 → task_framework
│   │   ├── paths.py            # 路径管理器
│   │   ├── exceptions.py       # 异常体系
│   │   ├── worker.py           # 后台任务 Worker
│   │   └── ...                 # events, file_utils, performance, updater 等
│   │
│   ├── task_framework/         # 统一任务框架 (权威)
│   │   ├── manager.py          # TaskManager
│   │   └── ...                 # task, worker, queue, signals, qthread_adapter
│   │
│   ├── services/               # 服务层 (懒加载)
│   │   └── ...                 # pdf, image, video, ocr, download, file 等
│   │
│   ├── auth.py                 # 认证入口 (re-export)
│   ├── auth_store.py           # 用户存储 + 密码哈希
│   ├── password_policy.py      # 密码策略
│   ├── auth_preferences.py     # 登录偏好
│   ├── auth_dialog.py          # 登录对话框
│   │
│   ├── widgets/                # 通用 UI 组件 (拆分后)
│   │   ├── cards.py            # make_card, make_transparent_row
│   │   ├── dialogs.py          # ThemedMessageDialog, show_themed_*
│   │   ├── titlebar.py         # DragTitleBar, WindowControlButton
│   │   ├── dropzone.py         # DropZoneCard
│   │   ├── animation.py        # animate_fade, animate_stack_switch, pulse
│   │   ├── base_tab.py         # build_base_tool_tab_class
│   │   └── theme_helpers.py    # style_combo_popup
│   │
│   ├── plugins/                # 插件系统 (manifest-first 发现)
│   ├── window.py               # 主窗口 (消费 tool_registry)
│   └── ...
│
├── config/                     # 配置系统 (v2, 权威)
│   ├── manager.py              # ConfigManager
│   └── ...
│
├── logs/                       # 日志系统 (后端实现)
│   ├── manager.py              # LogManager
│   └── ...
│
├── video-downloader/           # 网页/TG 视频下载 (拆分后)
│   ├── models.py               # 数据类型
│   ├── _shared.py              # 共享工具
│   ├── source_parser.py        # URL 分类/任务解析
│   ├── progress.py             # 进度格式化
│   ├── telegram_backend.py     # Telethon 下载
│   ├── web_backend.py          # yt-dlp/aria2/ffmpeg 下载
│   ├── converter.py            # 薄代理层 (re-export)
│   ├── tab.py                  # Tab 主类
│   ├── tab_constants.py        # Tab 常量/样式
│   ├── tab_formatters.py       # Tab 格式化
│   ├── tab_workers.py          # Worker 工厂
│   ├── tab_panels.py           # UI 面板构建
│   └── tests_video_downloader.py
│
├── same/                       # 重复文件检测 (拆分后)
│   ├── _common.py              # 共享常量/工具
│   ├── exact_duplicate.py      # 精确重复检测
│   ├── video_signature.py      # 视频相似度
│   ├── move_plan.py            # 移动计划
│   ├── converter.py            # 薄代理层
│   └── tests_same_converter.py
│
├── music/                      # NCM 转 MP3
├── zipandpng/                  # 文件伪装
├── mp4-mp3/                    # MP4 转 MP3
├── image-convert/              # 图片格式互转
├── pdf-tools/                  # PDF 工具
├── name/                       # 批量文件命名
├── 分类/                        # 文件自动分类
├── base64/                     # Base64 编解码
│
├── themes/                     # 主题样式 (dark.qss / light.qss)
├── docs/                       # 文档
│   └── superpowers/plans/      # 优化计划
│
├── pyproject.toml              # pytest 配置 (basetemp + warning filter)
├── HylToolbox.spec             # PyInstaller 打包 (自动生成)
├── requirements.txt            # 运行依赖
├── requirements-dev.txt        # 测试依赖
└── tests_*.py                  # 集成测试 (329 个)
```

## 架构设计

### 工具注册表

`toolbox_app/tool_registry.py` 是工具定义的唯一来源：

```python
from toolbox_app.tool_registry import TOOL_DEFINITIONS, get_packaging_datas

# 所有工具定义
for tool in TOOL_DEFINITIONS:
    print(tool.id, tool.title, tool.sidebar_label)

# PyInstaller 打包清单 (自动生成)
datas = get_packaging_datas()
```

`window.py` 从注册表动态构建侧栏和 Tab，新增工具只需修改注册表。

### Builder / Deps 注入模式

每个工具模块采用 **builder 函数 + deps 字典** 的依赖注入模式：

```python
def build_xxx_tab_class(deps: dict):
    QWidget = deps['QWidget']
    class XxxTab(BaseToolTab):
        def __init__(self, settings):
            ...
    return XxxTab
```

好处：工具模块不直接 import PySide6，通过 deps 注入，方便测试和解耦。

### 认证系统

- `password_policy.py`：密码策略 (6-64 位 + 含字母 + 含数字)
- `auth_store.py`：SHA-256 哈希 + salt 存储
- `auth_preferences.py`：记住密码、自动登录
- 默认账号 `admin`，默认密码 `123`

> **注意**：现阶段密码模块纯属练手玩一下，安全性不做强要求，后续有需要再加强。

### 主题系统

- `themes/dark.qss` + `themes/light.qss` 全局样式
- `window.py` 的 `toggle_theme()` 遍历所有 tab 调用 `apply_theme()`
- 每个 tab 通过 `apply_theme()` 协议管理自己的样式

### 网页下载加速

`video-downloader/web_backend.py` 优化参数：
- aria2c: 16 连接、HTTP 管线化、异步 DNS、64MB 磁盘缓存
- yt-dlp: 16 并发分片、10MB 块大小、500KB 节流检测
- 自动模式: 速度→并发映射 (10Mbps→8, 5Mbps→6, 2Mbps→4)

## 运行

```bash
# 安装依赖
pip install -r requirements.txt

# 安装测试依赖
pip install -r requirements-dev.txt

# 启动
python hyl_toolbox.py

# 打包 (从注册表自动生成 spec)
python generate_spec.py
pyinstaller HylToolbox.spec
```

## 测试

```bash
# 全量测试 (329 个)
python -m pytest --tb=short -q

# 单模块测试
python -m pytest tests_toolbox.py -q       # 应用主流程
python -m pytest tests_core.py -q          # 核心模块
python -m pytest tests_tool_registry.py -q # 注册表 + spec 一致性
python -m pytest tests_services.py -q      # 服务层
python -m pytest video-downloader/tests_video_downloader.py -q  # 下载模块
```

## 工程优化记录

详见 `docs/superpowers/plans/code_review_optimization_direction.md`。

关键优化：
- **工具注册表**: `tool_registry.py` 作为唯一来源，window/spec 测试统一消费
- **模块拆分**: video-downloader 2147行→11 子模块, widgets 615行→7 子模块, same 605行→5 子模块
- **认证安全**: 移除 admin/123 密码豁免, 拆为 auth_store/password_policy/auth_preferences
- **插件安全**: manifest-first 发现, 不执行插件代码
- **测试稳定**: 329 项全绿, QApplication fixture, offscreen 渲染, 缺依赖显式 skip
- **下载加速**: aria2c/yt-dlp 参数调优, 自动并发映射
- **spec 自动生成**: `generate_spec.py` 从注册表生成, 不再手写
