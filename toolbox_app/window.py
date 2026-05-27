"""Extracted ToolboxWindow — receives all dependencies via builder."""

from __future__ import annotations


def build_toolbox_window_class(deps: dict):
    """Return a ToolboxWindow class with all Qt/helper deps injected."""

    QMainWindow = deps['QMainWindow']
    QWidget = deps['QWidget']
    QVBoxLayout = deps['QVBoxLayout']
    QHBoxLayout = deps['QHBoxLayout']
    QFrame = deps['QFrame']
    QLabel = deps['QLabel']
    QPushButton = deps['QPushButton']
    QListWidget = deps['QListWidget']
    QStackedWidget = deps['QStackedWidget']
    QPixmap = deps['QPixmap']
    Qt = deps['Qt']
    QIcon = deps.get('QIcon')
    DragTitleBar = deps['DragTitleBar']
    load_setting = deps['load_setting']
    save_setting = deps['save_setting']
    get_theme_stylesheet = deps['get_theme_stylesheet']
    build_global_scrollbar_style = deps['build_global_scrollbar_style']
    build_help_popup_state = deps['build_help_popup_state']
    build_user_menu_state = deps['build_user_menu_state']
    style_combo_popup = deps['style_combo_popup']
    animate_stack_switch = deps['animate_stack_switch']
    LOGO_PATH = deps['LOGO_PATH']
    WEIXIN_IMAGE_PATH = deps['WEIXIN_IMAGE_PATH']
    MusicTab = deps['MusicTab']
    ZipAndPngTab = deps['ZipAndPngTab']
    Mp4ToMp3Tab = deps['Mp4ToMp3Tab']
    ImageConvertTab = deps['ImageConvertTab']
    PdfToolsTab = deps['PdfToolsTab']
    VideoDownloaderTab = deps['VideoDownloaderTab']
    BatchRenameTab = deps['BatchRenameTab']
    FileSorterTab = deps['FileSorterTab']
    SameTab = deps['SameTab']
    Base64Tab = deps['Base64Tab']

    class ToolboxWindow(QMainWindow):
        def __init__(self, settings, authenticated_username: str = ''):
            super().__init__()
            self.settings = settings
            self.authenticated_username = authenticated_username.strip() or load_setting(settings, 'auth/last_user', '')
            self.current_theme = load_setting(settings, 'ui/theme', 'dark')
            self._drag_offset = None
            self._normal_geometry = None
            self.relogin_requested = False
            self.setWindowFlags(self.windowFlags() | Qt.FramelessWindowHint)
            self.setWindowTitle('格式转换工具')
            self.resize(1180, 820)
            self.setStyleSheet(get_theme_stylesheet(self.current_theme))
            if LOGO_PATH.exists() and QIcon is not None:
                self.setWindowIcon(QIcon(str(LOGO_PATH)))
            root = QWidget()
            root.setObjectName('windowSurface')
            root.setProperty('windowSurface', True)
            root_layout = QVBoxLayout(root)
            root_layout.setContentsMargins(10, 10, 10, 10)
            root_layout.setSpacing(0)
            self.content_surface = QWidget()
            self.content_surface.setProperty('contentSurface', True)
            content_layout = QVBoxLayout(self.content_surface)
            content_layout.setContentsMargins(0, 0, 0, 0)
            content_layout.setSpacing(0)
            self.drag_bar = DragTitleBar(self)
            content_layout.addWidget(self.drag_bar)
            central = QWidget()
            central.setAttribute(Qt.WA_TranslucentBackground, True)
            shell = QHBoxLayout(central)
            shell.setContentsMargins(18, 20, 18, 20)
            shell.setSpacing(20)
            side_panel = QFrame()
            side_panel.setProperty('navPanel', True)
            side_layout = QVBoxLayout(side_panel)
            side_layout.setContentsMargins(18, 22, 18, 18)
            side_layout.setSpacing(14)
            brand = QLabel('  格式转换工具 · Clean local toolbox')
            brand.setProperty('brandTitle', True)
            sub = QLabel('    作者：HhhYl')
            sub.setProperty('brandSub', True)
            side_layout.addWidget(brand)
            side_layout.addWidget(sub)
            self.theme_button = QPushButton('☀️' if self.current_theme == 'dark' else '🌙')
            self.theme_button.setProperty('themeToggle', True)
            self.theme_button.setMinimumSize(44, 44)
            self.theme_button.setMaximumSize(44, 44)
            self.theme_button.clicked.connect(self.toggle_theme)
            self.sidebar = QListWidget()
            self.sidebar.setProperty('navList', True)
            self.sidebar.setFixedWidth(196)
            self.sidebar.setStyleSheet(build_global_scrollbar_style())
            self.sidebar.addItem('NCM 转 MP3')
            self.sidebar.addItem('图片伪装')
            self.sidebar.addItem('MP4 转 MP3')
            self.sidebar.addItem('图片格式互转')
            self.sidebar.addItem('PDF工具')
            self.sidebar.addItem('TG下载')
            self.sidebar.addItem('网页视频下载')
            self.sidebar.addItem('批量命名')
            self.sidebar.addItem('文件分类')
            self.sidebar.addItem('重复文件')
            self.sidebar.addItem('图片Base64')
            self.sidebar.setCurrentRow(0)
            side_layout.addWidget(self.sidebar, 1)
            bottom_row = QHBoxLayout()
            bottom_row.setContentsMargins(0, 0, 0, 0)
            bottom_row.setSpacing(10)
            self.user_avatar_button = QPushButton()
            self.user_avatar_button.setProperty('themeToggle', True)
            self.user_avatar_button.setMinimumSize(38, 38)
            self.user_avatar_button.setMaximumSize(38, 38)
            self.user_avatar_button.setCursor(Qt.PointingHandCursor)
            self.user_avatar_button.clicked.connect(self.toggle_user_menu)
            bottom_row.addWidget(self.user_avatar_button, 0, Qt.AlignLeft | Qt.AlignVCenter)
            bottom_row.addWidget(self.theme_button, 0, Qt.AlignLeft | Qt.AlignVCenter)
            self.hint_button = QPushButton('❕')
            self.hint_button.setProperty('themeToggle', True)
            self.hint_button.setMinimumSize(38, 38)
            self.hint_button.setMaximumSize(38, 38)
            self.hint_button.setCursor(Qt.PointingHandCursor)
            self.hint_button.clicked.connect(self.toggle_help_popup)
            bottom_row.addWidget(self.hint_button, 0, Qt.AlignLeft | Qt.AlignVCenter)
            bottom_row.addStretch(1)
            side_layout.addLayout(bottom_row)
            shell.addWidget(side_panel)
            self.stack = QStackedWidget()
            self.music_tab = MusicTab(settings)
            self.zip_tab = ZipAndPngTab(settings)
            self.mp4_tab = Mp4ToMp3Tab(settings)
            self.image_convert_tab = ImageConvertTab(settings)
            self.pdf_tools_tab = PdfToolsTab(settings)
            self.tg_downloader_tab = VideoDownloaderTab(settings, 'telegram')
            self.web_video_downloader_tab = VideoDownloaderTab(settings, 'web')
            self.video_downloader_tab = self.tg_downloader_tab
            self.batch_rename_tab = BatchRenameTab(settings)
            self.file_sorter_tab = FileSorterTab(settings)
            self.same_tab = SameTab(settings)
            self.base64_tab = Base64Tab(settings)
            self.stack.addWidget(self.music_tab)
            self.stack.addWidget(self.zip_tab)
            self.stack.addWidget(self.mp4_tab)
            self.stack.addWidget(self.image_convert_tab)
            self.stack.addWidget(self.pdf_tools_tab)
            self.stack.addWidget(self.tg_downloader_tab)
            self.stack.addWidget(self.web_video_downloader_tab)
            self.stack.addWidget(self.batch_rename_tab)
            self.stack.addWidget(self.file_sorter_tab)
            self.stack.addWidget(self.same_tab)
            self.stack.addWidget(self.base64_tab)
            shell.addWidget(self.stack, 1)
            self.sidebar.currentRowChanged.connect(self.switch_tool_page)
            content_layout.addWidget(central, 1)
            root_layout.addWidget(self.content_surface)
            self.setCentralWidget(root)
            self.central_surface = self.content_surface
            self._build_user_menu()
            self._build_help_popup()
            self.update_user_menu_ui()
            self.update_window_controls()

        def start_window_drag(self, global_pos):
            if self.isMaximized():
                return
            self._drag_offset = global_pos - self.frameGeometry().topLeft()

        def update_window_drag(self, global_pos):
            if self._drag_offset is None or self.isMaximized():
                return
            self.move(global_pos - self._drag_offset)

        def stop_window_drag(self):
            self._drag_offset = None

        def toggle_max_restore(self):
            if self.isMaximized():
                self.showNormal()
                if self._normal_geometry is not None:
                    self.setGeometry(self._normal_geometry)
            else:
                self._normal_geometry = self.geometry()
                self.showMaximized()
            self.update_window_controls()

        def update_window_controls(self):
            if not hasattr(self, 'max_button'):
                return
            is_max = self.isMaximized()
            self.max_button.control_type = 'restore' if is_max else 'max'
            self.max_button.setToolTip('还原' if is_max else '最大化')
            self.max_button.update()

        def _build_user_menu(self):
            self.user_menu = QFrame(self)
            self.user_menu.setVisible(False)
            self.user_menu.setFrameShape(QFrame.StyledPanel)
            self.user_menu.setStyleSheet('border-radius: 18px; padding: 0px;')
            layout = QVBoxLayout(self.user_menu)
            layout.setContentsMargins(20, 20, 20, 20)
            layout.setSpacing(14)
            self.user_menu_name_label = QLabel('')
            self.user_menu_name_label.setProperty('brandSub', True)
            layout.addWidget(self.user_menu_name_label)
            self.logout_button = QPushButton('退出账号')
            self.logout_button.setMinimumHeight(40)
            self.logout_button.clicked.connect(self.logout)
            layout.addWidget(self.logout_button)
            self.user_menu.resize(236, 148)

        def _build_help_popup(self):
            state = build_help_popup_state(WEIXIN_IMAGE_PATH)
            self.help_overlay = QFrame(self)
            self.help_overlay.setGeometry(self.rect())
            self.help_overlay.setStyleSheet('background-color: rgba(0, 0, 0, 110); border-radius: 24px;')
            self.help_overlay.setVisible(False)
            self.help_popup = QFrame(self)
            self.help_popup.setWindowFlags(Qt.SubWindow | Qt.FramelessWindowHint)
            self.help_popup.setProperty('contentSurface', True)
            self.help_popup.setAttribute(Qt.WA_StyledBackground, True)
            self.help_popup.setStyleSheet('border-radius: 18px; padding: 10px;')
            self.help_popup.setVisible(False)
            layout = QVBoxLayout(self.help_popup)
            layout.setContentsMargins(16, 16, 16, 16)
            layout.setSpacing(10)
            self.help_image_label = QLabel()
            self.help_image_label.setAlignment(Qt.AlignCenter)
            if state['has_image']:
                pixmap = QPixmap()
                pixmap.loadFromData(state['image_bytes'])
                scaled_pixmap = pixmap.scaled(
                    state['max_width'],
                    state['max_height'],
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation,
                )
                self.help_image_label.setPixmap(scaled_pixmap)
                self.help_image_label.setMinimumSize(scaled_pixmap.size())
            else:
                self.help_image_label.setText('未找到赞赏二维码图片')
                self.help_image_label.setProperty('cardSub', True)
                self.help_image_label.setMinimumSize(state['max_width'], 96)
            layout.addWidget(self.help_image_label)
            self.help_caption_label = QLabel(state['caption'])
            self.help_caption_label.setAlignment(Qt.AlignCenter)
            self.help_caption_label.setProperty('cardSub', True)
            self.help_caption_label.setStyleSheet(
                f'font-size: {state["caption_font_size"]}px; font-weight: {state["caption_font_weight"]};'
            )
            layout.addWidget(self.help_caption_label)
            self.help_popup.adjustSize()

        def update_user_menu_ui(self):
            state = build_user_menu_state(self.authenticated_username)
            self.user_avatar_button.setText(state['avatar_text'])
            self.user_avatar_button.setToolTip(state['username'])
            self.user_avatar_button.setProperty('themeToggle', state['avatar_uses_theme_toggle_style'])
            self.user_avatar_button.setMinimumSize(state['avatar_button_size'], state['avatar_button_size'])
            self.user_avatar_button.setMaximumSize(state['avatar_button_size'], state['avatar_button_size'])
            self.user_avatar_button.setStyleSheet(
                f'border-radius: {state["avatar_border_radius"]}px; font-weight: 700; padding: 0px;'
            )
            self.user_menu.layout().setContentsMargins(
                state['menu_padding'],
                state['menu_padding'],
                state['menu_padding'],
                state['menu_padding'],
            )
            self.user_menu.layout().setSpacing(state['menu_spacing'])
            self.user_menu.resize(state['menu_width'], state['menu_height'])
            self.user_menu_name_label.setText(f'当前用户：{state["username"]}')
            self.logout_button.setText(state['logout_text'])

        def toggle_user_menu(self):
            if self.user_menu.isVisible():
                self.user_menu.hide()
                return
            button_pos = self.user_avatar_button.mapTo(self, self.user_avatar_button.rect().topLeft())
            menu_x = button_pos.x() + self.user_avatar_button.width() - self.user_menu.width()
            menu_y = button_pos.y() - self.user_menu.height() - 8
            self.user_menu.move(max(12, menu_x), max(12, menu_y))
            self.user_menu.show()
            self.user_menu.raise_()

        def show_help_popup(self):
            self.help_overlay.setGeometry(self.rect())
            self.help_overlay.setVisible(True)
            self.help_overlay.raise_()
            self.help_popup.adjustSize()
            popup_x = max(12, (self.width() - self.help_popup.width()) // 2)
            popup_y = max(12, (self.height() - self.help_popup.height()) // 2)
            self.help_popup.move(popup_x, popup_y)
            self.help_popup.setVisible(True)
            self.help_popup.raise_()

        def hide_help_popup(self):
            self.help_popup.setVisible(False)
            self.help_overlay.setVisible(False)

        def toggle_help_popup(self):
            if self.help_popup.isVisible():
                self.hide_help_popup()
                return
            self.show_help_popup()

        def handle_global_mouse_press(self, global_pos):
            if not self.help_popup.isVisible():
                return
            local_pos = self.mapFromGlobal(global_pos)
            if self.rect().contains(local_pos):
                self.hide_help_popup()

        def mousePressEvent(self, event):
            if self.help_popup.isVisible() and event is not None:
                self.handle_global_mouse_press(event.globalPosition().toPoint() if hasattr(event, 'globalPosition') else event.globalPos())
                event.accept()
                return
            super().mousePressEvent(event)

        def resizeEvent(self, event):
            super().resizeEvent(event)
            if hasattr(self, 'help_overlay'):
                self.help_overlay.setGeometry(self.rect())

        def logout(self):
            self.relogin_requested = True
            save_setting(self.settings, 'auth/auto_login', '0')
            self.user_menu.hide()
            self.close()

        def switch_tool_page(self, index: int):
            animate_stack_switch(self.stack, index)

        def changeEvent(self, event):
            super().changeEvent(event)
            self.update_window_controls()

        def toggle_theme(self):
            self.current_theme = 'light' if self.current_theme == 'dark' else 'dark'
            save_setting(self.settings, 'ui/theme', self.current_theme)
            self.theme_button.setText('☀️' if self.current_theme == 'dark' else '🌙')
            style_combo_popup(self.image_convert_tab.jpg_background_combo, self.current_theme)
            style_combo_popup(self.base64_tab.mode_combo, self.current_theme)
            style_combo_popup(self.pdf_tools_tab.action_combo, self.current_theme)
            style_combo_popup(self.pdf_tools_tab.image_format_combo, self.current_theme)
            style_combo_popup(self.pdf_tools_tab.text_format_combo, self.current_theme)
            self.setStyleSheet(get_theme_stylesheet(self.current_theme))
            self.content_surface.setGraphicsEffect(None)
            if hasattr(self.file_sorter_tab, 'apply_theme'):
                self.file_sorter_tab.apply_theme(self.current_theme)
            if hasattr(self.tg_downloader_tab, 'apply_theme'):
                self.tg_downloader_tab.apply_theme(self.current_theme)
            if hasattr(self.web_video_downloader_tab, 'apply_theme'):
                self.web_video_downloader_tab.apply_theme(self.current_theme)
            self.update_window_controls()
            self.update_user_menu_ui()
            if hasattr(self, 'user_menu') and self.user_menu.isVisible():
                self.user_menu.hide()
            if hasattr(self, 'help_popup') and self.help_popup.isVisible():
                self.hide_help_popup()

    return ToolboxWindow
