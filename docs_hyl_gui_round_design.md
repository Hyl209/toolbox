# HYL Toolbox Frameless Rounded GUI Design

**Goal:** Make the toolbox window use fully custom-drawn rounded corners on Windows, with the outer shell, left navigation, and right content surfaces visually aligned like an Apple-style card layout, while preserving frameless drag and maximize/restore behavior.

**Architecture:** Keep the existing frameless QMainWindow + custom title bar structure, but move visual responsibility for the outer shell to a custom paintEvent on ToolboxWindow. Use a transparent top-level window, disable system-provided background/border reliance, and make all visible surfaces align to a single radius system. Use normal mode with shadow padding and rounded corners; use maximized mode with zero outer padding and square edges to avoid border artifacts at screen edges.

**Scope:** Only update PROJECT_ROOT/hyl_toolbox.py. No feature changes to the left menu, tool tabs, or business logic.

## Design decisions

1. Top-level window becomes translucent
   - Apply `Qt.WA_TranslucentBackground` to the main window, not only an inner child.
   - Keep `Qt.FramelessWindowHint` and do not depend on system frame/shadow.

2. Outer shell is custom painted
   - Draw the background, border, and optional soft edge/shadow in `ToolboxWindow.paintEvent` using antialiasing.
   - Avoid relying on QMainWindow/QWidget default backgrounds, which can leak black/white corners on Windows.

3. Unified radius system
   - Outer window radius: primary radius used by the shell.
   - Sidebar panel: large radius on outer-facing corners, smaller radius on inner seam corners.
   - Main content region: mirror the sidebar logic so the two inner panels visually nest into the outer shell.

4. Maximized-mode fallback
   - When maximized, remove custom outer margins and disable rounded corners/shadow so the window can sit flush with the desktop edges.
   - Keep existing maximize/restore toggle semantics.

5. No layout breakage
   - Preserve the current left sidebar width, stack widget usage, and drag bar placement.
   - Only change wrappers/styles/painting needed for geometry and visuals.

## Target geometry system

Normal window:
- outer visual padding: 12 px
- outer shell radius: 28 px
- inner content radius: 24 px
- left/right split panels: 24 px outer corners, 16 px inner seam corners

Maximized window:
- outer visual padding: 0 px
- outer shell radius: 0 px
- content padding reduced so no black/white edge appears

## Planned code changes

1. Add constants for radii/margins near the stylesheet section.
2. Remove global dependency on QMainWindow/QWidget solid backgrounds that can show through the transparent top-level window.
3. Add object names/properties for sidebar panel and main stack wrapper so their radii can be styled independently.
4. Wrap the stacked widget in a dedicated right-side panel frame instead of styling the raw QStackedWidget directly.
5. Add helper(s) in ToolboxWindow to compute current visual metrics for normal vs maximized mode.
6. Add `resizeEvent`/state refresh hooks if needed so layout margins update immediately after maximize/restore.
7. Implement `paintEvent` on ToolboxWindow to draw the antialiased outer shell.
8. Keep drag/max/restore behavior intact.

## Verification plan

1. Syntax-check the file with Python compilation.
2. Instantiate the window offscreen via `build_main_window_for_test()`.
3. Verify:
   - main window has `WA_TranslucentBackground`
   - frameless flag still present
   - central/root/content widgets exist
   - maximized toggle still changes button state without exception
4. If possible, capture a rendered offscreen image or at least ensure paintEvent can run without errors.

## Acceptance criteria

- No visible system border/background dependence in code path.
- Outer four corners use custom rounded rendering.
- Sidebar and right content panel corners correspond to the outer shell instead of fighting it.
- No black/white edge introduced by QWidget/QMainWindow default paints.
- Existing drag bar and maximize/restore still function.

