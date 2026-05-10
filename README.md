# hyl tools

一个面向 Windows 本地文件处理的 Python 桌面工具箱，当前主入口是 `hyl_toolbox.py`。项目把多个常用的小工具整合进同一个 PySide6 GUI，方便直接拖拽文件、选择输出目录并批量处理。

## 当前能力

- **网易云 NCM 转 MP3**：批量把 `.ncm` 转成 `.mp3`，并在页面里显示已添加歌曲的封面与歌名
- **MP4 转 MP3**：从视频中提取音频
- **Zip+PNG / 单文件伪装**：把任意单文件附加到图片末尾，并支持恢复
- **图片格式互转**：批量处理 JPG / PNG / WebP / HEIC
- **PDF 工具**：支持合并、拆分、转图片、提取文字、导出 TXT / DOCX
- **图片 Base64**：支持图片转 Base64 / Data URL，以及 Base64 还原图片
- 统一 GUI 工具箱：通过一个桌面界面集中使用以上能力
- 统一主题弹层：完成/提示/失败消息采用无边框主题自适应弹窗
- **Windows 打包分发**：可用 PyInstaller 打包为 `格式转换工具.exe`

## 目录结构

```text
hyl tools/
├─ hyl_toolbox.py
├─ HylToolbox.spec
├─ hyl_toolbox.ini
├─ README.md
├─ tests_toolbox.py
├─ tests_tool_pages.py
├─ image-convert/
│  ├─ converter.py
│  ├─ README.md
│  └─ tests_image_convert.py
├─ pdf-tools/
│  ├─ converter.py
│  ├─ README.md
│  └─ tests_pdf_tools.py
├─ music/
├─ mp4-mp3/
├─ zipandpng/
├─ build/
├─ dist/
└─ 测试/
```

## 各子模块说明

### 1. `hyl_toolbox.py`
统一 GUI 入口，负责：
- 页面切换与交互逻辑
- 调用各子模块能力
- 读取/保存工具箱配置
- 兼容源码运行与 PyInstaller 打包运行
- 提供无边框窗口、自定义圆点控制按钮与 30px 顶部拖拽区
- 提供页面切换、拖拽高亮、主题切换的轻量过渡动画

### 2. `music/`
负责网易云 `.ncm` 到 `.mp3` 的转换，支持单文件、目录递归、批量转换与输出目录指定。

### 3. `mp4-mp3/`
负责从 `.mp4` 中提取音频并输出 `.mp3`，依赖系统中的 `ffmpeg`。

### 4. `zipandpng/`
负责单文件伪装进图片与恢复，支持 `disguise / recover / info` 等命令。

### 5. `image-convert/`
负责图片格式互转，当前支持：
- 输入：JPG / JPEG / PNG / WebP / HEIC
- 输出：JPG / PNG / WebP / HEIC
- 质量参数控制
- 目标体积压缩
- 图片尺寸自动缩放兜底
- ImageMagick 依赖检测

### 6. `pdf-tools/`
PDF 子模块当前已支持：
- PDF 文件递归收集
- 页码范围解析
- 输出命名规则生成
- Tesseract 依赖检测
- `pypdf` 合并 / 拆分
- `PyMuPDF` 转图片
- 文本层提取
- OCR 兜底策略
- 导出 `.txt` / `.docx`
- GUI 页面接入与参数校验

## 运行方式

### 直接运行源码

```bash
python hyl_toolbox.py
```

如果本机缺少 GUI 依赖，需先安装 `PySide6`。

### Windows 一键启动（BAT）

项目根目录提供：`启动工具箱.bat`

双击后会优先使用项目内虚拟环境：

```bat
.\\.venv\\Scripts\\python.exe .\\hyl_toolbox.py
```

如果提示缺少 `PySide6`，先安装到该虚拟环境：

```bash
.\\.venv\\Scripts\\python.exe -m pip install PySide6
```

如果启动失败，脚本会停留在窗口里，方便查看报错信息。

### 窗口交互说明

