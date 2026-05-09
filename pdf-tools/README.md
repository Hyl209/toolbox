# PDF 处理子模块

用于 `hyl tools` 工具箱中的 PDF 合并、拆分、转图片、提取文字、导出 Word 功能。

## 当前能力

- 支持递归收集 PDF 文件
- 支持页码范围解析
- 支持 Tesseract 依赖检测
- 支持 PDF 输出路径生成
- 支持拆分输出命名与转图片输出命名
- 支持文字层优先、OCR 兜底策略判断
- 支持基础操作参数校验
- 支持 `pypdf` 合并 / 拆分 PDF
- 支持 `PyMuPDF` 转图片
- 支持导出 `.txt`
- 支持导出 `.docx`（依赖 `python-docx`）
- 支持 GUI 接入 `merge / split / images / text`

## 依赖

- `pypdf`：合并、拆分
- `PyMuPDF`：转图片、提取文字
- `python-docx`：导出 Word
- `Tesseract`：OCR 兜底

## GUI 功能说明

- `merge`：合并多个 PDF，输出 `merged.pdf`
- `split`：按页码范围拆分单个 PDF
- `images`：将单个 PDF 按页导出为图片
- `text`：将单个 PDF 导出为 `txt` 或 `docx`，可勾选 OCR 兜底

## 测试

```bash
python -m pytest pdf-tools/tests_pdf_tools.py -q
```
