# hyl tools

一个面向本地文件处理的 Python 小工具集合，当前主入口是桌面端 GUI 程序 `hyl_toolbox.py`，用于把多个常用小工具集中到一个界面里，方便直接拖拽、选择输出目录并批量处理文件。

## 项目用途

这个项目主要用于把几类常见的本地文件处理需求整合成一个工具箱：

- **网易云 NCM 转 MP3**：把 `.ncm` 音乐文件转换为 `.mp3`
- **MP4 转 MP3**：提取视频音频，输出 mp3 文件
- **Zip+PNG / 单文件伪装**：把任意单文件附加到图片末尾，并支持恢复原文件
- **图片格式互转**：批量处理 JPG / PNG / WebP / HEIC 图片格式
- **统一 GUI 工具箱**：通过一个 PySide6 桌面界面统一调用以上能力
- **Windows 打包分发**：使用 PyInstaller 打包为 `格式转换工具.exe`

## 当前结构

```text
hyl tools/
├─ hyl_toolbox.py                # 工具箱主程序，PySide6 GUI 入口
├─ HylToolbox.spec               # PyInstaller 打包配置
├─ hyl_toolbox.ini               # 工具箱配置（输出目录、主题等）
├─ tests_tool_pages.py           # 工具箱页面/表单相关测试
├─ tests_toolbox.py              # 工具箱主逻辑测试
├─ check_ncmdump.py              # 检查 ncmdump 模块是否可用
├─ logo.png                      # GUI 图标资源
├─ logo.ico                      # Windows 可执行文件图标
├─ make_ico.py                   # 生成/处理 ico 的辅助脚本
├─ check_logo.py                 # 图标检查脚本
├─ build/                        # PyInstaller 构建中间产物
├─ dist/                         # 打包输出目录（含 exe）
├─ 测试/                         # 样例输入/输出文件
├─ music/
│  ├─ ncm_to_mp3.py              # NCM 转 MP3 核心脚本
│  ├─ tests_ncm_to_mp3.py        # NCM 转换测试
│  ├─ tests_ncm_gui.py           # 音乐页面 GUI 测试
│  ├─ gui_design.md              # 音乐页面设计文档
│  ├─ task_plan.md               # 音乐模块任务计划
│  ├─ progress.md                # 音乐模块开发进度
│  └─ findings.md                # 音乐模块调研/结论
├─ mp4-mp3/
│  ├─ app.py                     # mp4 转 mp3 命令行入口
│  ├─ converter.py               # ffmpeg 转换逻辑
│  ├─ config_store.py            # 默认输出目录配置读写
│  ├─ README.md                  # mp4-mp3 子模块说明
│  ├─ mp4mp3_config.json         # 子模块配置文件
│  ├─ task_plan.md               # 子模块任务计划
│  ├─ progress.md                # 子模块开发进度
│  └─ findings.md                # 子模块调研/结论
└─ zipandpng/
   ├─ zipandpng.py               # 单文件伪装/恢复核心脚本
   ├─ README.md                  # zipandpng 子模块说明
   ├─ tests/test_zipandpng.py    # zipandpng 测试
   ├─ docs/plans/                # zipandpng 相关实现计划
   ├─ task_plan.md               # 子模块任务计划
   ├─ progress.md                # 子模块开发进度
   └─ findings.md                # 子模块调研/结论
```

## 各模块说明

### 1. `hyl_toolbox.py`

项目主入口，也是当前最核心的整合层。

作用：
- 提供统一的桌面 GUI
- 管理页面切换与交互逻辑
- 调用 `music/`、`mp4-mp3/`、`zipandpng/` 下的功能模块
- 读取/保存工具箱配置
- 兼容源码运行与 PyInstaller 打包运行

从 `HylToolbox.spec` 可以看到，打包时会把这些核心文件一起带入：
- `music/ncm_to_mp3.py`
- `mp4-mp3/converter.py`
- `mp4-mp3/config_store.py`
- `zipandpng/zipandpng.py`
- `logo.png`

