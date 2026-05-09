# PDF 工具接入计划

## 目标
为 `hyl tools` 的 `pdf-tools/` 继续补齐剩余 PDF 能力：在已完成 `pypdf` 合并/拆分、`PyMuPDF` 转图片、GUI 页面与 spec 接入基础上，继续完善 `PDF -> TXT / DOCX`、依赖探测、表单校验与 README。

## 阶段
- [x] Phase 1：确认当前 PDF 核心模块现状
- [x] Phase 2：为 PyMuPDF / GUI / 打包补 RED 测试
- [x] Phase 3：实现 PDF 后端与 GUI 接入
- [x] Phase 4：更新 spec、跑验证并整理文档
- [ ] Phase 5：为 TXT / DOCX / OCR 兜底补 RED 测试
- [ ] Phase 6：实现文本导出与 GUI 扩展
- [ ] Phase 7：回归验证并更新 README

## 已确认现状
- `merge_pdfs()` / `split_pdf()` 已真实实现。
- `pdf_to_images()` 已接入 `PyMuPDF`。
- `hyl_toolbox.py` 已接入 PDF 页面。
- `HylToolbox.spec` 已包含 `pdf-tools/converter.py`。

## 关键问题
- 当前 GUI 仍只覆盖 merge / split / images，未覆盖 txt / docx。
- 需要把“文字层优先，OCR 兜底”真正落到导出路径中。
- WSL 侧继续以纯逻辑/模块测试为主，避免虚报 GUI 真机效果。

## 错误记录
- 暂无
