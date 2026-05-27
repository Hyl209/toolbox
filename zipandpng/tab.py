from __future__ import annotations

from pathlib import Path


def split_dropped_files(paths: list[str]) -> dict[str, str]:
    payload = ''
    cover_png = ''
    image_exts = {'.png', '.jpg', '.jpeg', '.gif', '.webp'}
    for raw in paths:
        path = Path(raw).resolve()
        if path.suffix.lower() in image_exts and not cover_png:
            cover_png = str(path)
        elif not payload:
            payload = str(path)
    return {'payload': payload, 'cover_png': cover_png}


def choose_output_suffix(cover_path: str) -> str:
    suffix = Path(cover_path).suffix.lower().strip()
    if suffix in {'.png', '.jpg', '.jpeg', '.gif', '.webp'}:
        return suffix
    return '.png'


def normalize_output_name(name: str, cover_path: str = '', payload_path: str = '') -> str:
    base = name.strip()
    if not base and payload_path:
        base = Path(payload_path).stem
    if not base:
        base = 'output'
    suffix = choose_output_suffix(cover_path)
    return f'{Path(base).stem}{suffix}'


def validate_zipandpng_form(payload_path: str, cover_png_path: str, output_dir: str, output_name: str) -> list[str]:
    errors: list[str] = []
    if not payload_path:
        errors.append('请选择要伪装的文件')
    elif not Path(payload_path).exists():
        errors.append('要伪装的文件不存在')
    if not cover_png_path:
        errors.append('请选择PNG封面')
    elif not Path(cover_png_path).exists():
        errors.append('PNG封面不存在')
    if not output_dir:
        errors.append('请选择输出目录')
    elif not Path(output_dir).exists():
        errors.append('输出目录不存在')
    if not output_name.strip():
        errors.append('请输入输出文件名')
    return errors


