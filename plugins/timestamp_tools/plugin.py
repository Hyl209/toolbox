from __future__ import annotations

from toolbox_app.plugins.base import PluginBase, PluginInfo, lazy_sibling_converter

_converter = lazy_sibling_converter(__file__, "timestamp_tools_converter")


class TimestampToolsPlugin(PluginBase):
    def initialize(self, deps: dict = None) -> bool:
        self._deps = deps or {}
        self._widget = None
        return True

    def get_plugin_info(self) -> PluginInfo:
        return PluginInfo(
            name="timestamp_tools",
            version="1.0.0",
            description="时间戳与日期时间互转",
            author="HylToolbox",
            plugin_type="gui",
        )

    def get_sidebar_label(self) -> str:
        return "时间戳工具"

    def get_tab_widget(self):
        if self._widget is not None:
            return self._widget

        QWidget = self._deps.get("QWidget")
        QVBoxLayout = self._deps.get("QVBoxLayout")
        QHBoxLayout = self._deps.get("QHBoxLayout")
        QLabel = self._deps.get("QLabel")
        QPushButton = self._deps.get("QPushButton")
        QPlainTextEdit = self._deps.get("QPlainTextEdit")
        QLineEdit = self._deps.get("QLineEdit")
        make_card = self._deps.get("make_card")
        build_global_scrollbar_style = self._deps.get("build_global_scrollbar_style", lambda: "")

        if not all((QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QPlainTextEdit, QLineEdit)):
            return None

        widget = QWidget()
        root = QVBoxLayout(widget)
        root.setContentsMargins(0, 0, 0, 0)

        if make_card:
            card, layout = make_card("时间戳工具", "时间戳与日期时间互转")
        else:
            card = QWidget()
            layout = QVBoxLayout(card)
            layout.addWidget(QLabel("时间戳工具"))

        tz_row = QHBoxLayout()
        tz_row.addWidget(QLabel("时区"))
        self.tz_edit = QLineEdit("+08:00")
        self.tz_edit.setPlaceholderText("+08:00 / UTC / -05:00")
        self.tz_edit.setMaximumWidth(160)
        tz_row.addWidget(self.tz_edit)
        tz_row.addStretch(1)
        layout.addLayout(tz_row)

        self.input_edit = QPlainTextEdit()
        self.input_edit.setPlaceholderText("输入时间戳或日期时间，例如 1717041600 / 2024-05-30 12:00:00")
        self.input_edit.setMinimumHeight(150)
        self.input_edit.setStyleSheet(build_global_scrollbar_style())
        layout.addWidget(self.input_edit)

        action_row = QHBoxLayout()
        now_button = QPushButton("当前时间")
        now_button.clicked.connect(self._show_now)
        action_row.addWidget(now_button)
        to_time_button = QPushButton("转日期")
        to_time_button.clicked.connect(self._timestamp_to_datetime)
        action_row.addWidget(to_time_button)
        to_stamp_button = QPushButton("转时间戳")
        to_stamp_button.clicked.connect(self._datetime_to_timestamp)
        action_row.addWidget(to_stamp_button)
        action_row.addStretch(1)
        layout.addLayout(action_row)

        self.output_edit = QPlainTextEdit()
        self.output_edit.setReadOnly(True)
        self.output_edit.setPlaceholderText("转换结果")
        self.output_edit.setMinimumHeight(170)
        self.output_edit.setStyleSheet(build_global_scrollbar_style())
        layout.addWidget(self.output_edit, 1)

        root.addWidget(card)
        self._widget = widget
        return widget

    def _input_text(self) -> str:
        return self.input_edit.toPlainText().strip()

    def _tz_offset(self) -> str:
        return self.tz_edit.text().strip() or "+08:00"

    def _show_now(self):
        try:
            state = _converter.current_time(self._tz_offset())
            self.output_edit.setPlainText(
                f"时间：{state['datetime']}\n秒：{state['seconds']}\n毫秒：{state['milliseconds']}\nISO：{state['iso']}"
            )
        except Exception as exc:
            self.output_edit.setPlainText(f"处理失败：{exc}")

    def _timestamp_to_datetime(self):
        try:
            state = _converter.timestamp_to_datetime(self._input_text(), self._tz_offset())
            self.output_edit.setPlainText(
                f"时间：{state['datetime']}\nISO：{state['iso']}\n单位：{state['unit']}\n时区：{state['timezone']}"
            )
        except Exception as exc:
            self.output_edit.setPlainText(f"处理失败：{exc}")

    def _datetime_to_timestamp(self):
        try:
            state = _converter.datetime_to_timestamp(self._input_text(), self._tz_offset())
            self.output_edit.setPlainText(
                f"秒：{state['seconds']}\n毫秒：{state['milliseconds']}\nISO：{state['iso']}"
            )
        except Exception as exc:
            self.output_edit.setPlainText(f"处理失败：{exc}")

    def handle_command(self, command: str, **kwargs):
        tz_offset = kwargs.get("tz_offset", "+08:00")
        text = kwargs.get("text", "")
        if command == "timestamp_to_datetime":
            return _converter.timestamp_to_datetime(text, tz_offset, unit=kwargs.get("unit", "auto"))
        if command == "datetime_to_timestamp":
            return _converter.datetime_to_timestamp(text, tz_offset)
        if command == "current_time":
            return _converter.current_time(tz_offset)
        return None

    def cleanup(self):
        self._widget = None
        super().cleanup()
