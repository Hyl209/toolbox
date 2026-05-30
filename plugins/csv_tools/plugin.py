from __future__ import annotations

from toolbox_app.plugins.base import PluginBase, PluginInfo, load_sibling_converter

_converter = load_sibling_converter(__file__, "csv_tools_converter")


class CsvToolsPlugin(PluginBase):
    def initialize(self, deps: dict = None) -> bool:
        self._deps = deps or {}
        self._widget = None
        return True

    def get_plugin_info(self) -> PluginInfo:
        return PluginInfo(
            name="csv_tools",
            version="1.0.0",
            description="格式化 CSV，转换 TSV 和 JSON",
            author="HylToolbox",
            plugin_type="gui",
        )

    def get_sidebar_label(self) -> str:
        return "CSV 工具"

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
            card, layout = make_card("CSV 工具", "格式化 CSV，转换 TSV 和 JSON")
        else:
            card = QWidget()
            layout = QVBoxLayout(card)
            layout.addWidget(QLabel("CSV 工具"))

        self.input_edit = QPlainTextEdit()
        self.input_edit.setPlaceholderText("粘贴 CSV，例如：name,score")
        self.input_edit.setMinimumHeight(180)
        self.input_edit.setStyleSheet(build_global_scrollbar_style())
        layout.addWidget(self.input_edit)

        action_row = QHBoxLayout()
        format_button = QPushButton("格式化")
        format_button.clicked.connect(self._format)
        action_row.addWidget(format_button)
        tsv_button = QPushButton("转 TSV")
        tsv_button.clicked.connect(self._to_tsv)
        action_row.addWidget(tsv_button)
        json_button = QPushButton("转 JSON")
        json_button.clicked.connect(self._to_json)
        action_row.addWidget(json_button)
        summary_button = QPushButton("统计")
        summary_button.clicked.connect(self._summary)
        action_row.addWidget(summary_button)
        self.header_checkbox = QCheckBox("首行为表头") if QCheckBox else None
        if self.header_checkbox is not None:
            self.header_checkbox.setChecked(True)
            action_row.addWidget(self.header_checkbox)
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

    def _has_header(self) -> bool:
        return bool(self.header_checkbox and self.header_checkbox.isChecked())

    def _format(self):
        self._run(lambda text: _converter.format_csv(text))

    def _to_tsv(self):
        self._run(lambda text: _converter.csv_to_tsv(text))

    def _to_json(self):
        self._run(lambda text: _converter.csv_to_json(text, has_header=self._has_header()))

    def _summary(self):
        try:
            state = _converter.table_summary(self._input_text())
        except Exception as exc:
            self.output_edit.setPlainText(f"统计失败：{exc}")
            return
        self.output_edit.setPlainText(f"行数：{state['rows']}\n最大列数：{state['columns']}")

    def _run(self, action):
        try:
            self.output_edit.setPlainText(action(self._input_text()))
        except Exception as exc:
            self.output_edit.setPlainText(f"处理失败：{exc}")

    def handle_command(self, command: str, **kwargs):
        text = kwargs.get("text", "")
        delimiter = kwargs.get("delimiter", ",")
        if command == "format_csv":
            return _converter.format_csv(text, delimiter=delimiter)
        if command == "csv_to_tsv":
            return _converter.csv_to_tsv(text, delimiter=delimiter)
        if command == "csv_to_json":
            return _converter.csv_to_json(
                text,
                delimiter=delimiter,
                has_header=kwargs.get("has_header", True),
            )
        if command == "table_summary":
            return _converter.table_summary(text, delimiter=delimiter)
        return None

    def cleanup(self):
        self._widget = None
        super().cleanup()
