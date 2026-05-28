# Zip+PNG / 单文件伪装工具

命令行工具：把一张合法图片作为封面，把任意单个文件伪装进这个图片里，输出一个仍可正常预览的封面文件，并支持恢复原始文件。

当前支持的封面格式：
- PNG
- JPG / JPEG
- GIF
- WEBP

主命令：

```bash
python zipandpng.py disguise cover.png payload.exe out.png
python zipandpng.py disguise cover.jpg payload.exe out.jpg
python zipandpng.py disguise cover.gif payload.exe out.gif
python zipandpng.py disguise cover.webp payload.exe out.webp
python zipandpng.py disguise cover.jpg payload.exe
python zipandpng.py info out.jpg
python zipandpng.py recover out.gif recovered.exe
```

兼容旧别名：

```bash
python zipandpng.py merge cover.png payload.exe out.png
python zipandpng.py extract out.png recovered.exe
```

说明：
- disguise：输出文件格式为“原始图片字节 + 自定义附加标记 + 原文件名元数据 + 原文件内容”。
- info：查看是否存在附加文件，以及封面格式、原文件名和大小。
- recover：从伪装后的图片中恢复原始单文件；若不提供输出路径，则默认使用内嵌记录的原文件名。
- output 现在可省略；省略时会自动生成 `封面名_disguised.原扩展名`，例如 `cover.jpg -> cover_disguised.jpg`。
- 输出文件扩展名建议保持和封面一致，例如 JPG 封面输出 `.jpg`，GIF 封面输出 `.gif`，WEBP 封面输出 `.webp`。
- 大多数图片查看器可正常显示封面，但部分平台在转发/压缩图片时可能清掉尾部附加数据。
