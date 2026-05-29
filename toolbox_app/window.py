"""Extracted ToolboxWindow — receives all dependencies via builder."""

from __future__ import annotations

import logging
from toolbox_app.tool_registry import TOOL_DEFINITIONS

logger = logging.getLogger(__name__)


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
    SettingsDialog = deps['SettingsDialog']
    style_combo_popup = deps['style_combo_popup']
    animate_stack_switch = deps['animate_stack_switch']
    LOGO_PATH = deps['LOGO_PATH']
    WEIXIN_IMAGE_PATH = deps['WEIXIN_IMAGE_PATH']
    plugin_manager = deps.get('plugin_manager')
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

    # Tool id → tab class/instance mapping (order matches TOOL_DEFINITIONS)
    _TAB_BUILDERS = {
        'music': lambda s: MusicTab(s),
        'zipandpng': lambda s: ZipAndPngTab(s),
        'mp4mp3': lambda s: Mp4ToMp3Tab(s),
        'imageconvert': lambda s: ImageConvertTab(s),
        'pdftools': lambda s: PdfToolsTab(s),
        'tgdownloader': lambda s: VideoDownloaderTab(s, 'telegram'),
        'webvideodownloader': lambda s: VideoDownloaderTab(s, 'web'),
        'batchrename': lambda s: BatchRenameTab(s),
        'filesorter': lambda s: FileSorterTab(s),
        'same': lambda s: SameTab(s),
        'base64': lambda s: Base64Tab(s),
    }

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
            brand = QLabel('  格式转换工具')
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
            disabled_tools_str = load_setting(settings, 'tools/disabled', '')
            self._disabled_tools = set(disabled_tools_str.split(',')) if disabled_tools_str.strip() else set()
            self.sidebar = QListWidget()
            self.sidebar.setProperty('navList', True)
            self.sidebar.setFixedWidth(196)
            self.sidebar.setStyleSheet(build_global_scrollbar_style())
            self._sidebar_to_stack: list[int] = []
            for tool_def in TOOL_DEFINITIONS:
                if tool_def.id not in self._disabled_tools:
                    self._sidebar_to_stack.append(TOOL_DEFINITIONS.index(tool_def))
                    self.sidebar.addItem(tool_def.sidebar_label)
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
            self._tabs = {}
            for tool_def in TOOL_DEFINITIONS:
                builder = _TAB_BUILDERS[tool_def.id]
                tab = builder(settings)
                self._tabs[tool_def.id] = tab
                self.stack.addWidget(tab)
            # backward-compat aliases
            self.music_tab = self._tabs['music']
            self.zip_tab = self._tabs['zipandpng']
            self.mp4_tab = self._tabs['mp4mp3']
            self.image_convert_tab = self._tabs['imageconvert']
            self.pdf_tools_tab = self._tabs['pdftools']
            self.tg_downloader_tab = self._tabs['tgdownloader']
            self.web_video_downloader_tab = self._tabs['webvideodownloader']
            self.video_downloader_tab = self.tg_downloader_tab
            self.batch_rename_tab = self._tabs['batchrename']
            self.file_sorter_tab = self._tabs['filesorter']
            self.same_tab = self._tabs['same']
            self.base64_tab = self._tabs['base64']
            # --- 加载插件 ---
            self._plugin_tabs = []
            self._plugin_manager = plugin_manager
            if plugin_manager is not None:
                try:
                    # 从 settings 读取禁用列表
                    disabled_str = load_setting(settings, 'plugins/disabled', '')
                    disabled_names = set(disabled_str.split(',')) if disabled_str.strip() else set()
                    plugin_manager.load_all_plugins(disabled_names)
                    plugin_deps = {k: v for k, v in deps.items()}
                    plugin_deps['settings'] = settings
                    plugin_manager.initialize_all_plugins(plugin_deps)
                    for name, plugin in plugin_manager.get_enabled_plugins().items():
                        if plugin.plugin_info.plugin_type == 'gui':
                            tab_widget = plugin.get_tab_widget()
                            if tab_widget is not None:
                                label = plugin.get_sidebar_label()
                                stack_idx = self.stack.count()
                                self._sidebar_to_stack.append(stack_idx)
                                self.sidebar.addItem(label)
                                self.stack.addWidget(tab_widget)
                                self._tabs[f'plugin:{name}'] = tab_widget
                                self._plugin_tabs.append((name, tab_widget))
                    for name, plugin in plugin_manager.get_enabled_plugins().items():
                        try:
                            plugin.on_app_start()
                        except Exception:
                            logger.error(f"插件 on_app_start 异常: {name}", exc_info=True)
                except Exception:
                    logger.error("插件加载/初始化异常", exc_info=True)
            # --- 应用导航栏排序 ---
            self._apply_sidebar_order(settings)
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
            self.user_menu.setProperty('card', True)
            self.user_menu.setStyleSheet('QFrame { border-radius: 18px; }')
            layout = QVBoxLayout(self.user_menu)
            layout.setContentsMargins(20, 22, 20, 18)
            layout.setSpacing(0)
            # 头像圆圈
            avatar_row = QHBoxLayout()
            avatar_row.setAlignment(Qt.AlignCenter)
            self.user_menu_avatar = QLabel('')
            self.user_menu_avatar.setAlignment(Qt.AlignCenter)
            self.user_menu_avatar.setMinimumSize(56, 56)
            self.user_menu_avatar.setMaximumSize(56, 56)
            self.user_menu_avatar.setProperty('menuAvatar', True)
            avatar_row.addWidget(self.user_menu_avatar)
            layout.addLayout(avatar_row)
            layout.addSpacing(10)
            # 用户名
            self.user_menu_name_label = QLabel('')
            self.user_menu_name_label.setAlignment(Qt.AlignCenter)
            self.user_menu_name_label.setProperty('brandTitle', True)
            self.user_menu_name_label.setStyleSheet('font-size: 15px;')
            layout.addWidget(self.user_menu_name_label)
            layout.addSpacing(4)
            # 状态标签
            self.user_menu_status = QLabel('已登录')
            self.user_menu_status.setAlignment(Qt.AlignCenter)
            self.user_menu_status.setProperty('cardSub', True)
            layout.addWidget(self.user_menu_status)
            layout.addSpacing(14)
            # 分隔线
            sep = QFrame()
            sep.setFrameShape(QFrame.HLine)
            sep.setStyleSheet('background: rgba(128,128,128,0.18); max-height: 1px;')
            layout.addWidget(sep)
            layout.addSpacing(10)
            # 设置按钮
            self.settings_button = QPushButton('  ⚙  设置')
            self.settings_button.setMinimumHeight(38)
            self.settings_button.clicked.connect(self.open_settings)
            layout.addWidget(self.settings_button)
            layout.addSpacing(6)
            # 退出按钮
            self.logout_button = QPushButton('  ↗  退出账号')
            self.logout_button.setMinimumHeight(38)
            self.logout_button.clicked.connect(self.logout)
            self.logout_button.setStyleSheet(
                'QPushButton { color: #e07070; } '
                'QPushButton:hover { color: #f08080; }'
            )
            layout.addWidget(self.logout_button)
            self.user_menu.resize(240, 248)

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
            # 弹框内大头像
            avatar_size = state['menu_avatar_size']
            radius = avatar_size // 2
            self.user_menu_avatar.setText(state['avatar_text'])
            self.user_menu_avatar.setMinimumSize(avatar_size, avatar_size)
            self.user_menu_avatar.setMaximumSize(avatar_size, avatar_size)
            self.user_menu_avatar.setStyleSheet(
                f'QLabel[menuAvatar="true"] {{ border-radius: {radius}px; font-size: 22px; font-weight: 700; }}'
            )
            self.user_menu.resize(state['menu_width'], state['menu_height'])
            self.user_menu_name_label.setText(state['username'])
            is_logged_in = state['username'] != '未登录'
            self.user_menu_status.setText('已登录' if is_logged_in else '未登录')
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

        def closeEvent(self, event):
            """Clean up tabs (threads, timers) before window closes."""
            # 清理插件
            if hasattr(self, '_plugin_manager') and self._plugin_manager is not None:
                try:
                    # 合并：启动时未加载的禁用插件（不在 registry 中）+ 运行时禁用的
                    orig_disabled_str = load_setting(self.settings, 'plugins/disabled', '')
                    orig_disabled = set(orig_disabled_str.split(',')) if orig_disabled_str.strip() else set()
                    disabled = self._plugin_manager.get_disabled_plugin_names() | orig_disabled
                    save_setting(self.settings, 'plugins/disabled', ','.join(sorted(disabled)))
                    for name, plugin in self._plugin_manager.get_enabled_plugins().items():
                        try:
                            plugin.on_app_close()
                        except Exception:
                            logger.error(f"插件 on_app_close 异常: {name}", exc_info=True)
                    self._plugin_manager.cleanup_all_plugins()
                except Exception:
                    logger.error("插件清理异常", exc_info=True)
            # 清理内置 Tab 线程
            for tab in self._tabs.values():
                for attr in ('cleanup_worker', 'cleanup_scan_worker',
                             'cleanup_thumbnail_worker', 'cleanup_detection_worker'):
                    cleanup = getattr(tab, attr, None)
                    if cleanup:
                        try:
                            cleanup()
                        except Exception:
                            pass
            super().closeEvent(event)

        def open_settings(self):
            self.user_menu.hide()
            dialog = SettingsDialog(self.settings, self._plugin_manager, self)
            if dialog.exec() == SettingsDialog.Accepted:
                self._apply_sidebar_order(self.settings)

        def _apply_sidebar_order(self, settings):
            saved_order = load_setting(settings, 'sidebar/order', '')
            if not saved_order.strip():
                return
            order_ids = [s.strip() for s in saved_order.split(',') if s.strip()]
            if not order_ids:
                return
            # 当前 sidebar 中的 id 列表（按 sidebar 顺序）
            sidebar_ids = []
            for i in range(self.sidebar.count()):
                # 通过 _sidebar_to_stack 找到 stack index，再通过 stack widget 找到 tab id
                stack_idx = self._sidebar_to_stack[i]
                widget = self.stack.widget(stack_idx)
                for tid, tab in self._tabs.items():
                    if tab is widget:
                        sidebar_ids.append(tid)
                        break
            # 按保存的顺序重排（只排当前 sidebar 中的项）
            ordered_set = set()
            new_ids = []
            for tid in order_ids:
                if tid in sidebar_ids and tid not in ordered_set:
                    new_ids.append(tid)
                    ordered_set.add(tid)
            for tid in sidebar_ids:
                if tid not in ordered_set:
                    new_ids.append(tid)
            # 保存文本和 widget
            sidebar_texts = {tid: self.sidebar.item(i).text() for i, tid in enumerate(sidebar_ids)}
            self.sidebar.blockSignals(True)
            self.sidebar.clear()
            self._sidebar_to_stack = []
            for tid in new_ids:
                self._sidebar_to_stack.append(self._get_stack_index(tid))
                self.sidebar.addItem(sidebar_texts[tid])
            self.sidebar.blockSignals(False)
            if self._sidebar_to_stack:
                self.sidebar.setCurrentRow(0)
                self.stack.setCurrentIndex(self._sidebar_to_stack[0])

        def _get_stack_index(self, tab_id: str) -> int:
            widget = self._tabs.get(tab_id)
            if widget is None:
                return 0
            for i in range(self.stack.count()):
                if self.stack.widget(i) is widget:
                    return i
            return 0

        def logout(self):
            self.relogin_requested = True
            save_setting(self.settings, 'auth/auto_login', '0')
            self.user_menu.hide()
            self.close()

        def switch_tool_page(self, index: int):
            if 0 <= index < len(self._sidebar_to_stack):
                animate_stack_switch(self.stack, self._sidebar_to_stack[index])
            else:
                animate_stack_switch(self.stack, index)

        def changeEvent(self, event):
            super().changeEvent(event)
            self.update_window_controls()

        def toggle_theme(self):
            self.current_theme = 'light' if self.current_theme == 'dark' else 'dark'
            save_setting(self.settings, 'ui/theme', self.current_theme)
            self.theme_button.setText('☀️' if self.current_theme == 'dark' else '🌙')
            # Generic: iterate all tabs, call apply_theme if available
            for i in range(self.stack.count()):
                page = self.stack.widget(i)
                if hasattr(page, 'apply_theme'):
                    page.apply_theme(self.current_theme)
            self.setStyleSheet(get_theme_stylesheet(self.current_theme))
            self.content_surface.setGraphicsEffect(None)
            self.update_window_controls()
            self.update_user_menu_ui()
            # 通知插件主题变更
            if hasattr(self, '_plugin_manager') and self._plugin_manager is not None:
                for name, plugin in self._plugin_manager.get_enabled_plugins().items():
                    try:
                        plugin.on_theme_change(self.current_theme)
                    except Exception:
                        logger.error(f"插件 on_theme_change 异常: {name}", exc_info=True)
            if hasattr(self, 'user_menu') and self.user_menu.isVisible():
                self.user_menu.hide()
            if hasattr(self, 'help_popup') and self.help_popup.isVisible():
                self.hide_help_popup()

    return ToolboxWindow
