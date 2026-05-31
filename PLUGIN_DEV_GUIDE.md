# HylToolbox 插件开发指南

## 目录

- [插件类型](#插件类型)
- [目录结构](#目录结构)
- [快速开始：GUI 插件](#快速开始gui-插件)
- [快速开始：Hook 插件](#快速开始hook-插件)
- [PluginBase API 参考](#pluginbase-api-参考)
- [manifest.json 字段说明](#manifestjson-字段说明)
- [依赖注入（deps）](#依赖注入deps)
- [生命周期](#生命周期)
- [插件配置系统](#插件配置系统)
- [设置对话框集成](#设置对话框集成)
- [注意事项与限制](#注意事项与限制)

---

## 插件类型

| 类型 | `plugin_type` | 说明 | 典型用途 |
|------|---------------|------|----------|
| GUI 插件 | `"gui"` | 提供界面 Tab，嵌入主窗口侧边栏 | 工具面板、设置页面 |
| Hook 插件 | `"hook"` | 无界面，通过生命周期钩子和命令注入逻辑 | 日志、自动任务、事件监听 |

---

## 目录结构

### GUI 插件（推荐，多文件）

```
plugins/
  my_plugin/
    manifest.json      # 插件清单（必须）
    plugin.py          # 插件主类（必须）
    ...                # 其他辅助模块
```

### Hook 插件（单文件）

```
plugins/
  my_hook_plugin.py    # 单文件即可，无需 manifest.json
```

> 单文件插件通过源码扫描自动发现，无需 `manifest.json`。

---

## 快速开始：GUI 插件

### 1. 创建 `manifest.json`

```json
{
  "name": "my_plugin",
  "version": "1.0.0",
  "description": "我的插件描述",
  "author": "作者名",
  "entry": "plugin.py:MyPlugin",
  "type": "gui",
  "enabled": true,
  "priority": 0
}
```

### 2. 创建 `plugin.py`

```python
from __future__ import annotations
from toolbox_app.plugins.base import PluginBase, PluginInfo


class MyPlugin(PluginBase):

    def get_plugin_info(self) -> PluginInfo:
        return PluginInfo(
            name="my_plugin",
            version="1.0.0",
            description="我的插件描述",
            author="作者名",
            plugin_type="gui",
        )

    def initialize(self, deps: dict = None) -> bool:
        self._deps = deps or {}
        return True

    def get_sidebar_label(self) -> str:
        return "我的插件"

    def get_tab_widget(self):
        QWidget = self._deps.get('QWidget')
        QVBoxLayout = self._deps.get('QVBoxLayout')
        QLabel = self._deps.get('QLabel')
        if QWidget is None:
            return None

        widget = QWidget()
        layout = QVBoxLayout(widget)
        label = QLabel("Hello from my plugin!")
        layout.addWidget(label)
        return widget

    # cleanup() 现在是可选的，不覆盖则使用默认实现
```

### 3. 放入 `plugins/` 目录，重启应用即可

---

## 快速开始：Hook 插件

创建 `plugins/my_hook.py`：

```python
from __future__ import annotations
from toolbox_app.plugins.base import PluginBase, PluginInfo


class MyHookPlugin(PluginBase):

    def get_plugin_info(self) -> PluginInfo:
        return PluginInfo(
            name="my_hook",
            version="1.0.0",
            description="后台钩子示例",
            author="作者名",
            plugin_type="hook",
        )

    def initialize(self, deps: dict = None) -> bool:
        self._deps = deps or {}
        return True

    def on_app_start(self):
        print("应用已启动！")

    def on_app_close(self):
        print("应用即将关闭")

    def on_theme_change(self, theme: str):
        print(f"主题切换为: {theme}")

    def handle_command(self, command: str, **kwargs):
        if command == "ping":
            return "pong"
        return None

    def cleanup(self):
        super().cleanup()  # 可选覆盖，建议调用 super()
```

---

## PluginBase API 参考

### 必须实现的抽象方法

| 方法 | 签名 | 说明 |
|------|------|------|
| `get_plugin_info()` | `-> PluginInfo` | 返回插件元数据 |
| `initialize()` | `(deps: dict = None) -> bool` | 初始化插件，返回 `True` 表示成功 |
| `cleanup()` | `-> None` | 清理资源（可选覆盖，建议调用 `super().cleanup()`） |

### GUI 插件方法

| 方法 | 签名 | 说明 |
|------|------|------|
| `get_tab_widget()` | `-> Optional[QWidget]` | 返回要嵌入主窗口的 Qt 控件 |
| `get_sidebar_label()` | `-> str` | 侧边栏显示文字，默认返回 `name` |

### 生命周期钩子（可选）

| 方法 | 触发时机 |
|------|----------|
| `on_app_start()` | 所有插件加载并初始化完成后 |
| `on_app_close()` | 应用窗口关闭时 |
| `on_theme_change(theme: str)` | 用户切换主题时 |

### 命令处理

| 方法 | 说明 |
|------|------|
| `handle_command(command: str, **kwargs)` | 外部命令分发入口，返回处理结果 |

### 状态属性

| 属性 | 类型 | 说明 |
|------|------|------|
| `name` | `str` | 插件名称（来自 `PluginInfo`） |
| `version` | `str` | 插件版本 |
| `is_initialized` | `bool` | 是否已初始化 |
| `is_enabled` | `bool` | 是否启用 |

---

## manifest.json 字段说明

| 字段 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `name` | string | 是 | - | 插件唯一标识 |
| `version` | string | 是 | - | 语义化版本号 |
| `description` | string | 是 | - | 插件描述 |
| `author` | string | 是 | - | 作者 |
| `entry` | string | 是 | - | 入口，格式 `"文件名.py:类名"`；类必须继承 `PluginBase` |
| `type` | string | 否 | `"gui"` | `"gui"` 或 `"hook"` |
| `enabled` | bool | 否 | `true` | 是否默认启用 |
| `priority` | int | 否 | `0` | 加载优先级，越大越先加载 |
| `dependencies` | list | 否 | `[]` | 依赖的其他插件 `name` 列表；不能自引用或形成循环 |

---

## 依赖注入（deps）

`initialize(deps)` 接收的 `deps` 字典由主应用注入，包含以下内容：

### Qt 类

| Key | 说明 |
|-----|------|
| `QWidget` | Qt 基础控件 |
| `QVBoxLayout` | 垂直布局 |
| `QHBoxLayout` | 水平布局 |
| `QLabel` | 标签 |
| `QPushButton` | 按钮 |
| `QLineEdit` | 单行输入框 |
| `QTextEdit` | 多行文本框 |
| `QComboBox` | 下拉选择框 |
| `QCheckBox` | 复选框 |
| ... | 其他常用 Qt 类 |

### 工具函数

| Key | 说明 |
|-----|------|
| `make_card` | 创建卡片样式容器 |
| `load_setting` | 读取 QSettings 配置 |
| `save_setting` | 写入 QSettings 配置 |
| `get_theme_stylesheet` | 获取当前主题样式表 |

### 对象

| Key | 说明 |
|-----|------|
| `settings` | QSettings 实例 |
| `plugin_manager` | 插件管理器实例 |

> **注意**：GUI 插件应通过 `deps` 获取 Qt 类，而非直接 `import`，以保持松耦合。

---

## 生命周期

```
应用启动
  │
  ├─ 1. PluginDiscovery.discover_plugins()   # 扫描 plugins/ 目录
  ├─ 2. 按 priority 降序排序
  ├─ 3. 验证依赖关系
  ├─ 4. 逐个实例化插件
  ├─ 5. 调用 plugin.initialize(deps)
  ├─ 6. GUI 插件: get_tab_widget() + get_sidebar_label() → 嵌入侧边栏
  ├─ 7. 调用 plugin.on_app_start()
  │
  │  运行中...
  │  ├─ 主题切换 → plugin.on_theme_change(theme)
  │  └─ 命令调用 → plugin.handle_command(cmd, **kw)
  │
  └─ 应用关闭
       ├─ plugin.on_app_close()
       └─ plugin.cleanup()
```

---

## 插件配置系统

插件可通过 `PluginConfig` 获得独立的持久化配置：

```python
from config.manager import ConfigManager

def initialize(self, deps: dict = None) -> bool:
    config_mgr = ConfigManager()
    self.config = config_mgr.get_plugin_config("my_plugin")
    # config 文件位于 config/plugins/my_plugin/config.json
    return True
```

`PluginConfig` 支持的操作：

| 方法 | 说明 |
|------|------|
| `get(key, default=None)` | 获取值（支持 `a.b.c` 嵌套路径） |
| `set(key, value)` | 设置值 |
| `delete(key)` | 删除键 |
| `has(key)` | 判断键是否存在 |
| `keys()` | 列出所有顶层键 |
| `toggle(key)` | 布尔值取反 |
| `increment(key, amount=1)` | 数值增加 |

---

## 设置对话框集成

插件会自动出现在 **设置 → 功能管理** 页面中，展示：

- 插件名称、版本、描述
- 启用/禁用开关

用户禁用的插件会持久化保存，下次启动自动跳过。若禁用某个插件的依赖项，依赖它的插件会在设置页自动同步为禁用；重新启用依赖方时，可见依赖也会自动勾选，避免下次启动加载失败。

---

## 注意事项与限制

1. **`cleanup()` 可选覆盖**，若覆盖需调用 `super().cleanup()` 以确保状态标记更新
2. **路径安全**：插件文件必须位于 `plugins/` 目录内，框架会校验路径防止目录穿越
3. **模块隔离**：插件模块以 `plugin_{name}` 注册到 `sys.modules`，卸载时自动清理
4. **插件名唯一**：同名插件会注册失败，日志会报错
5. **入口类必须继承 `PluginBase`**：manifest `entry` 指向普通类时会在实例化前拒绝加载
6. **Hook 插件不需要 `manifest.json`**：单文件放到 `plugins/` 目录即可自动发现
7. **优先级**：`priority` 越大越先加载，适合有启动顺序依赖的场景
8. **不要在 `initialize()` 中做耗时操作**：会阻塞应用启动；异步任务放到 `on_app_start()` 中
