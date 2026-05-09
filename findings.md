# Findings

- `pdf-tools/converter.py` 已具备 PDF 收集、页码解析、`pypdf` 合并拆分、`PyMuPDF` 转图片。
- `hyl_toolbox.py` 已接入 `PDF工具` 页面，并支持 `merge / split / images / text`。
- `HylToolbox.spec` 已包含 `pdf-tools/converter.py`。
- `pdf-tools` 现已支持 `.txt` / `.docx` 导出，以及文字层为空时 OCR 兜底。
- `zipandpng/__init__.py` 已补出包导出，修复 pytest 下 `import zipandpng` 命名空间不一致问题。
