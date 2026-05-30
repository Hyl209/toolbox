from __future__ import annotations

from toolbox_app.plugins.base import PluginBase, PluginInfo, load_sibling_converter

_converter = load_sibling_converter(__file__, "json_tools_converter")


class JsonToolsPlugin(PluginBase):
    def initialize(self, deps: dict = None) -> bool:
        self._deps = deps or {}
        self._widget = None
        return True

    def get_plugin_info(self) -> PluginInfo:
        return PluginInfo(
            name="json_tools",
            version="1.0.0",
            description="格式化、压缩和校验 JSON 文本",
            author="HylToolbox",
            plugin_type="gui",
        )

    def get_sidebar_label(self) -> str:
        return "JSON 工具"

    def get_tab_widget(self):
        if self._widget is not None:
            return self._widget

        QWidget = self._deps.get("QWidget")
        QVBoxLayout = self._deps.get("QVBoxLayout")
        QHBoxLayout = self._deps.get("QHBoxLayout")
        QLabel = self._deps.get("QLabel")
        QPushButton = self._deps.get("QPushButton")
        QPlainTextEdit = self._deps.get("QPlainTextEdit")
        QCheckBox = self._deps.get("QCheckBox")
        make_card = self._deps.get("make_card")
        build_global_scrollbar_style = self._deps.get("build_global_scrollbar_style", lambda: "")

        if not all((QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QPlainTextEdit)):
            return None

        widget = QWidget()
        root = QVBoxLayout(widget)
        root.setContentsMargins(0, 0, 0, 0)

        if make_card:
            card, layout = make_card("JSON 工具", "格式化、压缩和校验 JSON 文本")
        else:
            card = QWidget()
            layout = QVBoxLayout(card)
            layout.addWidget(QLabel("JSON 工具"))

        self.input_edit = QPlainTextEdit()
        self.input_edit.setPlaceholderText('粘贴 JSON，例如 {"name":"HylToolbox"}')
        self.input_edit.setMinimumHeight(180)
        self.input_edit.setStyleSheet(build_global_scrollbar_style())
        layout.addWidget(self.input_edit)

        action_row = QHBoxLayout()
        format_button = QPushButton("格式化")
        format_button.clicked.connect(self._format)
        action_row.addWidget(format_button)
        minify_button = QPushButton("压缩")
        minify_button.clicked.connect(self._minify)
        action_row.addWidget(minify_button)
        validate_button = QPushButton("校验")
        validate_button.clicked.connect(self._validate)
        action_row.addWidget(validate_button)
        self.sort_checkbox = QCheckBox("按键排序") if QCheckBox else None
        if self.sort_checkbox is not None:
            action_row.addWidget(self.sort_checkbox)
        action_row.addStretch(1)
        layout.addLayout(action_row)

        self.output_edit = QPlainTextEdit()
        self.output_edit.setReadOnly(True)
        self.output_edit.setPlaceholderText("处理结果")
        self.output_edit.setMinimumHeight(180)
        self.output_edit.setStyleSheet(build_global_scrollbar_style())
        layout.addWidget(self.output_edit, 1)

        root.addWidget(card)
        self._widget = widget
        return widget

    def _input_text(self) -> str:
        return self.input_edit.toPlainText()

    def _sort_keys(self) -> bool:
        return bool(self.sort_checkbox and self.sort_checkbox.isChecked())

    def _format(self):
        self._run_text_action(lambda text: _converter.format_json(text, sort_keys=self._sort_keys()))

    def _minify(self):
        self._run_text_action(lambda text: _converter.minify_json(text, sort_keys=self._sort_keys()))

    def _validate(self):
        try:
            state = _converter.validate_json(self._input_text())
        except Exception as exc:
            self.output_edit.setPlainText(f"校验失败：{exc}")
            return
        self.output_edit.setPlainText(f"JSON 有效：{state['type']}，条目数 {state['items']}")

    def _run_text_action(self, action):
        try:
            self.output_edit.setPlainText(action(self._input_text()))
        except Exception as exc:
            self.output_edit.setPlainText(f"处理失败：{exc}")

    def handle_command(self, command: str, **kwargs):
        text = kwargs.get("text", "")
        if command == "format_json":
            return _converter.format_json(
                text,
                indent=kwargs.get("indent", 2),
                sort_keys=kwargs.get("sort_keys", False),
            )
        if command == "minify_json":
            return _converter.minify_json(text, sort_keys=kwargs.get("sort_keys", False))
        if command == "validate_json":
            return _converter.validate_json(text)
        return None

    def cleanup(self):
        self._widget = None
        super().cleanup()
