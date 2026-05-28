     1|# 格式转换工具 · Hyl Toolbox
     2|
     3|PySide6 桌面格式转换工具箱，支持 11 种工具，暗色/亮色主题切换，自定义无边框窗口。
     4|
     5|## 项目结构
     6|
     7|```
     8|hyl tools/
     9|├── hyl_toolbox.py              # 主入口，依赖注入 + 启动循环
    10|├── conftest.py                 # pytest 全局 fixture (QApplication/offscreen)
    11|├── generate_spec.py            # 从 tool_registry 自动生成 HylToolbox.spec
    12|│
    13|├── toolbox_app/                # 核心框架
    14|│   ├── tool_registry.py        # 工具注册表 (唯一来源)
    15|│   ├── core/                   # 核心基础设施层
    16|│   │   ├── logger.py           # 公共日志 API (get_logger)
    17|│   │   ├── config.py           # [deprecated] 旧版配置 → config.manager
    18|│   │   ├── task_manager.py     # [deprecated] 旧版任务 → task_framework
    19|│   │   ├── paths.py            # 路径管理器
    20|│   │   ├── exceptions.py       # 异常体系
    21|│   │   ├── worker.py           # 后台任务 Worker
    22|│   │   └── ...                 # events, file_utils, performance, updater 等
    23|│   │
    24|│   ├── task_framework/         # 统一任务框架 (权威)
    25|│   │   ├── manager.py          # TaskManager
    26|│   │   └── ...                 # task, worker, queue, signals, qthread_adapter
    27|│   │
    28|│   ├── services/               # 服务层 (懒加载)
    29|│   │   └── ...                 # pdf, image, video, ocr, download, file 等
    30|│   │
    31|│   ├── auth.py                 # 认证入口 (re-export)
    32|│   ├── auth_store.py           # 用户存储 + 密码哈希
    33|│   ├── password_policy.py      # 密码策略
    34|│   ├── auth_preferences.py     # 登录偏好
    35|│   ├── auth_dialog.py          # 登录对话框
    36|│   │
    37|│   ├── widgets/                # 通用 UI 组件 (拆分后)
    38|│   │   ├── cards.py            # make_card, make_transparent_row
    39|│   │   ├── dialogs.py          # ThemedMessageDialog, show_themed_*
    40|│   │   ├── titlebar.py         # DragTitleBar, WindowControlButton
    41|│   │   ├── dropzone.py         # DropZoneCard
    42|│   │   ├── animation.py        # animate_fade, animate_stack_switch, pulse
    43|│   │   ├── base_tab.py         # build_base_tool_tab_class
    44|│   │   └── theme_helpers.py    # style_combo_popup
    45|│   │
    46|│   ├── plugins/                # 插件系统 (manifest-first 发现)
    47|│   ├── window.py               # 主窗口 (消费 tool_registry)
    48|│   └── ...
    49|│
    50|├── config/                     # 配置系统 (v2, 权威)
    51|│   ├── manager.py              # ConfigManager
    52|│   └── ...
    53|│
    54|├── logs/                       # 日志系统 (后端实现)
    55|│   ├── manager.py              # LogManager
    56|│   └── ...
    57|│
    58|├── video-downloader/           # 网页/TG 视频下载 (拆分后)
    59|│   ├── models.py               # 数据类型
    60|│   ├── _shared.py              # 共享工具
    61|│   ├── source_parser.py        # URL 分类/任务解析
    62|│   ├── progress.py             # 进度格式化
    63|│   ├── telegram_backend.py     # Telethon 下载
    64|│   ├── web_backend.py          # yt-dlp/aria2/ffmpeg 下载
    65|│   ├── converter.py            # 薄代理层 (re-export)
    66|│   ├── tab.py                  # Tab 主类
    67|│   ├── tab_constants.py        # Tab 常量/样式
    68|│   ├── tab_formatters.py       # Tab 格式化
    69|│   ├── tab_workers.py          # Worker 工厂
    70|│   ├── tab_panels.py           # UI 面板构建
    71|│   └── tests_video_downloader.py
    72|│
    73|├── same/                       # 重复文件检测 (拆分后)
    74|│   ├── _common.py              # 共享常量/工具
    75|│   ├── exact_duplicate.py      # 精确重复检测
    76|│   ├── video_signature.py      # 视频相似度
    77|│   ├── move_plan.py            # 移动计划
    78|│   ├── converter.py            # 薄代理层
    79|│   └── tests_same_converter.py
    80|│
    81|├── music/                      # NCM 转 MP3
    82|├── zipandpng/                  # 文件伪装
    83|├── mp4-mp3/                    # MP4 转 MP3
    84|├── image-convert/              # 图片格式互转
    85|├── pdf-tools/                  # PDF 工具
    86|├── name/                       # 批量文件命名
    87|├── 分类/                        # 文件自动分类
    88|├── base64/                     # Base64 编解码
    89|│
    90|├── themes/                     # 主题样式 (dark.qss / light.qss)
    91|├── docs/                       # 文档
    92|│   └── superpowers/plans/      # 优化计划
    93|│
    94|├── pyproject.toml              # pytest 配置 (basetemp + warning filter)
    95|├── HylToolbox.spec             # PyInstaller 打包 (自动生成)
    96|├── requirements.txt            # 运行依赖
    97|├── requirements-dev.txt        # 测试依赖
    98|└── tests_*.py                  # 集成测试 (329 个)
    99|```
   100|
   101|## 架构设计
   102|
   103|### 工具注册表
   104|
   105|`toolbox_app/tool_registry.py` 是工具定义的唯一来源：
   106|
   107|```python
   108|from toolbox_app.tool_registry import TOOL_DEFINITIONS, get_packaging_datas
   109|
   110|# 所有工具定义
   111|for tool in TOOL_DEFINITIONS:
   112|    print(tool.id, tool.title, tool.sidebar_label)
   113|
   114|# PyInstaller 打包清单 (自动生成)
   115|datas = get_packaging_datas()
   116|```
   117|
   118|`window.py` 从注册表动态构建侧栏和 Tab，新增工具只需修改注册表。
   119|
   120|### Builder / Deps 注入模式
   121|
   122|每个工具模块采用 **builder 函数 + deps 字典** 的依赖注入模式：
   123|
   124|```python
   125|def build_xxx_tab_class(deps: dict):
   126|    QWidget = deps['QWidget']
   127|    class XxxTab(BaseToolTab):
   128|        def __init__(self, settings):
   129|            ...
   130|    return XxxTab
   131|```
   132|
   133|好处：工具模块不直接 import PySide6，通过 deps 注入，方便测试和解耦。
   134|
   135|### 认证系统
   136|
   137|- `password_policy.py`：密码策略 (6-64 位 + 含字母 + 含数字)
   138|- `auth_store.py`：SHA-256 哈希 + salt 存储
   139|- `auth_preferences.py`：记住密码、自动登录
   140|- 默认账号 `admin`，默认密码 `123`
   141|
   142|> **注意**：现阶段密码模块纯属练手玩一下，安全性不做强要求，后续有需要再加强。
   143|
   144|### 主题系统
   145|
   146|- `themes/dark.qss` + `themes/light.qss` 全局样式
   147|- `window.py` 的 `toggle_theme()` 遍历所有 tab 调用 `apply_theme()`
   148|- 每个 tab 通过 `apply_theme()` 协议管理自己的样式
   149|
   150|### 网页下载加速
   151|
   152|`video-downloader/web_backend.py` 优化参数：
   153|- aria2c: 16 连接、HTTP 管线化、异步 DNS、64MB 磁盘缓存
   154|- yt-dlp: 16 并发分片、10MB 块大小、500KB 节流检测
   155|- 自动模式: 速度→并发映射 (10Mbps→8, 5Mbps→6, 2Mbps→4)
   156|
   157|## 运行
   158|
   159|```bash
   160|# 安装依赖
   161|pip install -r requirements.txt
   162|
   163|# 安装测试依赖
   164|pip install -r requirements-dev.txt
   165|
   166|# 启动
   167|python hyl_toolbox.py
   168|
   169|# 打包 (从注册表自动生成 spec)
   170|python generate_spec.py
   171|pyinstaller HylToolbox.spec
   172|```
   173|
   174|## 测试
   175|
   176|```bash
   177|# 全量测试 (329 个)
   178|python -m pytest --tb=short -q
   179|
   180|# 单模块测试
   181|python -m pytest tests_toolbox.py -q       # 应用主流程
   182|python -m pytest tests_core.py -q          # 核心模块
   183|python -m pytest tests_tool_registry.py -q # 注册表 + spec 一致性
   184|python -m pytest tests_services.py -q      # 服务层
   185|python -m pytest video-downloader/tests_video_downloader.py -q  # 下载模块
   186|```
   187|
   188|## 工程优化记录
   189|
   190|详见 `docs/superpowers/plans/code_review_optimization_direction.md`。
   191|
   192|关键优化：
   193|- **工具注册表**: `tool_registry.py` 作为唯一来源，window/spec 测试统一消费
   194|- **模块拆分**: video-downloader 2147行→11 子模块, widgets 615行→7 子模块, same 605行→5 子模块
   195|- **认证安全**: 移除 admin/123 密码豁免, 拆为 auth_store/password_policy/auth_preferences
   196|- **插件安全**: manifest-first 发现, 不执行插件代码
   197|- **测试稳定**: 329 项全绿, QApplication fixture, offscreen 渲染, 缺依赖显式 skip
   198|- **下载加速**: aria2c/yt-dlp 参数调优, 自动并发映射
   199|- **spec 自动生成**: `generate_spec.py` 从注册表生成, 不再手写
   200|