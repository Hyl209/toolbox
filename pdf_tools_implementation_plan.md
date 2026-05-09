# PDF Tools Implementation Plan

> **For Hermes:** Use subagent-driven-development skill to implement this plan task-by-task.

**Goal:** Add a new `pdf-tools/` module plus a GUI tab for PDF-to-images, PDF merge, PDF split, PDF-to-Word (`.docx`), and text extraction with fallback OCR.

**Architecture:** Keep the existing toolbox pattern: one root GUI entrypoint (`hyl_toolbox.py`) orchestrates independent feature modules. The new module will be a standalone folder whose Python code wraps `pypdf`, `PyMuPDF`, `python-docx`, and optional `pytesseract`/`tesseract` for OCR fallback.

**Tech Stack:** Python, pathlib, pypdf, PyMuPDF (`fitz`), python-docx, pytesseract, PySide6, pytest.

---

### Task 1: Create the new module folder and planning files

**Objective:** Establish the new PDF feature as a sibling module following the existing project layout.

**Files:**
- Create: `pdf-tools/converter.py`
- Create: `pdf-tools/README.md`
- Create: `pdf-tools/tests_pdf_tools.py`
- Create: `pdf-tools/task_plan.md`
- Create: `pdf-tools/findings.md`
- Create: `pdf-tools/progress.md`

### Task 2: Add failing tests for helper logic

**Objective:** Define expected behavior before implementing helpers.

**Files:**
- Test: `pdf-tools/tests_pdf_tools.py`
- Modify: `pdf-tools/converter.py`

Test for:
- collecting supported PDF inputs
- parsing page ranges
- output path generation
- Tesseract dependency probe behavior
- validation of merge/split/text-export inputs

### Task 3: Implement merge/split/path helpers

**Objective:** Add core PDF structure operations first.

**Files:**
- Modify: `pdf-tools/converter.py`
- Test: `pdf-tools/tests_pdf_tools.py`

Implement:
- `collect_pdf_inputs`
- `parse_page_ranges`
- `build_pdf_output_path`
- `merge_pdfs`
- `split_pdf`

### Task 4: Implement PDF-to-images and OCR fallback flow

**Objective:** Add page rendering plus text extraction strategy.

**Files:**
- Modify: `pdf-tools/converter.py`
- Test: `pdf-tools/tests_pdf_tools.py`

Implement:
- `pdf_to_images`
- `probe_tesseract`
- `extract_page_text`
- fallback rule: text layer first, OCR second

### Task 5: Implement TXT and DOCX export

**Objective:** Produce `.txt` and real `.docx` outputs from extracted text.

**Files:**
- Modify: `pdf-tools/converter.py`
- Test: `pdf-tools/tests_pdf_tools.py`

Implement:
- `extract_text_to_txt`
- `pdf_to_docx`
- output naming helpers

### Task 6: Integrate a new GUI tab into `hyl_toolbox.py`

**Objective:** Expose the new feature through the existing sidebar + stacked tab UI.

**Files:**
- Modify: `hyl_toolbox.py`
- Modify: `tests_tool_pages.py`
- Modify: `tests_toolbox.py`

Add:
- module loader for `pdf-tools/converter.py`
- helpers for input collection and summary
- `PdfToolsTab` widget
- sidebar item and stack registration
- settings key for output directory

### Task 7: Add docs and packaging support

**Objective:** Make the feature discoverable and includable in the packaged exe.

**Files:**
- Modify: `README.md`
- Modify: `HylToolbox.spec`
- Modify: `pdf-tools/README.md`

### Task 8: Run final verification

**Objective:** Verify the integrated feature by running the relevant tests.

**Files:**
- Test: `pdf-tools/tests_pdf_tools.py`
- Test: `tests_tool_pages.py`
- Test: `tests_toolbox.py`

Run:
- `python3 -m pytest 'PROJECT_ROOT/pdf-tools/tests_pdf_tools.py' -q`
- `python3 -m pytest 'PROJECT_ROOT/tests_tool_pages.py' 'PROJECT_ROOT/tests_toolbox.py' -q`

