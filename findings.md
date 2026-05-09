# Findings

- 已存在三个功能子目录：`music/`、`mp4-mp3/`、`zipandpng/`。
- 根目录 GUI 入口为 `hyl_toolbox.py`，README 已说明它统一调度多个子功能。
- 新功能应按用户要求，新建与现有模块同级的独立文件夹，而不是直接塞进旧模块。
- GUI 结构为：侧边栏 `QListWidget` + `QStackedWidget` 多 Tab 页面，新增功能需要新增一个 Tab 并接入侧边栏。
- 用户确认采用第二种方案，即 ImageMagick 路线。
- 用户要求 JPG 透明底色保持可选。
- 用户额外要求支持输入目标大小数字，尽量压缩到指定体积。
