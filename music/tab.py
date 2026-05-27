from __future__ import annotations

from pathlib import Path

_MUSIC_DIR = Path(__file__).resolve().parent


def _load_ncm_module():
    from toolbox_app.loaders import load_module_once
    return load_module_once('music_ncm_to_mp3', _MUSIC_DIR / 'ncm_to_mp3.py')


def collect_music_inputs(paths: list[str]) -> list[Path]:
    ncm_module = _load_ncm_module()
    return ncm_module.collect_input_paths([Path(p) for p in paths])


def get_music_backend_status() -> tuple[bool, str]:
    ncm_module = _load_ncm_module()
    return ncm_module.probe_converter_backend()


def format_music_drop_summary(files: list[Path]) -> str:
    return '拖入ncm文件'


def get_music_file_items(paths: list[str]) -> list[dict[str, str]]:
    ncm_module = _load_ncm_module()
    files = ncm_module.collect_input_paths([Path(p) for p in paths])
    return [ncm_module.extract_song_info(path) for path in files]


def build_music_item_text(item: dict[str, str]) -> str:
    title = str(item.get('title', '')).strip() or Path(str(item.get('file_path', ''))).stem
    artist = str(item.get('artist', '')).strip()
    return f'{title}\n{artist}' if artist else title


def format_music_log_added(items: list[dict[str, str]]) -> str:
    if not items:
        return '🫥 没有新增歌曲'
    lines = ['🎵 已添加歌曲', '────────────']
    for index, item in enumerate(items, start=1):
        title = str(item.get('title', '')).strip() or Path(str(item.get('file_path', ''))).stem
        artist = str(item.get('artist', '')).strip()
        lines.append(f'• {index:02d}｜{title}')
        if artist:
            lines.append(f'   👤 {artist}')
    return '\n'.join(lines)


def format_music_log_output_dir(output_dir: str) -> str:
    return f'📁 输出目录\n────────────\n{output_dir}'


def format_music_log_success(src: Path, out: Path) -> str:
    return '\n'.join([
        '✅ 转换成功',
        '────────────',
        f'🎵 {src.name}',
        f'💿 {out.name}',
    ])


def format_music_log_delete(src: Path) -> str:
    return f'🗑 已删除原文件\n────────────\n{src.name}'


def format_music_log_delete_failed(src: Path, exc: Exception) -> str:
    return f'⚠️ 删除失败\n────────────\n{src.name}\n{exc}'


def format_music_log_missing_dependency(message: str) -> str:
    return f'⚠️ 缺少依赖\n────────────\n{message}'


def format_music_log_summary(success_count: int, fail_count: int, deleted_count: int) -> str:
    lines = [
        '✨ 转换完成',
        '────────────',
        f'✅ 成功：{success_count}',
        f'❌ 失败：{fail_count}',
    ]
    if deleted_count:
        lines.append(f'🗑 删除：{deleted_count}')
    return '\n'.join(lines)


def format_music_log_error(exc: Exception) -> str:
    return f'❌ 转换失败\n────────────\n{exc}'


