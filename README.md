# 格式转换工具 · Hyl Toolbox

PySide6 桌面格式转换工具箱，支持 11 种工具，暗色/亮色主题切换，自定义无边框窗口。

## 项目结构

```
hyl tools/
├── hyl_toolbox.py              # 主入口，依赖注入 + 启动循环
│
├── toolbox_app/                # 核心框架
│   ├── core/                   # 核心基础设施层
│   │   ├── logger.py           # 集中式日志系统
│   │   ├── config.py           # 统一配置管理器
│   │   ├── paths.py            # 路径管理器
│   │   ├── exceptions.py       # 异常体系 (7 个异常类)
│   │   ├── worker.py           # 后台任务 Worker
│   │   ├── task_manager.py     # 任务管理器
│   │   ├── file_utils.py       # 文件工具 (17 个方法)
│   │   ├── downloader_base.py  # 下载器基类
│   │   ├── events.py           # 事件系统
│   │   ├── ui_helpers.py       # UI 辅助工具
│   │   ├── performance.py      # 性能监控 (timer/内存)
│   │   ├── updater.py          # 自动更新架构
│   │   ├── i18n.py             # 多语言支持
│   │   ├── ai_interface.py     # AI 扩展接口
│   │   ├── gpu_manager.py      # GPU 加速管理
│   │   ├── crash_recovery.py   # 崩溃恢复
│   │   └── startup.py          # 启动管理器
│   │
│   ├── task_framework/         # 统一任务框架
│   │   ├── task.py             # Task 基类 (6 种状态)
│   │   ├── worker.py           # TaskWorker (线程)
│   │   ├── queue.py            # TaskQueue (并发控制)
│   │   ├── signals.py          # 信号系统 (6 种信号)
│   │   ├── manager.py          # TaskManager (高层 API)
│   │   └── qthread_adapter.py  # QThread 适配器
│   │
│   ├── services/               # 服务层
│   │   ├── mp4_service.py      # MP4→MP3 (包装 converter)
│   │   ├── base64_service.py   # Base64 编解码
│   │   ├── image_service.py    # 图片格式转换 (ImageMagick)
│   │   ├── pdf_service.py      # PDF 工具 (PyMuPDF/pypdf)
│   │   ├── duplicate_service.py # 重复文件检测
│   │   ├── hash_service.py     # 文件哈希计算
│   │   ├── video_service.py    # 视频处理
│   │   ├── ocr_service.py      # OCR 识别
│   │   ├── download_service.py # HTTP 下载
│   │   └── file_service.py     # 文件整理/重命名
│   │
│   ├── plugins/                # 插件系统
│   │   ├── base.py             # PluginBase + PluginInfo
│   │   ├── discovery.py        # 插件发现 (manifest.json)
│   │   ├── registry.py         # 插件注册/注销
│   │   ├── manager.py          # 插件管理器
│   │   ├── dynamic_tabs.py     # 动态 Tab 加载
│   │   └── marketplace.py      # 插件市场接口
│   │
│   ├── tab_utils.py            # Tab 公共工具 (消除重复)
│   ├── auth.py                 # 认证逻辑
│   ├── auth_dialog.py          # 登录对话框
│   ├── dynamic_modules.py      # 动态模块注册表
│   ├── loaders.py              # 模块缓存加载器 (线程安全)
│   ├── tool_tabs.py            # 工具 Tab 接入
│   ├── utils.py                # 共享工具函数
│   ├── widgets.py              # 通用 UI 组件
│   └── window.py               # 主窗口
│
├── config/                     # 配置系统
│   ├── app.py                  # AppConfig
│   ├── user.py                 # UserConfig
│   ├── plugin.py               # PluginConfig
│   ├── manager.py              # ConfigManager (迁移/版本控制)
│   └── compat.py               # IniSettings 兼容层
│
├── logs/                       # 日志系统
│   ├── manager.py              # LogManager
│   ├── handlers.py             # 5 种 Handler
│   ├── formatters.py           # 6 种 Formatter
│   └── error_report.py         # 用户错误报告
│
├── resources/                  # 资源管理
│   ├── manager.py              # ResourceManager
│   ├── path_utils.py           # 路径工具
│   ├── temp_manager.py         # 临时文件管理
│   ├── cache.py                # 缓存管理 (脏标记优化)
│   ├── validators.py           # 资源验证器
│   └── resource_compat.py      # 资源兼容层
│
├── themes/                     # 主题样式
├── music/                      # NCM 转 MP3
├── zipandpng/                  # 文件伪装
├── mp4-mp3/                    # MP4 转 MP3
├── image-convert/              # 图片格式互转
├── pdf-tools/                  # PDF 工具
├── video-downloader/           # 网页视频下载
├── name/                       # 批量文件命名
├── 分类/                        # 文件自动分类
├── same/                       # 重复文件查找
├── base64/                     # Base64 编解码
│
├── docs/                       # 文档
│   ├── autoplan.md             # 工程升级计划 (135/135 ✅)
│   ├── architecture_report.md  # 架构报告
│   ├── migration_summary.md    # 迁移摘要
│   ├── future_roadmap.md       # 未来路线图
│   ├── performance_analysis.md # 性能分析
│   ├── plugin_api.md           # 插件 API 文档
│   ├── plugin_migration_plan.md # 插件迁移计划
│   ├── package_optimization.md # 包优化建议
│   └── developer_guide.md      # 开发者指南
│
├── .github/workflows/test.yml  # GitHub Actions CI
├── pyproject.toml              # pytest 配置
├── HylToolbox.spec             # PyInstaller 打包配置
└── tests_*.py                  # 集成测试 (189 个)
```