- 顶部提供 **30px 高度拖拽区**，颜色与当前背景保持一致，不做明显撞色分区
- 左侧导航栏在浅色模式下与窗口背景统一，不额外使用突兀卡片底色
- 右上角使用自定义圆点窗口按钮：最小化 / 最大化（还原）/ 关闭
- 双击顶部拖拽区可在最大化与还原之间切换
- 左侧工具页切换会进行淡入过渡，拖拽文件进入卡片会有轻微脉冲反馈，主题切换会柔和刷新主内容区

### 本地登录/注册

- 程序启动时会先显示本地登录窗口
- 程序会自动初始化默认账号：`admin`
- 默认密码：`123`
- 如果当前目录下还没有 `users.json`，会自动写入默认管理员账号
- 注册后的账号信息会保存在项目根目录的 `users.json`
- 可注册多个本地账号，之后只能使用已注册的账号密码登录
- 密码不会明文保存，而是以带随机盐的 SHA-256 哈希形式写入本地文件
- 新注册账号和修改密码都必须满足以下规则（默认管理员 `admin / 123` 为特例，可直接使用）：
  - 长度必须严格等于 12 位
  - 必须包含大写字母、小写字母、数字、特殊符号各至少 2 个
  - 不能包含连续 3 位相同字符
  - 不能包含连续 3 位顺序字符（如 123 / abc / ABC）
  - 不能包含 2024、2025、2026、admin、root、password 任何片段
  - 首字符必须是大写字母
  - 尾字符必须是数字
  - 特殊符号只能从 `!@#$%^&*()_+-=` 中选择
- 登录窗口支持“记住密码”和“自动登录”勾选项
- 自动登录会强制依赖记住密码：勾选自动登录时会自动勾选记住密码；取消记住密码时会自动取消自动登录
- `hyl_toolbox.ini` 会保存上次登录用户名、记住密码状态、自动登录状态，以及用于本地回填的可逆编码密码串
- 登录窗口支持“修改密码”模式，需要输入当前密码并设置新密码
- 登录/注册弹窗为无边框样式，右上角提供与主界面同风格的关闭按钮

示例存储文件：

```json
[
  {
    "username": "admin",
    "password_hash": "<salt>$<sha256>"
  }
]
```


```bash
python -m pytest -q
```

也可以只跑某个子模块，例如：

```bash
python -m pytest pdf-tools/tests_pdf_tools.py -q
python -m pytest image-convert/tests_image_convert.py -q
python -m pytest tests_toolbox.py tests_tool_pages.py -q
```

## 打包

项目包含 `HylToolbox.spec`，可直接使用 PyInstaller：

```bash
pyinstaller HylToolbox.spec
```

## 打包说明

如果你使用 PyInstaller 打包，请确保 `dist/` 目录里和 `格式转换工具.exe` 一起携带：
- `hyl_toolbox.ini`
- `users.json`

否则自动登录、记住密码等本地状态不会延续。

## 自动登录说明

源码方式启动（例如 `./.venv/Scripts/python.exe ./hyl_toolbox.py`）时，登录框会在构造阶段尝试自动登录。
如果此时已经完成 `accept()`，主流程不应再重复调用一次 `exec()`；否则会出现“看起来自动登录没生效”或启动衔接异常。

## 依赖说明

按当前模块情况，主要依赖包括：
- `PySide6`：桌面 GUI
- `ffmpeg`：MP4 转 MP3
- `ncmdump`：NCM 转 MP3
- `ImageMagick`（`magick`）：图片格式互转
- `pypdf`：PDF 合并/拆分
- `PyMuPDF`：PDF 转图片 / 文本提取
- `python-docx`：PDF 导出 Word
- `Tesseract`：PDF OCR 提取文字

## 当前状态

这个项目已经不是零散脚本集合，而是一个正在持续整理的本地工具箱工程：
- 有统一 GUI
- 有独立子模块
- 有测试
- 有打包配置
- 有 Windows 可执行产物
- PDF 工具链已接入核心能力

## 一句话总结

`hyl tools` 是一个以 **PySide6 桌面 GUI** 为入口、面向 **Windows 本地文件转换与处理** 的小工具箱，目前已集成音频、图片、伪装文件、PDF 处理等能力。
