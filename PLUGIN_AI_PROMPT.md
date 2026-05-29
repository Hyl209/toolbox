# HylToolbox 插件开发 AI Prompt

```
HylToolbox 是一个 PyQt 桌面工具箱，支持插件扩展。插件放在 plugins/ 目录下，启动时自动发现加载。

### 1. GUI 插件（带界面，嵌入侧边栏）
创建 plugins/插件名/ 目录，包含：
- manifest.json：声明元数据和入口
- plugin.py：实现插件类

manifest.json 格式：{"name":"唯一标识","version":"1.0.0","description":"描述","author":"作者","entry":"plugin.py:类名","type":"gui"}

plugin.py 的类必须继承 toolbox_app.plugins.base.PluginBase，实现：
- get_plugin_info() → 返回 PluginInfo 对象
- initialize(deps) → 从 deps 字典取 Qt 类构建界面，返回 True
- get_tab_widget() → 返回 QWidget 作为插件界面
- get_sidebar_label() → 返回侧边栏显示的文字
- cleanup() → 清理资源，必须调用 super().cleanup()

注意：Qt 控件（QWidget、QVBoxLayout、QLabel 等）必须从 deps 字典获取，不要直接 import PyQt/PySide。
```
