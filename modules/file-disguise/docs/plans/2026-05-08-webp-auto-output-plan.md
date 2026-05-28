# WEBP 与自动输出名实现计划

> **For Hermes:** Use subagent-driven-development skill to implement this plan task-by-task.

**Goal:** 在现有图片封面伪装工具基础上，新增 WEBP 封面支持，并让 disguise 命令在省略 output 时自动生成与封面同扩展名的输出文件名。

**Architecture:** 扩展图片头识别逻辑，增加 WEBP(RIFF....WEBP) 签名判断；再提取一个纯函数统一生成默认输出路径，命名为 `<封面文件名>_disguised<原扩展名>`。CLI 中把 disguise 的 output 参数改为可选，未提供时自动调用该命名函数。

**Tech Stack:** Python 3、argparse、pathlib、struct、pytest

---

### Task 1: 锁定 WEBP 封面支持

**Objective:** 先写 RED 测试，证明 WEBP 封面当前不可用。

**Files:**
- Modify: `tests/test_zipandpng.py`
- Modify: `zipandpng.py`

**Step 1: Write failing test**
增加 `test_disguise_recover_roundtrip_with_webp_cover`：使用最小 WEBP 字节作为封面，执行 `disguise -> recover`，断言恢复字节一致。

**Step 2: Run test to verify failure**
Run: `.venv-pytest/bin/python -m pytest tests/test_zipandpng.py::test_disguise_recover_roundtrip_with_webp_cover -v`
Expected: FAIL — 当前不识别 WEBP。

**Step 3: Write minimal implementation**
给 `detect_cover_image_format()` 增加 WEBP 识别。

**Step 4: Run test to verify pass**
Run: `.venv-pytest/bin/python -m pytest tests/test_zipandpng.py::test_disguise_recover_roundtrip_with_webp_cover -v`
Expected: PASS

### Task 2: 锁定自动输出名行为

**Objective:** 让 disguise 在不传 output 时自动生成输出路径。

**Files:**
- Modify: `tests/test_zipandpng.py`
- Modify: `zipandpng.py`

**Step 1: Write failing test**
增加 `test_disguise_uses_auto_output_name_when_output_is_omitted`：输入 `cover.jpg` 与一个 payload，不传 output，断言默认生成 `cover_disguised.jpg`，且文件存在。

**Step 2: Run test to verify failure**
Run: `.venv-pytest/bin/python -m pytest tests/test_zipandpng.py::test_disguise_uses_auto_output_name_when_output_is_omitted -v`
Expected: FAIL — 当前 output 是必填参数。

**Step 3: Write minimal implementation**
将 disguise 子命令 output 改为可选，并提取默认命名纯函数。

**Step 4: Run test to verify pass**
Run: `.venv-pytest/bin/python -m pytest tests/test_zipandpng.py::test_disguise_uses_auto_output_name_when_output_is_omitted -v`
Expected: PASS

### Task 3: 结构化命名函数测试

**Objective:** 确保默认输出名规则清晰稳定。

**Files:**
- Modify: `tests/test_zipandpng.py`
- Modify: `zipandpng.py`

**Step 1: Write failing test**
增加 `test_build_default_disguised_output_path_keeps_cover_suffix`，分别验证 png/jpg/gif/webp 都会生成 `*_disguised.<ext>`。

**Step 2: Run test to verify failure**
Run: `.venv-pytest/bin/python -m pytest tests/test_zipandpng.py::test_build_default_disguised_output_path_keeps_cover_suffix -v`
Expected: FAIL — 还没有该纯函数。

**Step 3: Write minimal implementation**
实现 `build_default_disguised_output_path()`。

**Step 4: Run test to verify pass**
Run: `.venv-pytest/bin/python -m pytest tests/test_zipandpng.py::test_build_default_disguised_output_path_keeps_cover_suffix -v`
Expected: PASS

### Task 4: 更新 README

**Objective:** 让文档反映 WEBP 与自动输出名行为。

**Files:**
- Modify: `README.md`

**Step 1: Update docs**
补充 WEBP 支持，说明 output 可省略，默认生成 `*_disguised.<ext>`。

**Step 2: Verify**
Read: `README.md`
Expected: 文案与 CLI/测试一致。

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
