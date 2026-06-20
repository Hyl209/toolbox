# Base64 文件工具

一个轻量本地模块，负责任意文件与 Base64 文本之间的双向转换。

## 功能
- 任意单文件转 Base64
- 可按文件后缀拼接 Data URL
- Base64 / Data URL 还原为文件
- 保存 Base64 为 `.txt`

## 支持格式
- 输入文件：任意本地文件
- 输出文件：根据 Data URL 推断后缀；裸 Base64 默认 `.bin`

## 测试
```bash
python -m pytest modules/base64/tests_base64_tools.py -q
```
