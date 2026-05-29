from __future__ import annotations

import importlib.util
import threading
from collections import deque
from pathlib import Path

from toolbox_app.plugins.base import PluginBase, PluginInfo


def _load_converter():  # -> types.ModuleType
    converter_path = Path(__file__).with_name("converter.py")
    spec = importlib.util.spec_from_file_location("archive_extractor_converter", converter_path)
    if spec is None or spec.loader is None:
        raise RuntimeError("无法加载解压插件 converter.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_converter = _load_converter()


def _get_qtimer(deps: dict):  # -> type[QTimer] | None
    qtimer = deps.get("QTimer")
    if qtimer is not None:
        return qtimer
    try:
        from PySide6.QtCore import QTimer
    except Exception:
        return None
    return QTimer


class ArchiveExtractorPlugin(PluginBase):
    def __init__(self):
        super().__init__()
        self._deps: dict = {}
        self._widget = None
        self._detect_generation: int = 0
        self._detect_lock = threading.Lock()
        self._detect_result: tuple[int, str, str, str] | None = None
        self._extracting: bool = False
        self._abort: threading.Event | None = None
        self._extract_logs: deque[str] = deque()
        self._extract_result: tuple[int, str, str] | None = None
        self._extract_lock = threading.Lock()

    def get_plugin_info(self) -> PluginInfo:
        return PluginInfo(
            name="archive_extractor",
            version="1.0.0",
            description="解压 ZIP / TAR / 7z 压缩包的 GUI 插件",
            author="HylToolbox",
            plugin_type="gui",
        )

    def initialize(self, deps: dict = None) -> bool:
        self._deps = deps or {}
        return True

    def get_sidebar_label(self) -> str:
        return "解压"

    def get_tab_widget(self):
        if self._widget is not None:
            return self._widget

        QWidget = self._deps.get("QWidget")
        QVBoxLayout = self._deps.get("QVBoxLayout")
        QHBoxLayout = self._deps.get("QHBoxLayout")
        QFrame = self._deps.get("QFrame")
        QLabel = self._deps.get("QLabel")
        QLineEdit = self._deps.get("QLineEdit")
        QPushButton = self._deps.get("QPushButton")
        QPlainTextEdit = self._deps.get("QPlainTextEdit")
        QProgressBar = self._deps.get("QProgressBar")
        QFileDialog = self._deps.get("QFileDialog")
        QTimer = _get_qtimer(self._deps)
        DropZoneCard = self._deps.get("DropZoneCard")
        make_card = self._deps.get("make_card")
        load_setting = self._deps.get("load_setting", lambda _settings, _key, default="": default)
        build_global_scrollbar_style = self._deps.get("build_global_scrollbar_style", lambda: "")
        Qt = self._deps.get("Qt")
        if not all((QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QPlainTextEdit)):
            return None

        widget = QWidget()
        root = QVBoxLayout(widget)
        root.setContentsMargins(0, 0, 0, 0)
        self.archive_path: str = ""
        self.settings = self._deps.get("settings")

        self._detect_timer = QTimer(widget) if QTimer else None
        if self._detect_timer is not None:
            self._detect_timer.setSingleShot(True)
            self._detect_timer.setInterval(80)
            self._detect_timer.timeout.connect(self._finish_pending_detection)

        self._extract_timer = QTimer(widget) if QTimer else None
        if self._extract_timer is not None:
            self._extract_timer.setInterval(80)
            self._extract_timer.timeout.connect(self._finish_pending_extraction)

        if make_card:
            card, layout = make_card("压缩包解压", "拖入任意文件，自动检测 ZIP / TAR / 7z 压缩包")
        else:
            card = QWidget()
            layout = QVBoxLayout(card)
            layout.addWidget(QLabel("压缩包解压"))

        if DropZoneCard:
            self.archive_drop = DropZoneCard("拖入压缩包文件\n\nZIP / TAR / 伪装后缀均可", self._handle_archive_drop)
        else:
            DropBase = QFrame or QWidget

            class DropArea(DropBase):
                def __init__(self, owner: ArchiveExtractorPlugin):
                    super().__init__()
                    self._owner = owner
                    self.setAcceptDrops(True)
                    self.setMinimumHeight(190)
                    self.label = QLabel("拖入压缩包文件\n\nZIP / TAR / 伪装后缀均可")
                    if Qt is not None:
                        self.label.setAlignment(Qt.AlignCenter)
                    drop_layout = QVBoxLayout(self)
                    drop_layout.addWidget(self.label)

                def set_body_text(self, text: str):
                    self.label.setText(text)

                def set_preview_file_icon(self, _path: str, header_text: str = "", body_text: str = ""):
                    self.label.setText("\n\n".join(part for part in (header_text, body_text) if part))

                def dragEnterEvent(self, event):
                    if event.mimeData().hasUrls():
                        event.acceptProposedAction()

                def dropEvent(self, event):
                    self._owner._handle_archive_drop([url.toLocalFile() for url in event.mimeData().urls()])
                    event.acceptProposedAction()

            self.archive_drop = DropArea(self)
        layout.addWidget(self.archive_drop)

        self.status_label = QLabel("等待选择压缩包")
        self.status_label.setProperty("cardSub", True)
        layout.addWidget(self.status_label)

        layout.addWidget(QLabel("输出目录"))
        self.output_edit = QLineEdit()
        if self.settings is not None:
            self.output_edit.setText(load_setting(self.settings, "archive_extractor/output_dir", ""))
        self.output_edit.setPlaceholderText("默认使用压缩包同目录下的 文件名_解压")
        output_btn = QPushButton("选择路径")
        output_btn.clicked.connect(self._choose_output)
        output_row = QHBoxLayout()
        output_row.addWidget(self.output_edit, 1)
        output_row.addWidget(output_btn)
        layout.addLayout(output_row)

        layout.addWidget(QLabel("解压密码"))
        self.password_edit = QLineEdit()
        self.password_edit.setPlaceholderText("无密码可留空，支持 ZIP / 7z 加密压缩包")
        layout.addWidget(self.password_edit)

        action_row = QHBoxLayout()
        archive_btn = QPushButton("选择文件")
        archive_btn.clicked.connect(self._choose_archive)
        action_row.addWidget(archive_btn)
        action_row.addStretch(1)
        self.clear_button = QPushButton("清空文件")
        self.clear_button.clicked.connect(self._clear_form)
        self.clear_button.setEnabled(False)
        action_row.addWidget(self.clear_button)
        self.cancel_button = QPushButton("取消解压")
        self.cancel_button.clicked.connect(self._cancel_extraction)
        self.cancel_button.setEnabled(False)
        self.cancel_button.setVisible(False)
        action_row.addWidget(self.cancel_button)
        self.run_button = QPushButton("开始解压")
        self.run_button.clicked.connect(self._extract)
        self.run_button.setEnabled(False)
        action_row.addWidget(self.run_button)
        layout.addLayout(action_row)

        self.progress = QProgressBar() if QProgressBar else None
        if self.progress is not None:
            self.progress.setRange(0, 100)
            self.progress.setValue(0)
            layout.addWidget(self.progress)

        self.log = QPlainTextEdit()
        self.log.setReadOnly(True)
        self.log.setMinimumHeight(140)
        self.log.setStyleSheet(build_global_scrollbar_style())
        layout.addWidget(self.log, 1)
        root.addWidget(card)
        self._widget = widget
        return widget

    def _choose_archive(self):
        QFileDialog = self._deps.get("QFileDialog")
        if QFileDialog is None:
            return
        path, _ = QFileDialog.getOpenFileName(
            self._widget,
            "选择压缩包",
            "",
            "All Files (*)",
        )
        if path:
            self._use_archive_file(path)

    def _choose_output(self):
        QFileDialog = self._deps.get("QFileDialog")
        if QFileDialog is None:
            return
        path = QFileDialog.getExistingDirectory(self._widget, "选择解压输出目录", "")
        if path:
            self.output_edit.setText(path)
            save_setting = self._deps.get("save_setting")
            if save_setting and self.settings is not None:
                save_setting(self.settings, "archive_extractor/output_dir", path)

    def _extract(self):
        if self._extracting:
            return
        archive = self.archive_path
        output = self.output_edit.text().strip()
        if not archive:
            self._show_message("提示", "请先拖入或选择压缩包", error=True)
            return
        if not output:
            source = Path(archive)
            output = str(source.with_name(f"{source.name}_解压"))
            self.output_edit.setText(output)
        self._start_extraction(archive, output)

    def _start_extraction(self, archive: str, output: str):
        self._extracting = True
        self._abort = threading.Event()
        self._extract_logs.clear()
        with self._extract_lock:
            self._extract_result = None
        if self.progress is not None:
            self.progress.setValue(0)
        self._set_status("正在解压...")
        self._set_extract_ui(True)
        self.log.appendPlainText(f"开始解压：{archive} -> {output}")

        if self._extract_timer is None:
            # No QTimer: run synchronously (fallback)
            try:
                count = _converter.extract_archive_sync(
                    archive, output, self.password_edit.text()
                )
            except Exception as exc:
                self.log.appendPlainText(f"解压失败：{exc}")
                self._set_status("解压失败")
                self._show_message("解压失败", str(exc), error=True)
            else:
                self._finish_extraction_success(count, output)
            finally:
                self._extracting = False
                self._set_extract_ui(False)
            return

        password = self.password_edit.text()
        self._extract_timer.start()

        def worker():
            count = 0
            error = ""
            try:
                count = _converter.extract_archive(
                    archive,
                    output,
                    password,
                    self._abort,
                    self._extract_logs.append,
                )
            except Exception as exc:
                error = str(exc)
            with self._extract_lock:
                self._extract_result = (count, error, output)

        threading.Thread(target=worker, daemon=True).start()

    def _finish_pending_extraction(self):
        # Drain log lines
        while self._extract_logs:
            self.log.appendPlainText(self._extract_logs.popleft())

        with self._extract_lock:
            result = self._extract_result
        if result is None:
            return

        self._extract_timer.stop()
        self._extracting = False
        self._set_extract_ui(False)

        # Drain any remaining logs
        while self._extract_logs:
            self.log.appendPlainText(self._extract_logs.popleft())

        count, error, output = result
        if error:
            self.log.appendPlainText(f"解压失败：{error}")
            self._set_status("解压失败")
            self._show_message("解压失败", error, error=True)
            return
        self._finish_extraction_success(count, output)

    def _finish_extraction_success(self, count: int, output: str):
        if self.progress is not None:
            self.progress.setValue(100)
        self.log.appendPlainText(f"解压完成：{count} 个条目 -> {output}")
        save_setting = self._deps.get("save_setting")
        if save_setting and self.settings is not None:
            save_setting(self.settings, "archive_extractor/output_dir", output)
        self._set_status(f"解压完成：{count} 个条目")
        self._show_message("解压完成", f"已解压 {count} 个条目")

    def _cancel_extraction(self):
        if self._abort is not None:
            self._abort.set()
        self.log.appendPlainText("正在取消解压...")

    def _set_extract_ui(self, extracting: bool):
        """Toggle UI elements during extraction."""
        self.run_button.setEnabled(not extracting)
        self.clear_button.setEnabled(not extracting)
        self.cancel_button.setEnabled(extracting)
        self.cancel_button.setVisible(extracting)

    def _handle_archive_drop(self, paths: list[str]):
        if paths:
            self._use_archive_file(paths[0])

    def _use_archive_file(self, path: str):
        self._start_archive_detection(path)

    def _start_archive_detection(self, path: str):
        self._detect_generation += 1
        generation = self._detect_generation
        self.archive_path = ""
        self._set_ready(False)
        self.clear_button.setEnabled(True)
        self._set_status("正在识别压缩包...")
        self.archive_drop.set_preview_file_icon(path, header_text="正在识别压缩包", body_text=Path(path).name)
        self.log.appendPlainText(f"正在识别：{path}")

        if self._detect_timer is None:
            self._apply_detected_archive(path, _converter.detect_archive_type(path))
            return

        with self._detect_lock:
            self._detect_result = None
        self._detect_timer.start()

        def worker():
            try:
                archive_type = _converter.detect_archive_type(path)
                error = ""
            except Exception as exc:
                archive_type = ""
                error = str(exc)
            with self._detect_lock:
                self._detect_result = (generation, path, archive_type, error)

        threading.Thread(target=worker, daemon=True).start()

    def _finish_pending_detection(self):
        with self._detect_lock:
            result = self._detect_result
            self._detect_result = None
        if result is None:
            self._detect_timer.start()  # single-shot: restart if still waiting
            return
        generation, path, archive_type, error = result
        if generation != self._detect_generation:
            return
        if error:
            self.log.appendPlainText(f"识别失败：{error}")
        self._apply_detected_archive(path, archive_type)

    def _apply_detected_archive(self, path: str, archive_type: str):
        if not archive_type:
            self.log.appendPlainText(f"不是可识别压缩包：{path}")
            self.archive_path = ""
            self.archive_drop.set_body_text("拖入压缩包文件\n\nZIP / TAR / 伪装后缀均可")
            self._set_ready(False)
            self._set_status("未识别为压缩包")
            return
        self.archive_path = path
        if not self.output_edit.text().strip():
            source = Path(path)
            self.output_edit.setText(str(source.with_name(f"{source.name}_解压")))
        self.archive_drop.set_preview_file_icon(
            path,
            header_text=f"已识别 {archive_type.upper()} 压缩包",
            body_text=Path(path).name,
        )
        self._set_ready(True)
        self._set_status(f"已选择 {archive_type.upper()} 压缩包")
        self.log.appendPlainText(f"已识别 {archive_type.upper()} 压缩包：{path}")

    def _clear_form(self):
        had_file = bool(self.archive_path)
        self._detect_generation += 1
        with self._detect_lock:
            self._detect_result = None
        if self._abort is not None:
            self._abort.set()
        if hasattr(self, "_detect_timer") and self._detect_timer is not None:
            self._detect_timer.stop()
        self.archive_path = ""
        self.archive_drop.set_body_text("拖入压缩包文件\n\nZIP / TAR / 伪装后缀均可")
        if self.progress is not None:
            self.progress.setValue(0)
        self._set_ready(False)
        self._set_status("等待选择压缩包")
        if had_file:
            self.log.appendPlainText("已清空压缩包")
        if hasattr(self, "password_edit"):
            self.password_edit.clear()

    def _set_ready(self, ready: bool):
        self.run_button.setEnabled(ready)
        self.clear_button.setEnabled(ready)

    def _set_status(self, text: str):
        if hasattr(self, "status_label"):
            self.status_label.setText(text)

    def _show_message(self, title: str, text: str, error: bool = False):
        if error:
            themed = self._deps.get("show_themed_error") or self._deps.get("show_themed_warning")
            if themed:
                themed(self._widget, title, text)
                return
        else:
            themed = self._deps.get("show_themed_success")
            if themed:
                themed(self._widget, title, [text])
                return
        QMessageBox = self._deps.get("QMessageBox")
        if QMessageBox is None:
            return
        if error:
            QMessageBox.warning(self._widget, title, text)
        else:
            QMessageBox.information(self._widget, title, text)

    def handle_command(self, command: str, **kwargs):
        if command == "extract_archive":
            return _converter.extract_archive_sync(
                kwargs.get("archive_path", ""),
                kwargs.get("output_dir", ""),
                kwargs.get("password", ""),
            )
        if command == "detect_archive_type":
            return _converter.detect_archive_type(kwargs.get("archive_path", ""))
        return None

    def cleanup(self):
        self._detect_generation += 1
        if self._abort is not None:
            self._abort.set()
        if hasattr(self, "_detect_timer") and self._detect_timer is not None:
            self._detect_timer.stop()
        if hasattr(self, "_extract_timer") and self._extract_timer is not None:
            self._extract_timer.stop()
        self._widget = None
        super().cleanup()
