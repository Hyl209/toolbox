from __future__ import annotations

import importlib.util
from pathlib import Path

from toolbox_app.plugins.base import PluginBase, PluginInfo


def _load_converter():
    converter_path = Path(__file__).with_name("converter.py")
    spec = importlib.util.spec_from_file_location("uuid_tools_converter", converter_path)
    if spec is None or spec.loader is None:
        raise RuntimeError("无法加载 UUID 工具插件 converter.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_converter = _load_converter()


class UuidToolsPlugin(PluginBase):
    def initialize(self, deps: dict = None) -> bool:
        self._deps = deps or {}
        self._widget = None
        return True

    def get_plugin_info(self) -> PluginInfo:
        return PluginInfo(
            name="uuid_tools",
            version="1.0.0",
            description="生成、校验和规范化 UUID",
            author="HylToolbox",
            plugin_type="gui",
            sidebar_label="UUID 工具",
        )

    def get_sidebar_label(self) -> str:
        return "UUID 工具"

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
            card, layout = make_card("UUID 工具", "生成、校验和规范化 UUID")
        else:
            card = QWidget()
            layout = QVBoxLayout(card)
            layout.addWidget(QLabel("UUID 工具"))

        count_row = QHBoxLayout()
        count_row.addWidget(QLabel("批量数量"))
        self.count_edit = QLineEdit("10")
        self.count_edit.setMaximumWidth(120)
        self.count_edit.setPlaceholderText("1-500")
        count_row.addWidget(self.count_edit)
        count_row.addStretch(1)
        layout.addLayout(count_row)

        self.input_edit = QPlainTextEdit()
        self.input_edit.setPlaceholderText("粘贴 UUID，可校验、规范化或查看详情")
        self.input_edit.setMinimumHeight(130)
        self.input_edit.setStyleSheet(build_global_scrollbar_style())
        layout.addWidget(self.input_edit)

        action_row = QHBoxLayout()
        actions = [
            ("生成", self._generate_one),
            ("批量生成", self._generate_batch),
            ("规范化", self._normalize),
            ("查看详情", self._describe),
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
        return self.input_edit.toPlainText().strip()

    def _run_action(self, action):
        try:
            result = action()
            if isinstance(result, list):
                result = "\n".join(result)
            elif isinstance(result, dict):
                result = "\n".join(f"{key}: {value}" for key, value in result.items())
            self.output_edit.setPlainText(str(result))
        except Exception as exc:
            self.output_edit.setPlainText(f"处理失败：{exc}")

    def _generate_one(self):
        self._run_action(_converter.generate_uuid4)

    def _generate_batch(self):
        self._run_action(lambda: _converter.generate_uuid_batch(self.count_edit.text()))

    def _normalize(self):
        self._run_action(lambda: _converter.normalize_uuid(self._input_text()))

    def _describe(self):
        self._run_action(lambda: _converter.describe_uuid(self._input_text()))

    def handle_command(self, command: str, **kwargs):
        text = kwargs.get("text", "")
        if command == "generate_uuid":
            return _converter.generate_uuid4(
                uppercase=kwargs.get("uppercase", False),
                hyphenated=kwargs.get("hyphenated", True),
            )
        if command == "generate_uuid_batch":
            return _converter.generate_uuid_batch(
                kwargs.get("count", 10),
                uppercase=kwargs.get("uppercase", False),
                hyphenated=kwargs.get("hyphenated", True),
            )
        if command == "normalize_uuid":
            return _converter.normalize_uuid(
                text,
                uppercase=kwargs.get("uppercase", False),
                hyphenated=kwargs.get("hyphenated", True),
            )
        if command == "validate_uuid":
            return _converter.validate_uuid(text)
        if command == "describe_uuid":
            return _converter.describe_uuid(text)
        return None

    def cleanup(self):
        self._widget = None
        super().cleanup()