def build_music_tab_class(deps: dict[str, object]):
    QWidget = deps['QWidget']
    QVBoxLayout = deps['QVBoxLayout']
    QHBoxLayout = deps['QHBoxLayout']
    QScrollArea = deps['QScrollArea']
    QFrame = deps['QFrame']
    QLineEdit = deps['QLineEdit']
    QPushButton = deps['QPushButton']
    QLabel = deps['QLabel']
    QPlainTextEdit = deps['QPlainTextEdit']
    QProgressBar = deps['QProgressBar']
    QFileDialog = deps['QFileDialog']
    QCheckBox = deps['QCheckBox']
    Qt = deps['Qt']
    DropZoneCard = deps['DropZoneCard']
    load_setting = deps['load_setting']
    save_setting = deps['save_setting']
    make_card = deps['make_card']
    make_transparent_row = deps['make_transparent_row']
    build_global_scrollbar_style = deps['build_global_scrollbar_style']
    build_music_scroll_area_style = deps['build_music_scroll_area_style']
    show_themed_warning = deps['show_themed_warning']
    show_themed_error = deps['show_themed_error']
    show_themed_success = deps['show_themed_success']
    load_pixmap_from_data_url = deps['load_pixmap_from_data_url']
    ROOT = deps['ROOT']

    class MusicTab(QWidget):
        def __init__(self, settings):
            super().__init__()
            self.settings = settings
            self.files: list[Path] = []
            self.file_items: list[dict[str, str]] = []
            root = QVBoxLayout(self)
            card, layout = make_card('NCM转换MP3')
            self.drop_zone = DropZoneCard('拖入.ncm文件', self.add_paths)
            self.song_list_scroll = QScrollArea()
            self.song_list_scroll.setWidgetResizable(True)
            self.song_list_scroll.setMinimumHeight(260)
            self.song_list_scroll.setFrameShape(QFrame.NoFrame)
            self.song_list_scroll.setStyleSheet(build_music_scroll_area_style())
            self.song_list_container = QWidget()
            self.song_list_container.setStyleSheet('background: transparent;')
            self.song_list_layout = QVBoxLayout(self.song_list_container)
            self.song_list_layout.setContentsMargins(0, 0, 0, 0)
            self.song_list_layout.setSpacing(8)
            self.song_list_layout.setAlignment(Qt.AlignTop)
            self.song_list_scroll.setWidget(self.song_list_container)
            self.drop_zone.set_content_widget(self.song_list_scroll)
            layout.addWidget(self.drop_zone)
            row = QHBoxLayout()
            self.output_edit = QLineEdit(load_setting(settings, 'music/output_dir'))
            self.output_edit.setPlaceholderText('选择输出目录')
            choose_btn = QPushButton('选择路径')
            choose_btn.clicked.connect(self.choose_output_dir)
            row.addWidget(self.output_edit)
            row.addWidget(choose_btn)
            layout.addLayout(row)
            action_row_widget, action_row = make_transparent_row()
            self.overwrite_checkbox = QCheckBox('覆盖同名文件')
            action_row.addWidget(self.overwrite_checkbox)
            self.delete_source_checkbox = QCheckBox('删除原 NCM')
            action_row.addWidget(self.delete_source_checkbox)
            action_row.addStretch(1)
            self.clear_files_button = QPushButton('清空文件')
            self.clear_files_button.clicked.connect(self.clear_selected_files)
            action_row.addWidget(self.clear_files_button)
            self.convert_button = QPushButton('开始转换')
            self.convert_button.clicked.connect(self.convert_files)
            action_row.addWidget(self.convert_button)
            layout.addWidget(action_row_widget)
            self.progress = QProgressBar()
            layout.addWidget(self.progress)
            self.log = QPlainTextEdit()
            self.log.setReadOnly(True)
            self.log.setMinimumHeight(140)
            self.log.setStyleSheet(build_global_scrollbar_style())
            layout.addWidget(self.log)
            root.addWidget(card)
            self.refresh_song_list()

        def add_paths(self, paths: list[str]):
            items = get_music_file_items(paths)
            existing = {p.resolve() for p in self.files}
            new_items: list[dict[str, str]] = []
            for item in items:
                file_path = Path(str(item.get('file_path', ''))).resolve()
                if file_path not in existing:
                    normalized = dict(item)
                    normalized['file_path'] = str(file_path)
                    self.files.append(file_path)
                    self.file_items.append(normalized)
                    existing.add(file_path)
                    new_items.append(normalized)
            self.refresh_song_list()
            self.log.appendPlainText(format_music_log_added(new_items))

        def choose_output_dir(self):
            path = QFileDialog.getExistingDirectory(self, '选择输出目录', self.output_edit.text() or str(ROOT))
            if path:
                self.output_edit.setText(path)
                save_setting(self.settings, 'music/output_dir', path)
                self.log.appendPlainText(format_music_log_output_dir(path))

        def refresh_song_list(self):
            has_items = bool(self.file_items)
            self.drop_zone.set_body_text(format_music_drop_summary(self.files))
            self.drop_zone.set_content_mode(has_items)
            self.clear_files_button.setEnabled(has_items)
            while self.song_list_layout.count():
                item = self.song_list_layout.takeAt(0)
                widget = item.widget()
                if widget is not None:
                    widget.deleteLater()
            if not has_items:
                return
            for index, item in enumerate(self.file_items, start=1):
                self.song_list_layout.addWidget(self.build_song_item_widget(index, item))
            self.song_list_layout.addStretch(1)

        def clear_selected_files(self):
            if not self.file_items:
                return
            cleared_count = len(self.file_items)
            self.files = []
            self.file_items = []
            self.refresh_song_list()
            self.log.appendPlainText(f'已清空 {cleared_count} 个待转换文件')

        def remove_song_item(self, file_path: str):
            target = Path(file_path).resolve()
            original_count = len(self.file_items)
            self.file_items = [item for item in self.file_items if Path(str(item.get('file_path', ''))).resolve() != target]
            self.files = [path for path in self.files if path.resolve() != target]
            if len(self.file_items) != original_count:
                self.refresh_song_list()
                self.log.appendPlainText(f'已移除: {target.stem}')

        def build_song_item_widget(self, index: int, item: dict[str, str]):
            row = QFrame()
            row.setStyleSheet('background: transparent; border: none;')
            layout = QHBoxLayout(row)
            layout.setContentsMargins(14, 12, 14, 12)
            layout.setSpacing(12)
            cover_label = QLabel()
            cover_label.setFixedSize(56, 56)
            cover_label.setAlignment(Qt.AlignCenter)
            cover_label.setStyleSheet('border-radius: 12px; background-color: rgba(120, 146, 184, 0.18);')
            pixmap = load_pixmap_from_data_url(str(item.get('cover_data_url', '')))
            if pixmap is not None:
                cover_label.setPixmap(pixmap.scaled(56, 56, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation))
            else:
                cover_label.setText('♪')
            layout.addWidget(cover_label)
            text_col = QVBoxLayout()
            text_col.setContentsMargins(0, 0, 0, 0)
            text_col.setSpacing(4)
            title_label = QLabel(str(item.get('title', '')) or Path(str(item.get('file_path', ''))).stem)
            title_label.setStyleSheet('font-size: 14px; font-weight: 700;')
            title_label.setWordWrap(True)
            text_col.addWidget(title_label)
            artist_text = str(item.get('artist', '')).strip() or Path(str(item.get('file_path', ''))).name
            artist_label = QLabel(artist_text)
            artist_label.setProperty('cardSub', True)
            artist_label.setWordWrap(True)
            text_col.addWidget(artist_label)
            layout.addLayout(text_col, 1)
            index_label = QLabel(f'{index:02d}')
            index_label.setStyleSheet('font-size: 12px; color: #9aa6b5; font-weight: 600;')
            layout.addWidget(index_label, 0, Qt.AlignRight | Qt.AlignVCenter)
            remove_button = QPushButton('✕')
            remove_button.setCursor(Qt.PointingHandCursor)
            remove_button.setFixedWidth(18)
            remove_button.setFlat(True)
            remove_button.setStyleSheet(
                'QPushButton {border: none; background: transparent; color: #aeb8c6; font-size: 14px; font-weight: 700; padding: 0px;} '
                'QPushButton:hover {background: transparent; color: #f3c1c1;}'
            )
            remove_button.clicked.connect(lambda _checked=False, path=str(item.get('file_path', '')): self.remove_song_item(path))
            layout.addWidget(remove_button, 0, Qt.AlignRight | Qt.AlignVCenter)
            return row

        def convert_files(self):
            output_dir = self.output_edit.text().strip()
            if not output_dir:
                show_themed_warning(self, '提示', '请先选择输出目录')
                return
            if not self.files:
                show_themed_warning(self, '提示', '请先添加要转换的 .ncm 文件')
                return
            available, message = get_music_backend_status()
            if not available:
                show_themed_warning(self, '缺少依赖', message)
                self.log.appendPlainText(format_music_log_missing_dependency(message))
                return
            save_setting(self.settings, 'music/output_dir', output_dir)
            self.log.appendPlainText(format_music_log_output_dir(output_dir))
            self.progress.setMaximum(max(1, len(self.files)))
            self.progress.setValue(0)
            delete_source = self.delete_source_checkbox.isChecked()
            ncm_module = _load_ncm_module()
            success_count = 0
            deleted_count = 0
            info_by_src = {Path(str(item.get('file_path', ''))).resolve(): item for item in self.file_items}
            try:
                for idx, (src, out) in enumerate(ncm_module.convert_many(self.files, Path(output_dir), self.overwrite_checkbox.isChecked()), start=1):
                    src_path = Path(src).resolve()
                    out_path = Path(out).resolve()
                    if src_path in info_by_src:
                        enriched = ncm_module.enrich_song_info_from_mp3(info_by_src[src_path], out_path)
                        info_by_src[src_path].update(enriched)
                    self.log.appendPlainText(format_music_log_success(src_path, out_path))
                    success_count += 1
                    if delete_source and out_path.exists():
                        try:
                            src_path.unlink()
                            deleted_count += 1
                            self.log.appendPlainText(format_music_log_delete(src_path))
                        except Exception as exc:
                            self.log.appendPlainText(format_music_log_delete_failed(src_path, exc))
                    self.progress.setValue(idx)
                fail_count = max(0, len(self.files) - success_count)
                lines = [
                    f'✅ 成功：{success_count}个',
                    f'❌ 失败：{fail_count}个',
                ]
                if deleted_count:
                    lines.append(f'🗑 删除：{deleted_count}个')
                self.refresh_song_list()
                self.files = []
                self.file_items = []
                self.refresh_song_list()
                show_themed_success(self, '完成', lines)
                self.log.appendPlainText(format_music_log_summary(success_count, fail_count, deleted_count))
            except Exception as exc:
                self.log.appendPlainText(format_music_log_error(exc))
                show_themed_error(self, '转换失败', str(exc))

    return MusicTab
