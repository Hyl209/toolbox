from __future__ import annotations


def build_aiimage_tab_class(deps: dict):
    QWidget = deps["QWidget"]
    QVBoxLayout = deps["QVBoxLayout"]
    QLabel = deps["QLabel"]
    QPushButton = deps["QPushButton"]
    Qt = deps["Qt"]
    make_card = deps["make_card"]
    show_themed_success = deps["show_themed_success"]

    class AiImagePlaceholderTab(QWidget):
        def __init__(self, settings):
            super().__init__()
            self.settings = settings
            layout = QVBoxLayout(self)
            layout.setContentsMargins(0, 0, 0, 0)
            layout.setSpacing(16)

            card, card_layout = make_card("AI 生图")

            title = QLabel("该工具仅在新 Tauri UI 可用")
            title.setAlignment(Qt.AlignCenter)
            title.setStyleSheet("font-size: 22px; font-weight: 700; background: transparent;")
            card_layout.addWidget(title)

            desc = QLabel("请从 `desktop-tauri` 新界面使用 AI 生图功能。旧版 GUI 只保留占位入口，用于兼容注册、打包和测试。")
            desc.setWordWrap(True)
            desc.setAlignment(Qt.AlignCenter)
            desc.setStyleSheet("font-size: 14px; background: transparent;")
            card_layout.addWidget(desc)

            button = QPushButton("知道了")
            button.clicked.connect(lambda: show_themed_success(self, "提示", "AI 生图请在新 Tauri UI 中使用。"))
            card_layout.addWidget(button, 0, Qt.AlignCenter)

            layout.addWidget(card)
            layout.addStretch(1)

        def apply_theme(self, theme_name: str):
            del theme_name

    return AiImagePlaceholderTab
