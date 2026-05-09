# hyl tools

一个面向 Windows 本地文件处理的 Python 桌面工具箱，当前主入口是 `hyl_toolbox.py`。项目把多个常用的小工具整合进同一个 PySide6 GUI，方便直接拖拽文件、选择输出目录并批量处理。

## 当前能力

- **网易云 NCM 转 MP3**：批量把 `.ncm` 转成 `.mp3`
- **MP4 转 MP3**：从视频中提取音频
- **Zip+PNG / 单文件伪装**：把任意单文件附加到图片末尾，并支持恢复
- **图片格式互转**：批量处理 JPG / PNG / WebP / HEIC
- **PDF 工具**：支持合并、拆分、转图片、提取文字、导出 TXT / DOCX
- **统一 GUI 工具箱**：通过一个桌面界面集中使用以上能力
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

### 运行测试

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

打包后产物通常位于：

- `dist/格式转换工具.exe`
- `dist/hyl_toolbox.ini`

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
