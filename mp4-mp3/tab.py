from __future__ import annotations

from pathlib import Path

_MP4_DIR = Path(__file__).resolve().parent


def _load_mp4_converter():
    from toolbox_app.loaders import load_module_once
    return load_module_once('mp4_converter_module', _MP4_DIR / 'converter.py')


_MP4_SUFFIXES = {'.mp4'}


def collect_mp4_inputs(paths: list[str]) -> list[Path]:
    from toolbox_app.tab_utils import collect_inputs_by_suffix
    return collect_inputs_by_suffix(paths, _MP4_SUFFIXES)


def format_mp4_drop_summary(files: list[Path]) -> str:
    from toolbox_app.tab_utils import format_drop_summary
    return format_drop_summary(files, '视频')


def validate_mp4_form(files: list[Path], output_dir: str) -> list[str]:
    errors: list[str] = []
    if not files:
        errors.append('请先添加要转换的 .mp4 文件')
    if not output_dir.strip():
        errors.append('请选择输出目录')
    return errors


def build_mp4_tab_class(deps: dict):
    QWidget = deps['QWidget']
    QVBoxLayout = deps['QVBoxLayout']
    QHBoxLayout = deps['QHBoxLayout']
    QLineEdit = deps['QLineEdit']
    QPushButton = deps['QPushButton']
    QLabel = deps['QLabel']
    QPlainTextEdit = deps['QPlainTextEdit']
    QProgressBar = deps['QProgressBar']
    QFileDialog = deps['QFileDialog']
    Qt = deps['Qt']
    DropZoneCard = deps['DropZoneCard']
    load_setting = deps['load_setting']
    save_setting = deps['save_setting']
    make_card = deps['make_card']
    build_global_scrollbar_style = deps['build_global_scrollbar_style']
    show_themed_warning = deps['show_themed_warning']
    show_themed_error = deps['show_themed_error']
    show_themed_success = deps['show_themed_success']
    ROOT = deps['ROOT']

    from toolbox_app.widgets import build_base_tool_tab_class
    BaseToolTab = build_base_tool_tab_class(
        QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton,
        QLabel, QPlainTextEdit, QProgressBar, QFileDialog, Qt,
        DropZoneCard, load_setting, save_setting, make_card,
        build_global_scrollbar_style, ROOT, settings_prefix='mp4mp3')

    class Mp4ToMp3Tab(BaseToolTab):
        def __init__(self, settings):
            super().__init__()
            self.settings = settings
            self.files: list[Path] = []
            root = QVBoxLayout(self)
            card, layout = make_card('MP4转MP3', '拖入 MP4 视频，输出 MP3 音频文件')
            self.drop_zone = DropZoneCard('拖入 .mp4 文件或文件夹', self.add_paths)
            layout.addWidget(self.drop_zone)
            self.init_output_dir_row(layout)
            action_row = QHBoxLayout()
            action_row.addStretch(1)
            self.clear_files_button = QPushButton('清空文件')
            self.clear_files_button.clicked.connect(self.clear_form)
            action_row.addWidget(self.clear_files_button)
            self.convert_button = QPushButton('开始转换')
            self.convert_button.clicked.connect(self.convert_files)
            action_row.addWidget(self.convert_button)
            layout.addLayout(action_row)
            self.init_progress_widget(layout)
            self.init_log_widget(layout)
            root.addWidget(card)

        def add_paths(self, paths: list[str]):
            new_files = collect_mp4_inputs(paths)
            self.add_files_with_dedup(new_files, self.drop_zone)

        def clear_form(self):
            self.clear_files(self.drop_zone, format_mp4_drop_summary([]))

        def convert_files(self):
            output_dir = self.output_edit.text().strip()
            errors = validate_mp4_form(self.files, output_dir)
            if errors:
                show_themed_warning(self, '提示', '\n'.join(errors))
                return
            save_setting(self.settings, 'mp4mp3/output_dir', output_dir)
            self.log.appendPlainText(f'已保存输出目录: {output_dir}')
            self.progress.setMaximum(max(1, len(self.files)))
            self.progress.setValue(0)
            mp4_module = _load_mp4_converter()

            def do_convert():
                success_count = 0
                for idx, src in enumerate(self.files, start=1):
                    out = mp4_module.convert_mp4_to_mp3(src, Path(output_dir) / f'{src.stem}.mp3')
                    self.log.appendPlainText(f'OK {src} -> {out}')
                    success_count += 1
                    self.progress.setValue(idx)
                return success_count

            count = self.run_action_with_error_handling(
                '转换', do_convert,
                f'转换完成: 成功{len(self.files)} 个视频',
                clear_on_success=True,
                drop_zone=self.drop_zone,
                summary_text=format_mp4_drop_summary([]),
            )

    return Mp4ToMp3Tab
