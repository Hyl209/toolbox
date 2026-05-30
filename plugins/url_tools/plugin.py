from __future__ import annotations

from toolbox_app.plugins.base import PluginBase, PluginInfo, load_sibling_converter

_converter = load_sibling_converter(__file__, "url_tools_converter")


class UrlToolsPlugin(PluginBase):
    def initialize(self, deps: dict = None) -> bool:
        self._deps = deps or {}
        self._widget = None
        return True

    def get_plugin_info(self) -> PluginInfo:
        return PluginInfo(
            name="url_tools",
            version="1.0.0",
            description="URL 编码、解码和查询参数解析",
            author="HylToolbox",
            plugin_type="gui",
            sidebar_label="URL 工具",
        )

    def get_sidebar_label(self) -> str:
        return "URL 工具"

    def get_tab_widget(self):
        if self._widget is not None:
            return self._widget

        QWidget = self._deps.get("QWidget")
        QVBoxLayout = self._deps.get("QVBoxLayout")
        QHBoxLayout = self._deps.get("QHBoxLayout")
        QLabel = self._deps.get("QLabel")
        QPushButton = self._deps.get("QPushButton")
        QPlainTextEdit = self._deps.get("QPlainTextEdit")
        make_card = self._deps.get("make_card")
        build_global_scrollbar_style = self._deps.get("build_global_scrollbar_style", lambda: "")

        if not all((QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QPlainTextEdit)):
            return None

        widget = QWidget()
        root = QVBoxLayout(widget)
        root.setContentsMargins(0, 0, 0, 0)

        if make_card:
            card, layout = make_card("URL 工具", "编码、解码、解析链接查询参数")
        else:
            card = QWidget()
            layout = QVBoxLayout(card)
            layout.addWidget(QLabel("URL 工具"))

        self.input_edit = QPlainTextEdit()
        self.input_edit.setPlaceholderText("粘贴 URL、查询字符串或需要编码的文本")
        self.input_edit.setMinimumHeight(160)
        self.input_edit.setStyleSheet(build_global_scrollbar_style())
        layout.addWidget(self.input_edit)

        action_row = QHBoxLayout()
        actions = [
            ("编码", self._encode),
            ("解码", self._decode),
            ("解析参数", self._format_query),
            ("URL 摘要", self._summarize),
        ]
        for label, handler in actions:
            button = QPushButton(label)
            button.clicked.connect(handler)
            action_row.addWidget(button)
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

    def _run_action(self, action):
        try:
            self.output_edit.setPlainText(action(self._input_text()))
        except Exception as exc:
            self.output_edit.setPlainText(f"处理失败：{exc}")

    def _encode(self):
        self._run_action(_converter.encode_url_component)

    def _decode(self):
        self._run_action(_converter.decode_url_component)

    def _format_query(self):
        self._run_action(_converter.format_query_params)

    def _summarize(self):
        def render(text: str) -> str:
            summary = _converter.summarize_url(text)
            return "\n".join(f"{key}: {value}" for key, value in summary.items() if value)

        self._run_action(render)

    def handle_command(self, command: str, **kwargs):
        text = kwargs.get("text", "")
        if command == "encode_url":
            return _converter.encode_url_component(text, safe=kwargs.get("safe", ""))
        if command == "decode_url":
            return _converter.decode_url_component(text)
        if command == "parse_query":
            return _converter.parse_query_string(text)
        if command == "format_query":
            return _converter.format_query_params(text)
        if command == "summarize_url":
            return _converter.summarize_url(text)
        return None

    def cleanup(self):
        self._widget = None
        super().cleanup()
