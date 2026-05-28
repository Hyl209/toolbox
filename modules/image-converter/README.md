# image-convert

图片格式互转子模块，面向 `hyl tools` 工具箱使用。

## 当前能力

- 支持输入：JPG / JPEG / PNG / WebP / HEIC
- 支持输出：JPG / PNG / WebP / HEIC
- 支持批量收集图片文件或目录
- 支持质量参数
- 支持目标体积压缩
- 当只靠质量压不下去时，自动继续缩小分辨率
- 支持 ImageMagick 依赖检测
- 支持 GUI 工具箱调用

## 当前压缩策略

- 优先降低质量
- 若仍大于目标大小，则继续按比例缩小尺寸
- 目标是“尽量压到不超过目标大小”

## 依赖

需要系统中可用 `magick` 命令（ImageMagick）。
