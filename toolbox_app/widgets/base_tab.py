from __future__ import annotations

from pathlib import Path
from typing import Callable

from .dialogs import show_themed_error, show_themed_success


def build_base_tool_tab_class(QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton,
                               QLabel, QPlainTextEdit, QProgressBar, QFileDialog, Qt,
                               DropZoneCard, load_setting, save_setting, make_card,
                               build_global_scrollbar_style, ROOT, settings_prefix: str):
    """Return a BaseToolTab class with common UI helpers for tool tabs.

    Args:
        settings_prefix: The INI section prefix, e.g. 'mp4mp3', 'imageconvert'.
    """

    class BaseToolTab(QWidget):
        _settings_prefix = settings_prefix

        def init_output_dir_row(self, layout, placeholder='选择输出目录', setting_suffix='output_dir'):
            """Create output directory row with choose button. Attaches self.output_edit and self._choose_btn."""
            row = QHBoxLayout()
            self.output_edit = QLineEdit(load_setting(self.settings, f'{self._settings_prefix}/{setting_suffix}'))
            self.output_edit.setPlaceholderText(placeholder)
            self._choose_btn = QPushButton('选择路径')
            self._choose_btn.clicked.connect(self.choose_output_dir)
            row.addWidget(self.output_edit)
            row.addWidget(self._choose_btn)
            layout.addLayout(row)

        def init_log_widget(self, layout, min_height=140):
            """Create read-only log widget. Attaches self.log."""
            self.log = QPlainTextEdit()
            self.log.setReadOnly(True)
            self.log.setMinimumHeight(min_height)
            self.log.setStyleSheet(build_global_scrollbar_style())
            layout.addWidget(self.log)

        def init_progress_widget(self, layout):
            """Create progress bar. Attaches self.progress."""
            self.progress = QProgressBar()
            layout.addWidget(self.progress)

        def choose_output_dir(self):
            """Open directory dialog and save selection."""
            path = QFileDialog.getExistingDirectory(
                self, '选择输出目录', self.output_edit.text() or str(ROOT))
            if path:
                self.output_edit.setText(path)
                save_setting(self.settings, f'{self._settings_prefix}/output_dir', path)

        # --- Common business-logic helpers (Phase 4 refactor) ---

        def add_files_with_dedup(self, new_files: list[Path], drop_zone,
                                 log_prefix: str = '') -> list[Path]:
            """Merge new_files into self.files, update drop_zone preview, log result.

            Returns list of newly added files.
            """
            from toolbox_app.tab_utils import merge_new_files
            added = merge_new_files(self.files, new_files)
            if self.files:
                drop_zone.set_preview_file_icon(
                    str(self.files[0]),
                    header_text=f'已添加 {len(self.files)} 个文件',
                    body_text='\n'.join(p.stem for p in self.files[:3]) + (
                        f'\n... 另有 {len(self.files) - 3} 个文件' if len(self.files) > 3 else ''),
                )
            if added:
                self.log.appendPlainText(log_prefix + '\n'.join(p.stem for p in added))
            else:
                self.log.appendPlainText('没有新增文件')
            return added

        def clear_files(self, drop_zone, summary_text: str):
            """Clear self.files and reset drop_zone."""
            had_files = bool(self.files)
            self.files = []
            drop_zone.set_body_text(summary_text)
            if had_files:
                self.log.appendPlainText('已清空文件')

        def run_action_with_error_handling(self, action_name: str, func: Callable,
                                           success_message: str,
                                           clear_on_success: bool = True,
                                           drop_zone=None, summary_text: str = ''):
            """Execute func() wrapped in standard error handling.

            Shows success/error dialogs, logs result, optionally clears form.
            """
            try:
                result = func()
                self.log.appendPlainText(success_message)
                show_themed_success(self, '完成', [success_message])
                if clear_on_success and drop_zone and summary_text:
                    self.clear_files(drop_zone, summary_text)
                return result
            except Exception as exc:
                self.log.appendPlainText(f'ERROR {exc}')
                show_themed_error(self, f'{action_name}失败', str(exc))
                return None

    return BaseToolTab
