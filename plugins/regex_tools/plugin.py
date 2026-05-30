from __future__ import annotations

from toolbox_app.plugins.base import PluginBase, PluginInfo, load_sibling_converter

_converter = load_sibling_converter(__file__, "regex_tools_converter")


class RegexToolsPlugin(PluginBase):
    def initialize(self, deps: dict = None) -> bool:
        self._deps = deps or {}
        self._widget = None
        return True

    def get_plugin_info(self) -> PluginInfo:
        return PluginInfo(
            name="regex_tools",
            version="1.0.0",
            description="正则提取、替换和匹配统计",
            author="HylToolbox",
            plugin_type="gui",
        )

    def get_sidebar_label(self) -> str:
        return "正则工具"

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
        QCheckBox = self._deps.get("QCheckBox")
        make_card = self._deps.get("make_card")
        build_global_scrollbar_style = self._deps.get("build_global_scrollbar_style", lambda: "")

        if not all((QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QPlainTextEdit)):
            return None

        widget = QWidget()
        root = QVBoxLayout(widget)
        root.setContentsMargins(0, 0, 0, 0)

        if make_card:
            card, layout = make_card("正则工具", "正则提取、替换和匹配统计")
        else:
            card = QWidget()
            layout = QVBoxLayout(card)
            layout.addWidget(QLabel("正则工具"))

        self.input_edit = QPlainTextEdit()
        self.input_edit.setPlaceholderText("粘贴待处理文本")
        self.input_edit.setMinimumHeight(160)
        self.input_edit.setStyleSheet(build_global_scrollbar_style())
        layout.addWidget(self.input_edit)

        pattern_row = QHBoxLayout()
        self.pattern_edit = QLineEdit()
        self.pattern_edit.setPlaceholderText("正则表达式，例如：https?://\\S+")
        pattern_row.addWidget(self.pattern_edit, 2)
        self.replacement_edit = QLineEdit()
        self.replacement_edit.setPlaceholderText("替换为")
        pattern_row.addWidget(self.replacement_edit, 1)
        layout.addLayout(pattern_row)

        action_row = QHBoxLayout()
        extract_button = QPushButton("提取")
        extract_button.clicked.connect(self._extract)
        action_row.addWidget(extract_button)
        replace_button = QPushButton("替换")
        replace_button.clicked.connect(self._replace)
        action_row.addWidget(replace_button)
        summary_button = QPushButton("统计")
        summary_button.clicked.connect(self._summary)
        action_row.addWidget(summary_button)
        self.ignore_case_checkbox = QCheckBox("忽略大小写") if QCheckBox else None
        if self.ignore_case_checkbox is not None:
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

    def _pattern(self) -> str:
        return self.pattern_edit.text()

    def _ignore_case(self) -> bool:
        return bool(self.ignore_case_checkbox and self.ignore_case_checkbox.isChecked())

    def _extract(self):
        self._run(lambda: _converter.extract_matches_text(
            self._input_text(),
            self._pattern(),
            ignore_case=self._ignore_case(),
        ))

    def _replace(self):
        self._run(lambda: _converter.replace_matches(
            self._input_text(),
            self._pattern(),
            self.replacement_edit.text(),
            ignore_case=self._ignore_case(),
        ))

    def _summary(self):
        try:
            state = _converter.regex_summary(
                self._input_text(),
                self._pattern(),
                ignore_case=self._ignore_case(),
            )
        except Exception as exc:
            self.output_edit.setPlainText(f"统计失败：{exc}")
            return
        self.output_edit.setPlainText(f"匹配数：{state['matches']}\n唯一值：{state['unique']}")

    def _run(self, action):
        try:
            self.output_edit.setPlainText(action())
        except Exception as exc:
            self.output_edit.setPlainText(f"处理失败：{exc}")

    def handle_command(self, command: str, **kwargs):
        text = kwargs.get("text", "")
        pattern = kwargs.get("pattern", "")
        ignore_case = kwargs.get("ignore_case", False)
        if command == "extract_matches":
            return _converter.extract_matches(
                text,
                pattern,
                group=kwargs.get("group", 0),
                ignore_case=ignore_case,
            )
        if command == "extract_matches_text":
            return _converter.extract_matches_text(
                text,
                pattern,
                group=kwargs.get("group", 0),
                ignore_case=ignore_case,
            )
        if command == "replace_matches":
            return _converter.replace_matches(
                text,
                pattern,
                kwargs.get("replacement", ""),
                ignore_case=ignore_case,
            )
        if command == "regex_summary":
            return _converter.regex_summary(text, pattern, ignore_case=ignore_case)
        return None

    def cleanup(self):
        self._widget = None
        super().cleanup()
