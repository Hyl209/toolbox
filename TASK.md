# Task: 自定义主题颜色功能

## 需求概述
为 hyl tools 添加"自定义主题调色板"功能，用户可以自由搭配颜色，每个色彩分区都可以独立设置，通过调色板选取颜色后实时预览并持久化。

## 当前架构分析
- 主题系统：`themes/dark.qss` 和 `themes/light.qss`，硬编码颜色值
- `hyl_toolbox.py` 中 `_load_theme_css()` 读取 QSS 文件
- `toolbox_app/window.py` 中 `toggle_theme()` 切换主题，调用 `setStyleSheet()`
- 每个 tab 有 `apply_theme()` 方法
- 设置对话框在 `toolbox_app/settings_dialog.py`，有 account/plugins/order 三个导航项
- 持久化用 `IniSettings`（`hyl_toolbox.ini`）

## 设计方案

### 1. 色彩分区定义（7个分区）

| 分区 ID | 名称 | 影响范围 | dark 默认值 | light 默认值 |
|---------|------|---------|------------|-------------|
| `window_bg` | 窗口背景 | QMainWindow, windowSurface | `#1b1f25` | `#e5e9ef` |
| `surface_bg` | 面板背景 | QWidget, navPanel, contentSurface | `#1f2329` | `#eef1f5` |
| `card_bg` | 卡片背景 | QFrame[card], QFrame[dropzone] | `rgba(44,50,59,0.88)` | `rgba(245,247,252,0.92)` |
| `accent` | 强调色 | QPushButton, 选中项, 进度条, focus 边框 | `#6f95c7` | `#5b8dd9` |
| `text_primary` | 主文字 | QLabel, QWidget color | `#eef2f7` | `#1f252d` |
| `text_secondary` | 次文字 | cardSub, brandSub, nav 未选中 | `#9aa6b5` | `#697586` |
| `input_bg` | 输入框背景 | QLineEdit, QPlainTextEdit, QComboBox | `#2a3038` | `#eef1f5` |

### 2. 实现架构

#### 2.1 新建模块 `modules/theme-customizer/`
按 AGENTS.md 约定，新功能独立子目录。

- `color_scheme.py` — 核心逻辑：
  - `COLOR_ZONES` 定义：7个分区的 id、名称、描述、dark/light 默认值
  - `generate_qss(base_qss: str, overrides: dict[str, str], theme: str) -> str` — 用正则替换 QSS 中对应颜色
  - `get_default_colors(theme: str) -> dict` — 获取某主题的默认颜色
  - `load_custom_colors(settings, theme: str) -> dict` — 从 ini 读取自定义颜色
  - `save_custom_colors(settings, theme: str, colors: dict)` — 写入 ini

- `tab.py` — 设置界面（不单独作为 sidebar tab，而是嵌入 SettingsDialog）

#### 2.2 颜色替换策略
不用模板引擎，而是用**智能正则替换**：
- 读取原始 dark.qss / light.qss 内容
- 对每个分区，识别该分区对应的原始颜色值（从默认主题中提取）
- 把用户自定义颜色替换进去
- 保留 QSS 中的非颜色属性（border-radius、padding 等）

具体来说，`color_scheme.py` 中定义每个分区的"原始颜色映射"：
```python
ZONE_COLOR_MAP = {
    'dark': {
        'window_bg': ['#1b1f25'],
        'surface_bg': ['#1f2329'],
        'card_bg': ['rgba(44, 50, 59, 0.88)', 'rgba(44,50,59,0.88)'],
        'accent': ['#6f95c7', '#7ea6d9', '#6d94c8', '#6488b7', '#7b9fd0'],
        'text_primary': ['#eef2f7', '#eef4fb', '#f3f6fb', '#f4f7fb', '#f5f7fa'],
        'text_secondary': ['#9aa6b5', '#a4b0bf', '#9eabb9', '#aeb8c6', '#aab4c2'],
        'input_bg': ['#2a3038', '#303741'],
    },
    'light': {
        'window_bg': ['#e5e9ef'],
        'surface_bg': ['#eef1f5'],
        'card_bg': ['rgba(245, 247, 252, 0.92)', 'rgba(245,247,252,0.92)'],
        'accent': ['#5b8dd9', '#dfeafc', '#d4e4ff', '#5a9a6b', '#6aad7c'],
        'text_primary': ['#1f252d', '#2b3541', '#2d3748'],
        'text_secondary': ['#697586', '#7d8a9a', '#586474', '#637083'],
        'input_bg': ['#eef1f5', '#f5f7fa'],
    },
}
```

