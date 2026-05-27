from __future__ import annotations

from pathlib import Path

_MP4_DIR = Path(__file__).resolve().parent


def _load_mp4_converter():
    from toolbox_app.loaders import load_module_once
    return load_module_once('mp4_converter_module', _MP4_DIR / 'converter.py')


def collect_mp4_inputs(paths: list[str]) -> list[Path]:
    unique: dict[Path, None] = {}
    for raw in paths:
        path = Path(raw).resolve()
        if path.is_file() and path.suffix.lower() == '.mp4':
            unique[path] = None
        elif path.is_dir():
            for item in sorted(path.rglob('*.mp4')):
                if item.is_file():
                    unique[item.resolve()] = None
    return sorted(unique.keys())


def format_mp4_drop_summary(files: list[Path]) -> str:
    if not files:
        return '拖入 .mp4 文件或文件夹'
    names = [p.stem for p in files[:6]]
    summary = '\n'.join(names)
    if len(files) > 6:
        summary += f'\n... 另有 {len(files) - 6} 个视频'
    return f'已添加 {len(files)} 个视频\n\n{summary}'


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

    class Mp4ToMp3Tab(QWidget):
        def __init__(self, settings):
            super().__init__()
            self.settings = settings
            self.files: list[Path] = []
            root = QVBoxLayout(self)
            card, layout = make_card('MP4转MP3', '拖入 MP4 视频，输出 MP3 音频文件')
            self.drop_zone = DropZoneCard('拖入 .mp4 文件或文件夹', self.add_paths)
            layout.addWidget(self.drop_zone)
            row = QHBoxLayout()
            self.output_edit = QLineEdit(load_setting(settings, 'mp4mp3/output_dir'))
            self.output_edit.setPlaceholderText('选择输出目录')
            choose_btn = QPushButton('选择路径')
            choose_btn.clicked.connect(self.choose_output_dir)
            row.addWidget(self.output_edit)
            row.addWidget(choose_btn)
            layout.addLayout(row)
            action_row = QHBoxLayout()
            action_row.addStretch(1)
            self.clear_files_button = QPushButton('清空文件')
            self.clear_files_button.clicked.connect(self.clear_form)
            action_row.addWidget(self.clear_files_button)
            self.convert_button = QPushButton('开始转换')
            self.convert_button.clicked.connect(self.convert_files)
            action_row.addWidget(self.convert_button)
            layout.addLayout(action_row)
            self.progress = QProgressBar()
            layout.addWidget(self.progress)
            self.log = QPlainTextEdit()
            self.log.setReadOnly(True)
            self.log.setMinimumHeight(140)
            self.log.setStyleSheet(build_global_scrollbar_style())
            layout.addWidget(self.log)
            root.addWidget(card)

        def add_paths(self, paths: list[str]):
            files = collect_mp4_inputs(paths)
            existing = {p.resolve() for p in self.files}
            new_files: list[Path] = []
            for file in files:
                resolved = file.resolve()
                if resolved not in existing:
                    self.files.append(resolved)
                    existing.add(resolved)
                    new_files.append(resolved)
            if self.files:
                self.drop_zone.set_preview_file_icon(
                    str(self.files[0]),
                    header_text=f'已添加 {len(self.files)} 个视频',
                    body_text='\n'.join(p.stem for p in self.files[:3]) + (f'\n... 另有 {len(self.files) - 3} 个视频' if len(self.files) > 3 else ''),
                )
            else:
                self.drop_zone.set_body_text(format_mp4_drop_summary(self.files))
            if new_files:
                self.log.appendPlainText('\n'.join(p.stem for p in new_files))
            else:
                self.log.appendPlainText('没有新增视频')

        def choose_output_dir(self):
            path = QFileDialog.getExistingDirectory(self, '选择输出目录', self.output_edit.text() or str(ROOT))
            if path:
                self.output_edit.setText(path)
                save_setting(self.settings, 'mp4mp3/output_dir', path)

        def clear_form(self):
            had_files = bool(self.files)
            self.files = []
            self.drop_zone.set_body_text(format_mp4_drop_summary(self.files))
            if had_files:
                self.log.appendPlainText('已清空待转换视频')

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
            success_count = 0
            try:
                for idx, src in enumerate(self.files, start=1):
                    out = mp4_module.convert_mp4_to_mp3(src, Path(output_dir) / f'{src.stem}.mp3')
                    self.log.appendPlainText(f'OK {src} -> {out}')
                    success_count += 1
                    self.progress.setValue(idx)
                self.clear_form()
                summary = f'转换完成: 成功{success_count} 个视频'
                show_themed_success(self, '完成', [summary])
                self.log.appendPlainText(summary)
            except Exception as exc:
                self.log.appendPlainText(f'ERROR {exc}')
                show_themed_error(self, '转换失败', str(exc))

    return Mp4ToMp3Tab