最终输出的程序名是：`格式转换工具.exe`

### 2. `music/`

负责网易云 `.ncm` 文件转 `.mp3`。

已确认的用途：
- 支持输入单个 `.ncm` 文件
- 支持输入目录并递归查找 `.ncm`
- 支持批量转换
- 支持指定输出目录
- 依赖 `ncmdump` 作为转换后端

核心文件：
- `ncm_to_mp3.py`：转换实现与命令行入口
- `tests_ncm_to_mp3.py`：基础行为测试
- `tests_ncm_gui.py`：GUI 相关测试

### 3. `mp4-mp3/`

负责把 `.mp4` 视频中的音频提取为 `.mp3`。

已确认的用途：
- 支持直接传入 mp4 文件进行转换
- 支持指定输出文件路径或输出目录
- 支持记忆默认输出目录
- 供独立命令行使用，也能被 GUI 复用
- 依赖系统中的 `ffmpeg`

核心文件：
- `app.py`：命令行入口
- `converter.py`：实际调用 `ffmpeg` 完成转换
- `config_store.py`：默认输出目录读写

### 4. `zipandpng/`

负责把任意单文件伪装进图片中，并支持恢复。

已确认的用途：
- 支持 `PNG / JPG / JPEG / GIF / WEBP` 作为封面
- 支持 `disguise / recover / info` 命令
- 支持兼容旧命令别名 `merge / extract`
- 输出文件在大多数看图场景下仍能正常显示封面

核心文件：
- `zipandpng.py`：伪装、信息查看、恢复的完整逻辑
- `tests/test_zipandpng.py`：功能测试
- `README.md`：子模块说明文档

## 配置与产物

### `hyl_toolbox.ini`

当前配置文件用于保存：
- 音乐转换输出目录
- zipandpng 输出目录
- mp4 转 mp3 输出目录
- UI 主题（当前看到是 `light`）

### `build/` 与 `dist/`

- `build/`：PyInstaller 构建过程中的中间文件
- `dist/`：最终打包结果目录

当前已经存在：
- `dist/格式转换工具.exe`
- `dist/hyl_toolbox.ini`

说明这个项目不只是源码，还已经有可分发的 Windows 可执行版本。

## 测试相关

从项目里能看到几类测试：

- `tests_tool_pages.py`：验证 GUI 页面相关逻辑
- `tests_toolbox.py`：验证工具箱主逻辑
- `music/tests_ncm_to_mp3.py`：验证 NCM 转换核心逻辑
- `zipandpng/tests/test_zipandpng.py`：验证伪装与恢复逻辑

也就是说，这个项目不是单纯的脚本堆叠，而是已经开始往“可维护的小型工具箱项目”方向整理了。

## 适合怎样使用

比较适合下面这些场景：

- 想把多个零散文件处理脚本整合到一个桌面工具里
- 主要在 Windows 环境下使用本地文件转换工具
- 希望保留命令行脚本，同时再提供 GUI 给非技术用户使用
- 希望最终可以直接打包成 exe 分发

## 运行与维护建议

如果后面继续维护这个项目，建议重点关注这几层：

1. **GUI 整合层**：`hyl_toolbox.py`
2. **功能模块层**：`music/`、`mp4-mp3/`、`zipandpng/`
3. **配置层**：`hyl_toolbox.ini`、`mp4mp3_config.json`
4. **打包层**：`HylToolbox.spec`、`build/`、`dist/`
5. **验证层**：现有测试文件

## 一句话总结

`hyl tools` 是一个以 **PySide6 桌面 GUI 为入口**、集成了 **NCM 转 MP3、MP4 转 MP3、图片伪装/恢复** 三类本地文件处理能力的 Windows 小工具箱项目，并且已经具备 **测试文件、配置文件、打包配置和 exe 产物**。