替换逻辑：
1. 用户选择某分区的新颜色（比如 accent 从 `#6f95c7` 改为 `#ff6b6b`）
2. 计算衍生色：hover = lighten 8%, pressed = darken 8%, focus border = alpha 0.5
3. 在 QSS 文本中把该分区所有原始颜色值替换为新颜色 + 衍生色
4. 返回新的 QSS 字符串

#### 2.3 设置界面集成
在 `settings_dialog.py` 的 `_NAV_ITEMS` 中增加一项：
```python
('theme', '🎨  主题配色'),
```

主题配色页面布局：
- 顶部：当前主题指示（深色/浅色）+ "恢复默认" 按钮
- 主体：7 个色彩分区卡片，每行一个：
  - 左侧：分区名称 + 简短描述
  - 右侧：当前颜色预览圆点（可点击）
  - 点击颜色圆点 → 弹出 QColorDialog 选色
  - 选色后实时预览（调用主窗口的 setStyleSheet）
- 底部：导出/导入配色方案按钮（JSON 格式，可选做）

#### 2.4 持久化
在 `hyl_toolbox.ini` 中存储：
```ini
[theme/dark]
window_bg=#1b1f25
surface_bg=#1f2329
accent=#ff6b6b
...

[theme/light]
window_bg=#e5e9ef
...
```

#### 2.5 主窗口集成
修改 `window.py` 的 `toggle_theme()` 和初始化：
- 初始化时读取自定义颜色，生成 QSS 并应用
- toggle_theme 时切换 base theme，然后叠加自定义颜色
- SettingsDialog 关闭后如果有颜色变更，刷新主窗口样式

### 3. 文件变更清单

| 文件 | 操作 | 说明 |
|------|------|------|
| `modules/theme-customizer/__init__.py` | 新建 | 空 |
| `modules/theme-customizer/color_scheme.py` | 新建 | 色彩分区定义 + QSS 生成 + 持久化 |
| `toolbox_app/settings_dialog.py` | 修改 | 增加"主题配色"导航项和对应页面 |
| `toolbox_app/window.py` | 修改 | 初始化和 toggle_theme 使用自定义颜色 |
| `hyl_toolbox.py` | 修改 | 注册 theme-customizer 模块到 deps（如需要） |
| `HylToolbox.spec` | 修改 | 打包清单增加新模块 |

### 4. 关键约束
- **不改旧模块的 QSS 文件本身**，而是在运行时替换
- **衍生色自动计算**：hover、pressed、focus、disabled 等状态色由 accent 自动派生
- **QColorDialog** 是 Qt 内置的，不需要额外依赖
- **实时预览**：选色后立即刷新整个应用样式
- **向后兼容**：没有自定义颜色时，行为与现在完全一致（使用默认 QSS）
- 每个 tab 的 `apply_theme()` 不需要改，因为全局 setStyleSheet 已经覆盖

### 5. 验证步骤
1. 启动程序，打开设置 → 主题配色
2. 修改"强调色"为红色系，确认按钮、选中项、进度条变红
3. 切换到浅色主题，确认浅色主题也有自定义颜色
4. 关闭程序重新打开，确认颜色持久化
5. 点击"恢复默认"，确认回到原始配色
6. 运行 `pytest` 确认无破坏性变更
