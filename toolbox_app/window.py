"""Extracted ToolboxWindow — receives all dependencies via builder."""

from __future__ import annotations

import logging
from toolbox_app.tool_registry import TOOL_BY_ID, TOOL_DEFINITIONS

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
    QEvent = deps.get('QEvent')
    if QEvent is None:
        from PySide6.QtCore import QEvent
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
    builtin_tab_factories = deps['builtin_tab_factories']

    import os as _os, importlib.util as _ilu
    _cs_path = _os.path.join(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))), 'modules', 'theme-customizer', 'color_scheme.py')
    _cs_spec = _ilu.spec_from_file_location('color_scheme', _cs_path)
    _cs_mod = _ilu.module_from_spec(_cs_spec)
    _cs_spec.loader.exec_module(_cs_mod)
    generate_qss = _cs_mod.generate_qss
    load_custom_colors = _cs_mod.load_custom_colors
    get_default_colors = _cs_mod.get_default_colors
    # Tool id -> lazy tab factory mapping (order matches TOOL_DEFINITIONS)
    def _build_registered_tab(tool_id: str, settings):
        tab_factory = builtin_tab_factories[tool_id]
        tab_kwargs = TOOL_BY_ID[tool_id].tab_kwargs
        return tab_factory(settings, **tab_kwargs)

    _TAB_BUILDERS = {
        tool_def.id: lambda settings, tool_id=tool_def.id: _build_registered_tab(tool_id, settings)
        for tool_def in TOOL_DEFINITIONS
        if tool_def.id in builtin_tab_factories
    }

    class ToolboxWindow(QMainWindow):
        def __init__(self, settings, authenticated_username: str = ''):
            super().__init__()
            self.settings = settings
            self.authenticated_username = authenticated_username.strip() or load_setting(settings, 'auth/last_user', '')
            self.current_theme = load_setting(settings, 'ui/theme', 'dark')
            self.custom_theme_enabled = load_setting(settings, 'ui/custom_theme_enabled', '0') == '1'
            self._drag_offset = None
            self._normal_geometry = None
            self._resize_margin = 8
            self._resize_edge = None
            self._resize_start_global_pos = None
            self._resize_start_geometry = None
            self._resize_handles = {}
            self.relogin_requested = False
            self.setWindowFlags(self.windowFlags() | Qt.FramelessWindowHint)
            self.setWindowTitle('格式转换工具')
            self.resize(1180, 820)
            self.setMinimumSize(860, 560)
            self.setStyleSheet(get_theme_stylesheet(self.current_theme))
            self._apply_custom_theme_colors()
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
            self.theme_button = QPushButton()
            self.theme_button.setProperty('themeToggle', True)
            self.theme_button.setMinimumSize(44, 44)
            self.theme_button.setMaximumSize(44, 44)
            self._update_theme_button_state()
            self.theme_button.clicked.connect(self.toggle_theme)
            disabled_tools_str = load_setting(settings, 'tools/disabled', '')
            self._disabled_tools = set(disabled_tools_str.split(',')) if disabled_tools_str.strip() else set()
            self.sidebar = QListWidget()
            self.sidebar.setProperty('navList', True)
            self.sidebar.setFixedWidth(196)
            self.sidebar.setStyleSheet(build_global_scrollbar_style())
            self._sidebar_to_stack: list[int] = []
            self._stack_to_tool_id: dict[int, str] = {}
            sidebar_labels = []
            for stack_index, tool_def in enumerate(TOOL_DEFINITIONS):
                if tool_def.id not in self._disabled_tools:
                    self._sidebar_to_stack.append(stack_index)
                    self._stack_to_tool_id[stack_index] = tool_def.id
                    sidebar_labels.append(tool_def.sidebar_label)
            self.sidebar.addItems(sidebar_labels)
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
            self.hint_button.setToolTip('赞赏')
            self.hint_button.clicked.connect(self.toggle_help_popup)
            bottom_row.addWidget(self.hint_button, 0, Qt.AlignLeft | Qt.AlignVCenter)
            bottom_row.addStretch(1)
            side_layout.addLayout(bottom_row)
            shell.addWidget(side_panel)
            self.stack = QStackedWidget()
            stack_policy = self.stack.sizePolicy()
            stack_policy.setVerticalPolicy(stack_policy.Policy.Ignored)
            self.stack.setSizePolicy(stack_policy)
            self._tabs = {}
            self._tab_builders = dict(_TAB_BUILDERS)
            self._tab_settings = settings
            # Create placeholder widgets; real tabs built on first selection
            for tool_def in TOOL_DEFINITIONS:
                builder = self._tab_builders.get(tool_def.id)
                if builder is None:
                    logger.warning("跳过未知工具 id: %s", tool_def.id)
                    continue
                placeholder = QWidget()
                self._tabs[tool_def.id] = placeholder
                self.stack.addWidget(placeholder)
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
                            label = plugin.get_sidebar_label()
                            plugin_tool_id = f'plugin:{name}'
                            placeholder = QWidget()
                            stack_idx = self.stack.count()
                            self._stack_to_tool_id[stack_idx] = plugin_tool_id
                            self._sidebar_to_stack.append(stack_idx)
                            self.sidebar.addItem(label)
                            self.stack.addWidget(placeholder)
                            self._tabs[plugin_tool_id] = placeholder
                            self._tab_builders[plugin_tool_id] = (
                                lambda _settings, plugin=plugin, name=name: self._build_plugin_tab(name, plugin)
                            )
                    for name, plugin in plugin_manager.get_enabled_plugins().items():
                        try:
                            plugin.on_app_start()
                        except Exception:
                            logger.error("插件 on_app_start 异常: %s", name, exc_info=True)
                except Exception:
                    logger.error("插件加载/初始化异常", exc_info=True)
            # --- 应用导航栏排序 ---
            self._apply_sidebar_order(settings)
            # Eagerly create the first visible tab AFTER sidebar order is applied
            if self._sidebar_to_stack:
                first_stack_idx = self._sidebar_to_stack[0]
                first_tool_id = self._stack_to_tool_id.get(first_stack_idx)
                if first_tool_id:
                    self._ensure_tab_created(first_tool_id)
                self.stack.setCurrentIndex(first_stack_idx)
            shell.addWidget(self.stack, 1)
            self.sidebar.currentRowChanged.connect(self.switch_tool_page)
            content_layout.addWidget(central, 1)
            root_layout.addWidget(self.content_surface)
            self.setCentralWidget(root)
            self._build_resize_handles()
            self.central_surface = self.content_surface
            self._build_user_menu()
            self._build_help_popup()
            self.update_user_menu_ui()
            self.update_window_controls()

        def _build_resize_handles(self):
            cursors = {
                'left': Qt.SizeHorCursor,
                'right': Qt.SizeHorCursor,
                'top': Qt.SizeVerCursor,
                'bottom': Qt.SizeVerCursor,
                'top_left': Qt.SizeFDiagCursor,
                'bottom_right': Qt.SizeFDiagCursor,
                'top_right': Qt.SizeBDiagCursor,
                'bottom_left': Qt.SizeBDiagCursor,
            }
            for edge, cursor in cursors.items():
                handle = QWidget(self)
                handle.setObjectName(f'resizeHandle_{edge}')
                handle.setProperty('resizeHandle', True)
                handle.setMouseTracking(True)
                handle.setCursor(cursor)
                handle.setStyleSheet('background: transparent;')
                handle.installEventFilter(self)
                self._resize_handles[edge] = handle
            self._position_resize_handles()

        def _position_resize_handles(self):
            if not self._resize_handles:
                return
            margin = self._resize_margin
            width = self.width()
            height = self.height()
            middle_width = max(0, width - margin * 2)
            middle_height = max(0, height - margin * 2)
            geometries = {
                'top_left': (0, 0, margin, margin),
                'top_right': (max(0, width - margin), 0, margin, margin),
                'bottom_left': (0, max(0, height - margin), margin, margin),
                'bottom_right': (max(0, width - margin), max(0, height - margin), margin, margin),
                'left': (0, margin, margin, middle_height),
                'right': (max(0, width - margin), margin, margin, middle_height),
                'top': (margin, 0, middle_width, margin),
                'bottom': (margin, max(0, height - margin), middle_width, margin),
            }
            visible = not self.isMaximized()
            for edge, geometry in geometries.items():
                handle = self._resize_handles[edge]
                handle.setGeometry(*geometry)
                handle.setVisible(visible)
                handle.raise_()

        def _event_global_pos(self, event):
            if hasattr(event, 'globalPosition'):
                return event.globalPosition().toPoint()
            return event.globalPos()

        def eventFilter(self, obj, event):
            if obj in self._resize_handles.values():
                event_type = event.type()
                if event_type == QEvent.MouseButtonPress and event.button() == Qt.LeftButton:
                    if self.isMaximized():
                        return False
                    edge = next((key for key, handle in self._resize_handles.items() if handle is obj), None)
                    if edge is None:
                        return False
                    self._start_window_resize(edge, self._event_global_pos(event))
                    event.accept()
                    return True
                if event_type == QEvent.MouseMove and self._resize_edge is not None:
                    self._resize_window_to_global_pos(self._resize_edge, self._event_global_pos(event))
                    event.accept()
                    return True
                if event_type == QEvent.MouseButtonRelease and self._resize_edge is not None:
                    self._stop_window_resize()
                    event.accept()
                    return True
            return super().eventFilter(obj, event)

        def _start_window_resize(self, edge, global_pos):
            self._resize_edge = edge
            self._resize_start_global_pos = global_pos
            self._resize_start_geometry = self.geometry()

        def _stop_window_resize(self):
            self._resize_edge = None
            self._resize_start_global_pos = None
            self._resize_start_geometry = None
            if not self.isMaximized():
                self._normal_geometry = self.geometry()

        def _resize_window_to_global_pos(self, edge, global_pos):
            start_pos = self._resize_start_global_pos
            start_geometry = self._resize_start_geometry
            if start_pos is None or start_geometry is None or self.isMaximized():
                return
            delta = global_pos - start_pos
            left = start_geometry.left()
            top = start_geometry.top()
            width = start_geometry.width()
            height = start_geometry.height()
            min_width = self.minimumWidth()
            min_height = self.minimumHeight()
            max_width = self.maximumWidth()
            max_height = self.maximumHeight()

            if 'left' in edge:
                new_width = max(min_width, min(max_width, width - delta.x()))
                left = start_geometry.right() - new_width + 1
                width = new_width
            elif 'right' in edge:
                width = max(min_width, min(max_width, width + delta.x()))

            if 'top' in edge:
                new_height = max(min_height, min(max_height, height - delta.y()))
                top = start_geometry.bottom() - new_height + 1
                height = new_height
            elif 'bottom' in edge:
                height = max(min_height, min(max_height, height + delta.y()))

            self.setGeometry(left, top, width, height)

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
            self._position_resize_handles()

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
            self._help_popup_state = None  # Lazy-load state on first show
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
            self.help_image_label = QLabel('加载中...')
            self.help_image_label.setAlignment(Qt.AlignCenter)
            self.help_image_label.setProperty('cardSub', True)
            self.help_image_label.setMinimumSize(420, 96)
            layout.addWidget(self.help_image_label)
            self.help_caption_label = QLabel('感谢打赏')
            self.help_caption_label.setAlignment(Qt.AlignCenter)
            self.help_caption_label.setProperty('cardSub', True)
            self.help_caption_label.setStyleSheet('font-size: 18px; font-weight: 700;')
            layout.addWidget(self.help_caption_label)
            self.help_popup.adjustSize()

        def _ensure_help_popup_loaded(self):
            """Lazy-load help popup image on first show."""
            if self._help_popup_state is not None:
                return
            state = build_help_popup_state(WEIXIN_IMAGE_PATH)
            self._help_popup_state = state
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
                self.help_image_label.setMinimumSize(state['max_width'], 96)
            self.help_caption_label.setText(state['caption'])

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
            self._ensure_help_popup_loaded()
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
            if self.rect().contains(local_pos) and not self.help_popup.geometry().contains(local_pos):
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
            self._position_resize_handles()

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
                            logger.error("插件 on_app_close 异常: %s", name, exc_info=True)
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
                            logger.exception("tab cleanup 异常: %s", attr)
            super().closeEvent(event)

        def open_settings(self):
            self.user_menu.hide()
            dialog = SettingsDialog(self.settings, self._plugin_manager, self)
            if dialog.exec() == SettingsDialog.Accepted:
                self._apply_sidebar_order(self.settings)
                self.custom_theme_enabled = load_setting(self.settings, 'ui/custom_theme_enabled', '0') == '1'
                self._update_theme_button_state()
                self.refresh_theme_style()

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
                stack_idx = self._sidebar_to_stack[i]
                tid = self._stack_to_tool_id.get(stack_idx)
                if tid:
                    sidebar_ids.append(tid)
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
            reordered_labels = []
            for tid in new_ids:
                self._sidebar_to_stack.append(self._get_stack_index(tid))
                reordered_labels.append(sidebar_texts[tid])
            self.sidebar.addItems(reordered_labels)
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

        def _build_plugin_tab(self, name: str, plugin):
            tab_widget = plugin.get_tab_widget()
            if tab_widget is None:
                logger.warning("插件未提供页签控件: %s", name)
                return QWidget()
            self._plugin_tabs.append((name, tab_widget))
            return tab_widget

        def logout(self):
            self.relogin_requested = True
            save_setting(self.settings, 'auth/auto_login', '0')
            self.user_menu.hide()
            self.close()

        def _ensure_tab_created(self, tool_id: str):
            """Lazily create a tab widget on first access."""
            if tool_id not in self._tab_builders:
                return
            widget = self._tabs.get(tool_id)
            if widget is not None and not isinstance(widget, QWidget) or (isinstance(widget, QWidget) and tool_id in self._tab_builders and type(widget).__name__ == 'QWidget' and not widget.layout()):
                # It's a placeholder (plain QWidget with no layout)
                builder = self._tab_builders[tool_id]
                real_tab = builder(self._tab_settings)
                # Find stack index and replace placeholder
                for i in range(self.stack.count()):
                    if self.stack.widget(i) is widget:
                        self.stack.removeWidget(widget)
                        widget.deleteLater()
                        self.stack.insertWidget(i, real_tab)
                        break
                self._tabs[tool_id] = real_tab
                # Apply current theme to newly created tab
                if hasattr(real_tab, 'apply_theme'):
                    real_tab.apply_theme(self.current_theme)

        def _resolve_tab(self, tool_id: str):
            """Get tab, creating it lazily if needed."""
            self._ensure_tab_created(tool_id)
            return self._tabs.get(tool_id)

        def __getattr__(self, name):
            # Backward-compat lazy aliases
            _ALIAS_MAP = {
                'music_tab': 'music',
                'zip_tab': 'zipandpng',
                'mp4_tab': 'mp4mp3',
                'image_convert_tab': 'imageconvert',
                'pdf_tools_tab': 'pdftools',
                'tg_downloader_tab': 'tgdownloader',
                'web_video_downloader_tab': 'webvideodownloader',
                'batch_rename_tab': 'batchrename',
                'file_sorter_tab': 'filesorter',
                'same_tab': 'same',
                'base64_tab': 'base64',
                'word_formatter_tab': 'wordformatter',
            }
            if name == 'video_downloader_tab':
                return self._resolve_tab('tgdownloader')
            tool_id = _ALIAS_MAP.get(name)
            if tool_id is not None:
                return self._resolve_tab(tool_id)
            raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")

        def switch_tool_page(self, index: int):
            if 0 <= index < len(self._sidebar_to_stack):
                stack_idx = self._sidebar_to_stack[index]
                tool_id = self._stack_to_tool_id.get(stack_idx)
                if tool_id:
                    self._ensure_tab_created(tool_id)
                animate_stack_switch(self.stack, stack_idx)
            elif 0 <= index < self.stack.count():
                animate_stack_switch(self.stack, index)
            else:
                logger.warning("switch_tool_page: 无效索引 %d", index)

        def changeEvent(self, event):
            super().changeEvent(event)
            self.update_window_controls()

        def toggle_theme(self):
            next_mode = self._next_theme_mode()
            if next_mode == 'light':
                self.current_theme = 'light'
                self.custom_theme_enabled = False
            elif next_mode == 'dark':
                self.current_theme = 'dark'
                self.custom_theme_enabled = False
            else:
                self.custom_theme_enabled = True
            save_setting(self.settings, 'ui/theme', self.current_theme)
            save_setting(self.settings, 'ui/custom_theme_enabled', '1' if self.custom_theme_enabled else '0')
            self._update_theme_button_state()
            # Generic: iterate all tabs, call apply_theme if available
            for i in range(self.stack.count()):
                page = self.stack.widget(i)
                if hasattr(page, 'apply_theme'):
                    page.apply_theme(self.current_theme)
            self.setStyleSheet(get_theme_stylesheet(self.current_theme))
            if self.custom_theme_enabled:
                self._apply_custom_theme_colors()
            self.content_surface.setGraphicsEffect(None)
            self.update_window_controls()
            self.update_user_menu_ui()
            self._notify_plugins_theme_change()
            if hasattr(self, 'user_menu') and self.user_menu.isVisible():
                self.user_menu.hide()
            if hasattr(self, 'help_popup') and self.help_popup.isVisible():
                self.hide_help_popup()

        def toggle_custom_theme(self):
            self.custom_theme_enabled = not self.custom_theme_enabled
            save_setting(self.settings, 'ui/custom_theme_enabled', '1' if self.custom_theme_enabled else '0')
            self._update_theme_button_state()
            if self.custom_theme_enabled:
                self._apply_custom_theme_colors()
            else:
                self.setStyleSheet(get_theme_stylesheet(self.current_theme))
            self.content_surface.setGraphicsEffect(None)
            self.update_window_controls()
            self.update_user_menu_ui()
            self._notify_plugins_theme_change()

        def _update_custom_theme_button_state(self):
            self._update_theme_button_state()
            self._update_custom_theme_button_style()

        def _update_custom_theme_button_style(self):
            if not hasattr(self, 'custom_theme_button'):
                return
            if self.custom_theme_enabled:
                text_color = '#1f252d' if self.current_theme == 'light' else '#eef2f7'
                self.custom_theme_button.setStyleSheet(
                    'QPushButton { '
                    'background-color: rgba(111, 149, 199, 0.34); '
                    'border: 1px solid rgba(126, 166, 217, 0.85); '
                    'border-radius: 19px; '
                    'padding: 0; '
                    f'color: {text_color}; '
                    '} '
                    'QPushButton:hover { background-color: rgba(111, 149, 199, 0.44); } '
                    'QPushButton:pressed { background-color: rgba(111, 149, 199, 0.26); }'
                )
            else:
                self.custom_theme_button.setStyleSheet('')

        def _apply_custom_theme_colors(self):
            """Apply custom theme color overrides if enabled."""
            if not self.custom_theme_enabled:
                return
            custom = load_custom_colors(self.settings, self.current_theme)
            def_colors = get_default_colors(self.current_theme)
            overrides = {
                z: v for z, v in custom.items()
                if v and v != def_colors.get(z, '')
            }
            base = get_theme_stylesheet(self.current_theme)
            if overrides:
                qss = generate_qss(base, overrides, self.current_theme)
                self.setStyleSheet(qss + build_global_scrollbar_style())
            else:
                # 所有颜色都是默认值，也要重置掉旧的自定义 QSS
                self.setStyleSheet(base)

        def refresh_theme_style(self):
            """Re-apply theme with custom colors (called after settings dialog closes)."""
            if self.custom_theme_enabled:
                self._apply_custom_theme_colors()
            else:
                self.setStyleSheet(get_theme_stylesheet(self.current_theme))

        def _notify_plugins_theme_change(self):
            if hasattr(self, '_plugin_manager') and self._plugin_manager is not None:
                for name, plugin in self._plugin_manager.get_enabled_plugins().items():
                    try:
                        plugin.on_theme_change(self.current_theme)
                    except Exception:
                        logger.error("插件 on_theme_change 异常: %s", name, exc_info=True)

        def _update_theme_button_tooltip(self):
            self._update_theme_button_state()

        def _theme_mode(self):
            if self.custom_theme_enabled:
                return 'custom'
            return 'light' if self.current_theme == 'light' else 'dark'

        def _next_theme_mode(self):
            return {
                'light': 'dark',
                'dark': 'custom',
                'custom': 'light',
            }[self._theme_mode()]

        def _update_theme_button_state(self):
            mode = self._theme_mode()
            next_mode = self._next_theme_mode()
            self.theme_button.setText({
                'light': '🌙',
                'dark': '☀️',
                'custom': '🎨',
            }[mode])
            self.theme_button.setToolTip({
                'light': '切换为白天主题',
                'dark': '切换为夜晚主题',
                'custom': '切换为自定义配色',
            }[next_mode])

    return ToolboxWindow
