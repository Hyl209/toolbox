# 多封面格式支持实现计划

> **For Hermes:** Use subagent-driven-development skill to implement this plan task-by-task.

**Goal:** 在现有单文件伪装工具基础上，新增 JPG/JPEG/GIF 封面支持，允许输出文件保留封面原格式扩展名。

**Architecture:** 把当前 `ensure_png` 升级为通用图片签名识别函数，根据文件头识别 PNG/JPEG/GIF，并统一返回图片格式名。伪装与恢复逻辑仍使用“原图字节 + 尾部自定义负载”结构，不改负载协议，只扩展允许的封面类型。

**Tech Stack:** Python 3、argparse、pathlib、struct、pytest

---

### Task 1: 锁定 JPG 封面行为

**Objective:** 先写 RED 测试，证明 JPG 封面当前不被支持。

**Files:**
- Modify: `tests/test_zipandpng.py`
- Modify: `zipandpng.py`

**Step 1: Write failing test**
增加 `test_disguise_recover_roundtrip_with_jpg_cover`：使用极小 JPEG 字节作为封面，执行 `disguise -> info -> recover`，断言输出 `.jpg` 保持可处理，recover 后字节一致。

**Step 2: Run test to verify failure**
Run: `.venv-pytest/bin/python -m pytest tests/test_zipandpng.py::test_disguise_recover_roundtrip_with_jpg_cover -v`
Expected: FAIL — 当前只认 PNG。

**Step 3: Write minimal implementation**
实现 JPEG 文件头识别，并让 disguise/info/recover 共用该校验。

**Step 4: Run test to verify pass**
Run: `.venv-pytest/bin/python -m pytest tests/test_zipandpng.py::test_disguise_recover_roundtrip_with_jpg_cover -v`
Expected: PASS

### Task 2: 锁定 GIF 封面行为

**Objective:** 再写 RED 测试，证明 GIF 封面也可用。

**Files:**
- Modify: `tests/test_zipandpng.py`
- Modify: `zipandpng.py`

**Step 1: Write failing test**
增加 `test_disguise_recover_roundtrip_with_gif_cover`：使用极小 GIF 字节作为封面，执行 `disguise -> info -> recover`，断言 recover 后字节一致。

**Step 2: Run test to verify failure**
Run: `.venv-pytest/bin/python -m pytest tests/test_zipandpng.py::test_disguise_recover_roundtrip_with_gif_cover -v`
Expected: FAIL — 当前还未支持 GIF。

**Step 3: Write minimal implementation**
实现 GIF87a/GIF89a 文件头识别。

**Step 4: Run test to verify pass**
Run: `.venv-pytest/bin/python -m pytest tests/test_zipandpng.py::test_disguise_recover_roundtrip_with_gif_cover -v`
Expected: PASS

### Task 3: 提供结构化格式识别测试

**Objective:** 确保格式识别函数可单独验证，避免后续扩展继续堆 if。

**Files:**
- Modify: `tests/test_zipandpng.py`
- Modify: `zipandpng.py`

**Step 1: Write failing test**
增加 `test_detect_cover_image_format_supports_png_jpg_gif`，直接验证纯函数能识别三种格式，并对非法文件抛出统一错误。

**Step 2: Run test to verify failure**
Run: `.venv-pytest/bin/python -m pytest tests/test_zipandpng.py::test_detect_cover_image_format_supports_png_jpg_gif -v`
Expected: FAIL — 还没有通用检测函数。

**Step 3: Write minimal implementation**
提取 `detect_cover_image_format()` / `ensure_supported_cover_image()` 之类纯函数。

**Step 4: Run test to verify pass**
Run: `.venv-pytest/bin/python -m pytest tests/test_zipandpng.py::test_detect_cover_image_format_supports_png_jpg_gif -v`
Expected: PASS

### Task 4: 更新 README

**Objective:** 让说明文档与实际支持格式一致。

**Files:**
- Modify: `README.md`

**Step 1: Update docs**
把 README 中“PNG 封面”更新为“PNG/JPG/JPEG/GIF 封面”，并说明输出建议保留封面扩展名。

**Step 2: Verify**
Read: `README.md`
Expected: 文案与行为一致。

### Task 5: 全量验证

**Objective:** 确认所有回归与语法检查通过。

**Files:**
- Verify: `zipandpng.py`
- Verify: `tests/test_zipandpng.py`
- Verify: `README.md`

**Step 1: Run full test suite**
Run: `.venv-pytest/bin/python -m pytest tests/test_zipandpng.py -v`
Expected: all passed

**Step 2: Run syntax check**
Run: `python3 -m py_compile zipandpng.py tests/test_zipandpng.py`
Expected: no output
