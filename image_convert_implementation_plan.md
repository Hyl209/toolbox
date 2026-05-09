# Image Convert Implementation Plan

> **For Hermes:** Use subagent-driven-development skill to implement this plan task-by-task.

**Goal:** Add a new `image-convert/` module plus a GUI tab for JPG/PNG/WebP/HEIC batch conversion with quality control, target-size compression, optional JPG background fill, and auto-resize fallback.

**Architecture:** Keep the existing toolbox pattern: one root GUI entrypoint (`hyl_toolbox.py`) orchestrates independent feature modules. The new module will be a standalone folder whose Python code wraps ImageMagick CLI calls and exposes small, testable helper functions for collection, validation, conversion, and target-size search.

**Tech Stack:** Python, subprocess, pathlib, PySide6, pytest, ImageMagick (`magick` CLI).

---

### Task 1: Create the new module folder and planning files

**Objective:** Establish the new feature as a sibling module following the existing project layout.

**Files:**
- Create: `image-convert/converter.py`
- Create: `image-convert/README.md`
- Create: `image-convert/tests_image_convert.py`
- Create: `image-convert/task_plan.md`
- Create: `image-convert/findings.md`
- Create: `image-convert/progress.md`

**Step 1: Write the initial files**
Create the folder and placeholder files matching existing module conventions.

**Step 2: Verify files exist**
Run a file listing command that shows the new paths.
Expected: all six files are present.

### Task 2: Add failing tests for image helper logic

**Objective:** Define expected behavior before implementing the converter helpers.

**Files:**
- Test: `image-convert/tests_image_convert.py`
- Modify: `image-convert/converter.py`

**Step 1: Write failing tests**
Add tests for:
- collecting supported image inputs recursively
- choosing output suffix
- mapping JPG background option
- validating target size input
- dependency probe behavior when `magick` is absent

**Step 2: Run tests to verify failure**
Run: `pytest /mnt/e/hyl\ tools/image-convert/tests_image_convert.py -q`
Expected: FAIL due to missing functions.

**Step 3: Write minimal implementation**
Implement the helper functions in `converter.py` until tests can pass.

**Step 4: Run tests to verify pass**
Run: `pytest /mnt/e/hyl\ tools/image-convert/tests_image_convert.py -q`
Expected: PASS.

### Task 3: Implement ImageMagick conversion orchestration

**Objective:** Add single-file and batch conversion logic with transparent-output handling and JPG flattening.

**Files:**
- Modify: `image-convert/converter.py`
- Test: `image-convert/tests_image_convert.py`

**Step 1: Add tests for command-building behavior**
Write tests that assert:
- JPG output uses background + alpha removal options
- PNG/WebP/HEIC can preserve alpha when requested
- target output path uses source stem with new suffix

**Step 2: Run tests to verify failure**
Run: `pytest /mnt/e/hyl\ tools/image-convert/tests_image_convert.py -q`
Expected: FAIL on new behaviors.

**Step 3: Implement conversion command construction**
Add subprocess command assembly and execution helpers.

**Step 4: Run tests to verify pass**
Run: `pytest /mnt/e/hyl\ tools/image-convert/tests_image_convert.py -q`
Expected: PASS.

### Task 4: Implement target-size compression loop

**Objective:** Support “compress to target KB” using quality reduction first and dimension reduction second.

**Files:**
- Modify: `image-convert/converter.py`
- Test: `image-convert/tests_image_convert.py`

**Step 1: Add tests for search strategy helpers**
Write tests for:
- quality step generation
- resize step generation
- rejecting invalid target sizes

**Step 2: Run tests to verify failure**
Run: `pytest /mnt/e/hyl\ tools/image-convert/tests_image_convert.py -q`
Expected: FAIL.

**Step 3: Implement target-size helpers**
Implement the compression search helpers and integrate them into conversion flow.

**Step 4: Run tests to verify pass**
Run: `pytest /mnt/e/hyl\ tools/image-convert/tests_image_convert.py -q`
Expected: PASS.

### Task 5: Integrate a new GUI tab into `hyl_toolbox.py`

**Objective:** Expose the new feature through the existing sidebar + stacked tab UI.

**Files:**
- Modify: `hyl_toolbox.py`
- Modify: `tests_tool_pages.py`
- Modify: `tests_toolbox.py`

**Step 1: Write failing GUI tests**
Add tests that assert:
- sidebar contains “图片格式互转”
- new tab validates empty form
- dropped images update summary text

**Step 2: Run targeted tests to verify failure**
Run: `pytest /mnt/e/hyl\ tools/tests_tool_pages.py /mnt/e/hyl\ tools/tests_toolbox.py -q`
Expected: FAIL.

**Step 3: Implement the tab and wiring**
Add:
- module loader for `image-convert/converter.py`
- helpers for input collection and summary
- `ImageConvertTab` widget
- sidebar item and stack registration
- settings key for output directory

**Step 4: Run targeted tests to verify pass**
Run: `pytest /mnt/e/hyl\ tools/tests_tool_pages.py /mnt/e/hyl\ tools/tests_toolbox.py -q`
Expected: PASS.

### Task 6: Add docs and packaging support

**Objective:** Make the feature discoverable and includable in the packaged exe.

**Files:**
- Modify: `README.md`
- Modify: `HylToolbox.spec`
- Modify: `image-convert/README.md`

**Step 1: Update documentation**
Document the new module in the root README and add module-specific usage notes.

**Step 2: Update PyInstaller spec**
Include `image-convert/converter.py` in `datas`.

**Step 3: Verify file content**
Read the updated files and confirm references are present.
Expected: README and spec mention `image-convert`.

### Task 7: Run final verification

**Objective:** Verify the integrated feature by running the relevant tests.

**Files:**
- Test: `image-convert/tests_image_convert.py`
- Test: `tests_tool_pages.py`
- Test: `tests_toolbox.py`

**Step 1: Run the image-convert tests**
Run: `pytest /mnt/e/hyl\ tools/image-convert/tests_image_convert.py -q`
Expected: PASS.

**Step 2: Run the toolbox tests**
Run: `pytest /mnt/e/hyl\ tools/tests_tool_pages.py /mnt/e/hyl\ tools/tests_toolbox.py -q`
Expected: PASS.

**Step 3: Report verification evidence**
Summarize exactly which commands passed and any limitations that remain.
