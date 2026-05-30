from __future__ import annotations

from toolbox_app.plugins.base import PluginBase, PluginInfo, load_sibling_converter

_converter = load_sibling_converter(__file__, "text_tools_converter")


class TextToolsPlugin(PluginBase):
    def initialize(self, deps: dict = None) -> bool:
        self._deps = deps or {}
        self._widget = None
        return True

    def get_plugin_info(self) -> PluginInfo:
        return PluginInfo(
            name="text_tools",
            version="1.0.0",
            description="清理、去重、排序和转换文本行",
            author="HylToolbox",
            plugin_type="gui",
        )

    def get_sidebar_label(self) -> str:
        return "文本工具"

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
            card, layout = make_card("文本工具", "清理、去重、排序和转换文本行")
        else:
            card = QWidget()
            layout = QVBoxLayout(card)
            layout.addWidget(QLabel("文本工具"))

        self.input_edit = QPlainTextEdit()
        self.input_edit.setPlaceholderText("粘贴待处理文本，每行一条")
        self.input_edit.setMinimumHeight(180)
        self.input_edit.setStyleSheet(build_global_scrollbar_style())
        layout.addWidget(self.input_edit)

        action_row = QHBoxLayout()
        clean_button = QPushButton("清理空行")
        clean_button.clicked.connect(self._clean)
        action_row.addWidget(clean_button)
        dedupe_button = QPushButton("去重")
        dedupe_button.clicked.connect(self._dedupe)
        action_row.addWidget(dedupe_button)
        sort_button = QPushButton("排序")
        sort_button.clicked.connect(self._sort)
        action_row.addWidget(sort_button)
        upper_button = QPushButton("大写")
        upper_button.clicked.connect(lambda: self._case("upper"))
        action_row.addWidget(upper_button)
        lower_button = QPushButton("小写")
        lower_button.clicked.connect(lambda: self._case("lower"))
        action_row.addWidget(lower_button)
        self.ignore_case_checkbox = QCheckBox("忽略大小写") if QCheckBox else None
        if self.ignore_case_checkbox is not None:
            self.ignore_case_checkbox.setChecked(True)
            action_row.addWidget(self.ignore_case_checkbox)
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

    def _case_sensitive(self) -> bool:
        return not bool(self.ignore_case_checkbox and self.ignore_case_checkbox.isChecked())

    def _clean(self):
        self._run(lambda text: _converter.clean_lines(text))

    def _dedupe(self):
        self._run(lambda text: _converter.dedupe_lines(text, case_sensitive=self._case_sensitive()))

    def _sort(self):
        self._run(lambda text: _converter.sort_lines(text, case_sensitive=self._case_sensitive()))

    def _case(self, mode: str):
        self._run(lambda text: _converter.transform_case(text, mode))

    def _run(self, action):
        try:
            self.output_edit.setPlainText(action(self._input_text()))
        except Exception as exc:
            self.output_edit.setPlainText(f"处理失败：{exc}")

    def handle_command(self, command: str, **kwargs):
        text = kwargs.get("text", "")
        if command == "clean_lines":
            return _converter.clean_lines(
                text,
                trim=kwargs.get("trim", True),
                drop_empty=kwargs.get("drop_empty", True),
            )
        if command == "dedupe_lines":
            return _converter.dedupe_lines(
                text,
                case_sensitive=kwargs.get("case_sensitive", True),
                trim=kwargs.get("trim", True),
            )
        if command == "sort_lines":
            return _converter.sort_lines(
                text,
                case_sensitive=kwargs.get("case_sensitive", False),
                reverse=kwargs.get("reverse", False),
            )
        if command == "transform_case":
            return _converter.transform_case(text, kwargs.get("mode", "lower"))
        return None

    def cleanup(self):
        self._widget = None
        super().cleanup()
