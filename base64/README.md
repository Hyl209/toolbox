# Base64 图片工具

一个轻量本地模块，负责图片与 Base64 文本之间的双向转换。

## 功能
- 图片文件转 Base64
- 可拼接 Data URL
- Base64 / Data URL 还原为图片文件
- 保存 Base64 为 `.txt`

## 支持格式
- 输入图片：PNG / JPG / JPEG / WebP / GIF / BMP
- 输出图片：根据 Data URL 推断，默认 `.png`

## 测试
```bash
python -m pytest /mnt/e/hyl\ tools/base64/tests_base64_tools.py -q
```
