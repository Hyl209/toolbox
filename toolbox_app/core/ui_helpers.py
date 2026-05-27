from __future__ import annotations

from typing import Optional
from .logger import get_logger

logger = get_logger(__name__)


class UIHelpers:
    """UI 辅助工具类"""

    @staticmethod
    def show_message_box(parent, title: str, message: str, msg_type: str = 'info'):
        """显示消息框"""
        try:
            from PySide6.QtWidgets import QMessageBox
            msg_box = QMessageBox(parent)
            msg_box.setWindowTitle(title)
            msg_box.setText(message)

            if msg_type == 'info':
                msg_box.setIcon(QMessageBox.Icon.Information)
            elif msg_type == 'warning':
                msg_box.setIcon(QMessageBox.Icon.Warning)
            elif msg_type == 'error':
                msg_box.setIcon(QMessageBox.Icon.Critical)
            elif msg_type == 'question':
                msg_box.setIcon(QMessageBox.Icon.Question)
                msg_box.setStandardButtons(
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )

            return msg_box.exec()
        except ImportError:
            logger.warning("PySide6 未安装，无法显示消息框")
            return None

    @staticmethod
    def show_confirmation(parent, title: str, message: str) -> bool:
        """显示确认对话框"""
        result = UIHelpers.show_message_box(parent, title, message, 'question')
        try:
            from PySide6.QtWidgets import QMessageBox
            return result == QMessageBox.StandardButton.Yes
        except ImportError:
            return False

    @staticmethod
    def show_file_dialog(parent, title: str, directory: str = '',
                         file_filter: str = '', save_mode: bool = False) -> Optional[str]:
        """显示文件选择对话框"""
        try:
            from PySide6.QtWidgets import QFileDialog
            if save_mode:
                file_path, _ = QFileDialog.getSaveFileName(
                    parent, title, directory, file_filter
                )
            else:
                file_path, _ = QFileDialog.getOpenFileName(
                    parent, title, directory, file_filter
                )
            return file_path if file_path else None
        except ImportError:
            logger.warning("PySide6 未安装，无法显示文件对话框")
            return None

    @staticmethod
    def show_directory_dialog(parent, title: str, directory: str = '') -> Optional[str]:
        """显示目录选择对话框"""
        try:
            from PySide6.QtWidgets import QFileDialog
            dir_path = QFileDialog.getExistingDirectory(parent, title, directory)
            return dir_path if dir_path else None
        except ImportError:
            logger.warning("PySide6 未安装，无法显示目录对话框")
            return None

    @staticmethod
    def create_progress_bar(parent, minimum: int = 0, maximum: int = 100):
        """创建进度条"""
        try:
            from PySide6.QtWidgets import QProgressBar
            progress_bar = QProgressBar(parent)
            progress_bar.setMinimum(minimum)
            progress_bar.setMaximum(maximum)
            return progress_bar
        except ImportError:
            logger.warning("PySide6 未安装，无法创建进度条")
            return None

    @staticmethod
    def create_button(parent, text: str, callback=None):
        """创建按钮"""
        try:
            from PySide6.QtWidgets import QPushButton
            button = QPushButton(text, parent)
            if callback:
                button.clicked.connect(callback)
            return button
        except ImportError:
            logger.warning("PySide6 未安装，无法创建按钮")
            return None

    @staticmethod
    def create_label(parent, text: str, alignment=None):
        """创建标签"""
        try:
            from PySide6.QtWidgets import QLabel
            from PySide6.QtCore import Qt
            label = QLabel(text, parent)
            if alignment:
                label.setAlignment(alignment)
            return label
        except ImportError:
            logger.warning("PySide6 未安装，无法创建标签")
            return None

    @staticmethod
    def create_line_edit(parent, placeholder: str = '', text: str = ''):
        """创建文本输入框"""
        try:
            from PySide6.QtWidgets import QLineEdit
            line_edit = QLineEdit(parent)
            if placeholder:
                line_edit.setPlaceholderText(placeholder)
            if text:
                line_edit.setText(text)
            return line_edit
        except ImportError:
            logger.warning("PySide6 未安装，无法创建文本输入框")
            return None

    @staticmethod
    def create_combo_box(parent, items: list[str] = None):
        """创建下拉框"""
        try:
            from PySide6.QtWidgets import QComboBox
            combo_box = QComboBox(parent)
            if items:
                combo_box.addItems(items)
            return combo_box
        except ImportError:
            logger.warning("PySide6 未安装，无法创建下拉框")
            return None

    @staticmethod
    def create_check_box(parent, text: str, checked: bool = False):
        """创建复选框"""
        try:
            from PySide6.QtWidgets import QCheckBox
            check_box = QCheckBox(text, parent)
            check_box.setChecked(checked)
            return check_box
        except ImportError:
            logger.warning("PySide6 未安装，无法创建复选框")
            return None

    @staticmethod
    def apply_stylesheet(widget, stylesheet: str):
        """应用样式表"""
        try:
            widget.setStyleSheet(stylesheet)
        except Exception as e:
            logger.error(f"应用样式表失败: {e}")

    @staticmethod
    def set_widget_enabled(widget, enabled: bool):
        """设置控件启用状态"""
        try:
            widget.setEnabled(enabled)
        except Exception as e:
            logger.error(f"设置控件状态失败: {e}")

    @staticmethod
    def set_widget_visible(widget, visible: bool):
        """设置控件可见状态"""
        try:
            widget.setVisible(visible)
        except Exception as e:
            logger.error(f"设置控件可见性失败: {e}")


# 全局 UI 辅助工具实例
ui_helpers = UIHelpers()
