# Zip+PNG / 真PNG伪装单文件 实现计划

> **For Hermes:** Use subagent-driven-development skill to implement this plan task-by-task.

**Goal:** 把现有 zip+png 工具改造成“真 PNG 封面伪装任意单文件”的命令行工具，输出可正常预览的 PNG，并能恢复原始单文件。

**Architecture:** 继续沿用“合法 PNG 字节 + 自定义尾部元数据 + 原始负载字节”的结构，把内部 zip 语义抽象成 attachment/file。CLI 以 disguise/recover/info 为主命令，并兼容旧 merge/extract 别名以减少使用摩擦。

**Tech Stack:** Python 3、argparse、pathlib、struct、pytest

---

### Task 1: 写负向命令测试

**Objective:** 先锁定新命令 disguise 的基础错误行为。

**Files:**
- Modify: `tests/test_zipandpng.py`
- Test: `tests/test_zipandpng.py`

**Step 1: Write failing test**
增加一个测试：`test_disguise_command_requires_existing_cover_png`，调用 `disguise missing.png payload.exe out.png`，断言退出码为 1，stderr 包含 `输入PNG不存在`。

**Step 2: Run test to verify failure**
Run: `.venv-pytest/bin/python -m pytest tests/test_zipandpng.py::test_disguise_command_requires_existing_cover_png -v`
Expected: FAIL — 还没有 disguise 命令。

**Step 3: Write minimal implementation**
为 CLI 增加 disguise 子命令解析，可先复用 merge 的主体逻辑。

**Step 4: Run test to verify pass**
Run: `.venv-pytest/bin/python -m pytest tests/test_zipandpng.py::test_disguise_command_requires_existing_cover_png -v`
Expected: PASS

### Task 2: 写完整往返测试

**Objective:** 锁定“任意单文件伪装 + 恢复 + 信息查看”的主流程。

**Files:**
- Modify: `tests/test_zipandpng.py`
- Modify: `zipandpng.py`

**Step 1: Write failing test**
把现有 roundtrip 测试改成：使用 `payload.exe`（任意二进制字节）执行 `disguise -> info -> recover`，断言：
- 输出是 .png 文件
- `info` 显示发现附加文件、原文件名、大小
- `recover` 后字节与原始 payload 完全一致

**Step 2: Run test to verify failure**
Run: `.venv-pytest/bin/python -m pytest tests/test_zipandpng.py::test_disguise_recover_and_info_roundtrip_for_single_file -v`
Expected: FAIL — 旧实现仍以 ZIP 命名与文案为主。

**Step 3: Write minimal implementation**
把数据结构从 zip 泛化为 attachment，info/recover 文案同步更新，recover 默认还原原文件名。

**Step 4: Run test to verify pass**
Run: `.venv-pytest/bin/python -m pytest tests/test_zipandpng.py::test_disguise_recover_and_info_roundtrip_for_single_file -v`
Expected: PASS

### Task 3: 保留兼容别名

**Objective:** 在新命令完成后保留 merge/extract 老名字，避免旧用法直接失效。

**Files:**
- Modify: `tests/test_zipandpng.py`
- Modify: `zipandpng.py`

**Step 1: Write failing test**
增加一个测试：旧 `merge` 与 `extract` 依然可用，且行为等同于 `disguise` 与 `recover`。

**Step 2: Run test to verify failure**
Run: `.venv-pytest/bin/python -m pytest tests/test_zipandpng.py::test_legacy_merge_and_extract_aliases_still_work -v`
Expected: FAIL — 若新命令重构后未保留别名。

**Step 3: Write minimal implementation**
让 merge→disguise，extract→recover，共享同一处理函数。

**Step 4: Run test to verify pass**
Run: `.venv-pytest/bin/python -m pytest tests/test_zipandpng.py::test_legacy_merge_and_extract_aliases_still_work -v`
Expected: PASS

### Task 4: 更新说明文档

**Objective:** 让 README 与当前真实能力一致。

**Files:**
- Modify: `README.md`

**Step 1: Write failing doc expectation mentally**
README 目前仍写 ZIP，需要改为“任意单文件 + 真PNG封面伪装”。

**Step 2: Write minimal implementation**
更新命令示例、行为说明、兼容别名说明。

**Step 3: Verify**
Read: `README.md`
Expected: 文案与 CLI/测试一致。

### Task 5: 全量验证

**Objective:** 确认回归通过且语法正常。

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