def build_zipandpng_tab_class(deps: dict[str, object]):
    QWidget = deps['QWidget']
    QVBoxLayout = deps['QVBoxLayout']
    QHBoxLayout = deps['QHBoxLayout']
    QLineEdit = deps['QLineEdit']
    QPushButton = deps['QPushButton']
    QLabel = deps['QLabel']
    QPlainTextEdit = deps['QPlainTextEdit']
    QFileDialog = deps['QFileDialog']
    Qt = deps['Qt']
    DropZoneCard = deps['DropZoneCard']
    load_setting = deps['load_setting']
    save_setting = deps['save_setting']
    make_card = deps['make_card']
    build_global_scrollbar_style = deps['build_global_scrollbar_style']
    show_themed_warning = deps['show_themed_warning']
    get_zip_module = deps['get_zip_module']
    ROOT = deps['ROOT']
    from toolbox_app.widgets import build_base_tool_tab_class
    BaseToolTab = build_base_tool_tab_class(
        QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton,
        QLabel, QPlainTextEdit, QProgressBar, QFileDialog, Qt,
        DropZoneCard, load_setting, save_setting, make_card,
        build_global_scrollbar_style, ROOT, settings_prefix='zipandpng')


    class ZipAndPngTab(BaseToolTab):
        def __init__(self, settings):
            super().__init__()
            self.settings = settings
            root = QVBoxLayout(self)
            card, layout = make_card('PNG伪装', '拖入任意文件与 PNG/JPG/GIF/WEBP 封面，输出伪装后的图片文件')
            self.payload_path = ''
            self.cover_path = ''
            self.payload_drop = DropZoneCard('拖入 zip / exe / pdf / mp4 等任意文件', self.handle_payload_drop)
            layout.addWidget(self.payload_drop)
            self.cover_drop = DropZoneCard('拖入 PNG / JPG / GIF / WEBP 封面', self.handle_cover_drop)
            layout.addWidget(self.cover_drop)
            layout.addWidget(QLabel('输出文件名'))
            self.output_name_edit = QLineEdit()
            self.output_name_edit.setPlaceholderText('例如：自定义文件名')
            layout.addWidget(self.output_name_edit)
            row = QHBoxLayout()
            self.output_dir_edit = QLineEdit(load_setting(settings, 'zipandpng/output_dir'))
            self.output_dir_edit.setPlaceholderText('选择或输入伪装 PNG 输出目录')
            choose_btn = QPushButton('选择路径')
            choose_btn.clicked.connect(self.choose_output_dir)
            row.addWidget(self.output_dir_edit)
            row.addWidget(choose_btn)
            layout.addLayout(row)
            action_row = QHBoxLayout()
            action_row.addStretch(1)
            self.clear_files_button = QPushButton('清空文件')
            self.clear_files_button.clicked.connect(self.clear_form)
            action_row.addWidget(self.clear_files_button)
            self.start_button = QPushButton('开始伪装')
            self.start_button.clicked.connect(self.run_disguise)
            action_row.addWidget(self.start_button)
            layout.addLayout(action_row)
            self.log = QPlainTextEdit()
            self.log.setReadOnly(True)
            self.log.setMinimumHeight(140)
            self.log.setStyleSheet(build_global_scrollbar_style())
            layout.addWidget(self.log)
            root.addWidget(card)

        def handle_payload_drop(self, paths: list[str]):
            result = split_dropped_files(paths)
            if result['payload']:
                self.payload_path = result['payload']
                self.payload_drop.set_preview_file_icon(
                    self.payload_path,
                    header_text='已添加载荷文件',
                    body_text=Path(self.payload_path).name,
                )
                if not self.output_name_edit.text().strip():
                    self.output_name_edit.setText(Path(self.payload_path).stem)
            if result['cover_png'] and not self.cover_path:
                self.cover_path = result['cover_png']
                self.cover_drop.set_preview_image(
                    self.cover_path,
                    header_text='已添加封面图',
                    body_text=Path(self.cover_path).name,
                )

        def handle_cover_drop(self, paths: list[str]):
            allowed = {'.png', '.jpg', '.jpeg', '.gif', '.webp'}
            for raw in paths:
                path = Path(raw)
                if path.suffix.lower() in allowed:
                    self.cover_path = str(path.resolve())
                    self.cover_drop.set_preview_image(
                        self.cover_path,
                        header_text='已添加封面图',
                        body_text=Path(self.cover_path).name,
                    )
                    break

        def choose_output_dir(self):
            path = QFileDialog.getExistingDirectory(self, '选择输出目录', self.output_dir_edit.text() or str(ROOT))
            if path:
                self.output_dir_edit.setText(path)
                save_setting(self.settings, 'zipandpng/output_dir', path)

        def clear_form(self):
            had_payload = bool(self.payload_path)
            had_cover = bool(self.cover_path)
            self.payload_path = ''
            self.cover_path = ''
            self.payload_drop.set_body_text('拖入 zip / exe / pdf / mp4 等任意文件')
            self.cover_drop.set_body_text('拖入 PNG / JPG / GIF / WEBP 封面')
            self.output_name_edit.clear()
            if had_payload or had_cover:
                self.log.appendPlainText('已清空伪装文件与封面')

        def run_disguise(self):
            errors = validate_zipandpng_form(
                self.payload_path,
                self.cover_path,
                self.output_dir_edit.text().strip(),
                self.output_name_edit.text().strip(),
            )
            if errors:
                show_themed_warning(self, '提示', '\n'.join(errors))
                return
            save_setting(self.settings, 'zipandpng/output_dir', self.output_dir_edit.text().strip())
            out_name = normalize_output_name(
                self.output_name_edit.text(),
                self.cover_path,
                self.payload_path,
            )
            out_path = Path(self.output_dir_edit.text().strip()) / out_name
            zip_module = get_zip_module()
            zip_module.disguise_file(
                Path(self.cover_path),
                Path(self.payload_path),
                out_path,
            )
            self.log.appendPlainText(f'伪装完成: {out_path}')
            self.clear_form()

    return ZipAndPngTab
