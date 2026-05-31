from __future__ import annotations

from pathlib import Path

from toolbox_app.plugins.base import PluginBase, PluginInfo, lazy_sibling_converter

_converter = lazy_sibling_converter(__file__, "file_hasher_converter")


class FileHasherPlugin(PluginBase):
    def initialize(self, deps: dict = None) -> bool:
        self._deps = deps or {}
        self._widget = None
        self.file_path = ""
        return True

    def get_plugin_info(self) -> PluginInfo:
        return PluginInfo(
            name="file_hasher",
            version="1.0.0",
            description="计算并校验文件 MD5 / SHA1 / SHA256 哈希",
            author="HylToolbox",
            plugin_type="gui",
        )

    def get_sidebar_label(self) -> str:
        return "哈希校验"

    def get_tab_widget(self):
        if self._widget is not None:
            return self._widget

        QWidget = self._deps.get("QWidget")
        QVBoxLayout = self._deps.get("QVBoxLayout")
        QHBoxLayout = self._deps.get("QHBoxLayout")
        QLabel = self._deps.get("QLabel")
        QLineEdit = self._deps.get("QLineEdit")
        QPushButton = self._deps.get("QPushButton")
        QPlainTextEdit = self._deps.get("QPlainTextEdit")
        QFileDialog = self._deps.get("QFileDialog")
        DropZoneCard = self._deps.get("DropZoneCard")
        make_card = self._deps.get("make_card")
        build_global_scrollbar_style = self._deps.get("build_global_scrollbar_style", lambda: "")

        if not all((QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QPlainTextEdit)):
            return None

        widget = QWidget()
        root = QVBoxLayout(widget)
        root.setContentsMargins(0, 0, 0, 0)

        if make_card:
            card, layout = make_card("文件哈希校验", "拖入文件后计算 MD5 / SHA1 / SHA256，可粘贴校验值比对")
        else:
            card = QWidget()
            layout = QVBoxLayout(card)
            layout.addWidget(QLabel("文件哈希校验"))

        if DropZoneCard:
            self.drop_zone = DropZoneCard("拖入需要校验的文件", self._handle_drop)
            layout.addWidget(self.drop_zone)

        file_row = QHBoxLayout()
        self.file_edit = QLineEdit()
        self.file_edit.setPlaceholderText("选择或拖入文件")
        file_row.addWidget(self.file_edit, 1)
        choose_button = QPushButton("选择文件")
        if QFileDialog is not None:
            choose_button.clicked.connect(self._choose_file)
        file_row.addWidget(choose_button)
        layout.addLayout(file_row)

        self.expected_edit = QLineEdit()
        self.expected_edit.setPlaceholderText("可选：粘贴 MD5 / SHA1 / SHA256 校验值")
        layout.addWidget(self.expected_edit)

        action_row = QHBoxLayout()
        calc_button = QPushButton("计算哈希")
        calc_button.clicked.connect(self._calculate)
        action_row.addWidget(calc_button)
        verify_button = QPushButton("校验")
        verify_button.clicked.connect(self._verify)
        action_row.addWidget(verify_button)
        action_row.addStretch(1)
        layout.addLayout(action_row)

        self.result = QPlainTextEdit()
        self.result.setReadOnly(True)
        self.result.setMinimumHeight(170)
        self.result.setStyleSheet(build_global_scrollbar_style())
        layout.addWidget(self.result, 1)

        root.addWidget(card)
        self._widget = widget
        return widget

    def _choose_file(self):
        QFileDialog = self._deps.get("QFileDialog")
        if QFileDialog is None:
            return
        path, _ = QFileDialog.getOpenFileName(self._widget, "选择文件", "", "All Files (*)")
        if path:
            self._use_file(path)

    def _handle_drop(self, paths: list[str]):
        if paths:
            self._use_file(paths[0])

    def _use_file(self, path: str):
        self.file_path = path
        self.file_edit.setText(path)
        if hasattr(self, "drop_zone"):
            self.drop_zone.set_preview_file_icon(path, header_text="已选择文件", body_text=Path(path).name)

    def _selected_file(self) -> str:
        return self.file_edit.text().strip() or self.file_path

    def _calculate(self):
        try:
            hashes = _converter.calculate_hashes(self._selected_file())
        except Exception as exc:
            self.result.setPlainText(f"计算失败：{exc}")
            return
        self.result.setPlainText(self._format_hashes(hashes))

    def _verify(self):
        try:
            state = _converter.verify_file_hash(self._selected_file(), self.expected_edit.text())
        except Exception as exc:
            self.result.setPlainText(f"校验失败：{exc}")
            return
        verdict = "匹配" if state["matched"] else "不匹配"
        self.result.setPlainText(
            f"算法：{state['algorithm'].upper()}\n"
            f"结果：{verdict}\n"
            f"文件：{state['actual']}\n"
            f"输入：{state['expected']}"
        )

    @staticmethod
    def _format_hashes(hashes: dict[str, str]) -> str:
        return "\n".join(f"{name.upper()}: {value}" for name, value in hashes.items())

    def handle_command(self, command: str, **kwargs):
        if command == "calculate_hashes":
            return _converter.calculate_hashes(kwargs.get("path", ""))
        if command == "verify_hash":
            return _converter.verify_file_hash(
                kwargs.get("path", ""),
                kwargs.get("expected", ""),
                kwargs.get("algorithm", "auto"),
            )
        return None

    def cleanup(self):
        self._widget = None
        super().cleanup()