## 架构设计

### 分层架构

```
┌─────────────────────────────────────────┐
│  Tab 文件 (UI 层)                        │
│  mp4-mp3/tab.py, base64/tab.py, ...     │
├─────────────────────────────────────────┤
│  Services (服务层)                        │
│  MP4Service, Base64Service, ...          │
├─────────────────────────────────────────┤
│  Core (基础设施层)                        │
│  logger, config, events, performance     │
├─────────────────────────────────────────┤
│  Task Framework (任务框架)                │
│  Task, TaskWorker, TaskQueue, TaskManager│
└─────────────────────────────────────────┘
```

### Builder / Deps 注入模式

每个工具模块采用 **builder 函数 + deps 字典** 的依赖注入模式：

```python
# tab.py — 每个工具的 GUI 页签
def build_xxx_tab_class(deps: dict):
    QWidget = deps['QWidget']
    # ... 从 deps 获取所有 Qt 类和工具函数

    class XxxTab(BaseToolTab):
        def __init__(self, settings):
            # 构建 UI
            ...

    return XxxTab
```

**好处：** 工具模块不直接 import PySide6，通过 deps 注入，方便测试和解耦。

### 服务层

业务逻辑从 UI 回调中解耦到 `services/`：

```python
# tab.py — 调用 service 而非直接调用 converter
from toolbox_app.services.mp4_service import MP4Service

service = MP4Service()
result = service.convert(input_path, output_path)
```

### 模块加载

`toolbox_app/loaders.py` 提供 `load_module_once(name, path)`：
- 首次加载时通过 `importlib` 动态导入
- 加载成功后缓存，后续调用直接返回
- 线程安全（`RLock` 保护）

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
| `BaseToolTab` | 工具页签基类，提供输出目录行、日志、进度条、文件去重、错误处理 |
| `DropZoneCard` | 拖拽区域卡片，支持文件/文件夹拖入 |
| `DragTitleBar` | 自定义无边框窗口标题栏 |
| `ThemedMessageDialog` | 主题一致的消息弹窗 |
| `show_themed_success/error/warning` | 统一弹窗入口 |

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
# 全量测试 (189 个)
python -m pytest --tb=short -q

# 单模块测试
python -m pytest tests_toolbox.py -q       # 应用主流程
python -m pytest tests_core.py -q          # 核心模块 + 边界
python -m pytest tests_tab_utils.py -q     # Tab 工具函数
python -m pytest tests_services.py -q      # 服务层
python -m pytest tests_performance.py -q   # 性能监控
```

## 子模块独立 CLI

```bash
# 文件伪装
python zipandpng/zipandpng.py disguise cover.png payload.exe out.png
python zipandpng/zipandpng.py recover out.png recovered.exe
python zipandpng/zipandpng.py info out.png
```

## 工程升级记录

详见 `docs/autoplan.md`（135/135 项全部完成）。

关键升级：
- **Phase 2**: 核心基础设施层 (core/)
- **Phase 3**: 统一任务框架 (task_framework/)
- **Phase 4**: 服务层解耦 (services/)
- **Phase 5**: 插件架构 (plugins/)
- **Phase 6**: 配置系统 (config/)
- **Phase 7**: 日志系统 (logs/)
- **Phase 8**: 资源管理 (resources/)
- **Phase 9**: 测试覆盖 (189 个测试)
- **Phase 10**: 性能优化 (CacheManager 脏标记、logger 延迟导入)
- **Phase 11**: GPU 加速、插件市场、崩溃恢复、开发者文档
