"""Settings dialog — receives all dependencies via builder."""

from __future__ import annotations


def build_settings_dialog_class(deps: dict):
    """Return a SettingsDialog class with all Qt/helper deps injected."""

    QDialog = deps['QDialog']
    QVBoxLayout = deps['QVBoxLayout']
    QHBoxLayout = deps['QHBoxLayout']
    QPushButton = deps['QPushButton']
    QLabel = deps['QLabel']
    QCheckBox = deps['QCheckBox']
    QWidget = deps['QWidget']
    QFrame = deps['QFrame']
    QListWidget = deps['QListWidget']
    QStackedWidget = deps['QStackedWidget']
    QScrollArea = deps['QScrollArea']
    Qt = deps['Qt']
    DragTitleBar = deps['DragTitleBar']
    load_setting = deps['load_setting']
    save_setting = deps['save_setting']
    get_theme_stylesheet = deps['get_theme_stylesheet']
    build_global_scrollbar_style = deps['build_global_scrollbar_style']
    TOOL_DEFINITIONS = deps['TOOL_DEFINITIONS']

    _NAV_ITEMS = [
        ('account', '👤  账号设置'),
        ('plugins', '🧩  功能管理'),
        ('order', '📋  导航排序'),
    ]

    QTimer = deps.get('QTimer')

    class _DragScrollList(QListWidget):
        """QListWidget that auto-scrolls smoothly during drag near edges."""

        _MARGIN = 40
        _MIN_INTERVAL = 16
        _MAX_INTERVAL = 120
        _STEP = 2

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self._scroll_timer = QTimer(self) if QTimer else None
            self._scroll_dir = 0
            self._dragging = False
            if self._scroll_timer:
                self._scroll_timer.timeout.connect(self._on_tick)

        def startDrag(self, supportedActions):
            self._dragging = True
            # 启动轮询 timer（固定 30ms 刷新）
            if self._scroll_timer:
                self._scroll_timer.start(30)
            super().startDrag(supportedActions)
            # startDrag 返回说明拖拽结束
            self._dragging = False
            self._stop_scroll()

        def _on_tick(self):
            if not self._dragging:
                self._stop_scroll()
                return
            cursor_pos = self.mapFromGlobal(self.cursor().pos())
            y = cursor_pos.y()
            h = self.viewport().height()
            if y < self._MARGIN:
                self._scroll_dir = -1
                dist = max(1, y)
            elif y > h - self._MARGIN:
                self._scroll_dir = 1
                dist = max(1, h - y)
            else:
                self._scroll_dir = 0
                return
            # 距离越近速度越快
            ratio = dist / self._MARGIN
            speed = self._STEP + int((1 - ratio) * 4)
            sb = self.verticalScrollBar()
            sb.setValue(sb.value() + self._scroll_dir * speed)

        def _stop_scroll(self):
            self._scroll_dir = 0
            if self._scroll_timer and self._scroll_timer.isActive():
                self._scroll_timer.stop()

    class SettingsDialog(QDialog):
        def __init__(self, settings, plugin_manager=None, parent=None):
            super().__init__(parent)
            self.settings = settings
            self.plugin_manager = plugin_manager
            self.current_theme = load_setting(settings, 'ui/theme', 'dark')
            self.setWindowTitle('设置')
            self.setModal(True)
            self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
            self._drag_offset = None
            self.resize(680, 520)
            self._build_ui()
            self._load_current_settings()
            self._nav_list.setCurrentRow(0)

        # ---- layout ----

        def _build_ui(self):
            root = QVBoxLayout(self)
            root.setContentsMargins(10, 10, 10, 10)
            root.setSpacing(0)
            self.content_surface = QWidget()
            self.content_surface.setProperty('contentSurface', True)
            content_layout = QVBoxLayout(self.content_surface)
            content_layout.setContentsMargins(0, 0, 0, 0)
            content_layout.setSpacing(0)
            self.drag_bar = DragTitleBar(self)
            self.drag_bar.title_label.setText('设置')
            if hasattr(self, 'min_button'):
                self.min_button.hide()
            if hasattr(self, 'max_button'):
                self.max_button.hide()
            content_layout.addWidget(self.drag_bar)
            # --- body: sidebar + content ---
            body = QWidget()
            shell = QHBoxLayout(body)
            shell.setContentsMargins(0, 0, 0, 0)
            shell.setSpacing(0)
            # left nav
            nav_panel = QFrame()
            nav_panel.setProperty('navPanel', True)
            nav_panel.setFixedWidth(156)
            nav_layout = QVBoxLayout(nav_panel)
            nav_layout.setContentsMargins(14, 18, 10, 18)
            nav_layout.setSpacing(4)
            self._nav_list = QListWidget()
            self._nav_list.setProperty('navList', True)
            for _, label in _NAV_ITEMS:
                self._nav_list.addItem(label)
            self._nav_list.setFixedWidth(132)
            self._nav_list.currentRowChanged.connect(self._on_nav_changed)
            nav_layout.addWidget(self._nav_list, 1)
            shell.addWidget(nav_panel)
            # right content
            self._stack = QStackedWidget()
            self._stack.addWidget(self._build_account_page())
            self._stack.addWidget(self._build_plugins_page())
            self._stack.addWidget(self._build_order_page())
            shell.addWidget(self._stack, 1)
            content_layout.addWidget(body, 1)
            # --- bottom button row ---
            btn_bar = QWidget()
            btn_bar_layout = QHBoxLayout(btn_bar)
            btn_bar_layout.setContentsMargins(18, 10, 18, 16)
            btn_bar_layout.setSpacing(10)
            btn_bar_layout.addStretch(1)
            cancel_btn = QPushButton('取消')
            cancel_btn.setMinimumHeight(36)
            cancel_btn.setMinimumWidth(88)
            cancel_btn.clicked.connect(self.reject)
            btn_bar_layout.addWidget(cancel_btn)
            self.save_button = QPushButton('保存')
            self.save_button.setMinimumHeight(36)
            self.save_button.setMinimumWidth(88)
            self.save_button.clicked.connect(self._save_and_close)
            btn_bar_layout.addWidget(self.save_button)
            content_layout.addWidget(btn_bar)
            root.addWidget(self.content_surface)
            self.setStyleSheet(get_theme_stylesheet(self.current_theme) + build_global_scrollbar_style())
            self.close_button.clicked.disconnect()
            self.close_button.clicked.connect(self.reject)

        def _on_nav_changed(self, row: int):
            self._stack.setCurrentIndex(row)

        # ---- account page ----

        def _build_account_page(self):
            page = QWidget()
            layout = QVBoxLayout(page)
            layout.setContentsMargins(24, 22, 24, 16)
            layout.setSpacing(16)
            title = QLabel('账号设置')
            title.setProperty('brandTitle', True)
            layout.addWidget(title)
            # card
            card = QFrame()
            card.setProperty('card', True)
            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(20, 18, 20, 18)
            card_layout.setSpacing(14)
            self.remember_checkbox = QCheckBox('记住密码')
            self.remember_checkbox.toggled.connect(self._on_remember_toggled)
            card_layout.addWidget(self.remember_checkbox)
            sub = QLabel('下次启动时自动填充已保存的密码。')
            sub.setProperty('cardSub', True)
            sub.setContentsMargins(24, 0, 0, 0)
            card_layout.addWidget(sub)
            sep = QFrame()
            sep.setFrameShape(QFrame.HLine)
            sep.setStyleSheet('background: rgba(128,128,128,0.15); max-height: 1px;')
            card_layout.addWidget(sep)
            self.auto_login_checkbox = QCheckBox('自动登录')
            self.auto_login_checkbox.toggled.connect(self._on_auto_login_toggled)
            card_layout.addWidget(self.auto_login_checkbox)
            sub2 = QLabel('启动时跳过登录界面，直接进入工具箱。需要先开启"记住密码"。')
            sub2.setProperty('cardSub', True)
            sub2.setWordWrap(True)
            sub2.setContentsMargins(24, 0, 0, 0)
            card_layout.addWidget(sub2)
            layout.addWidget(card)
            layout.addStretch(1)
            return page

        # ---- plugins page ----

        def _build_plugins_page(self):
            page = QWidget()
            layout = QVBoxLayout(page)
            layout.setContentsMargins(24, 22, 24, 16)
            layout.setSpacing(16)
            title = QLabel('功能管理')
            title.setProperty('brandTitle', True)
            layout.addWidget(title)
            hint = QLabel('启用或禁用工具和插件，保存后重启生效。')
            hint.setProperty('cardSub', True)
            layout.addWidget(hint)
            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            scroll.setFrameShape(QFrame.NoFrame)
            scroll_widget = QWidget()
            self._plugin_layout = QVBoxLayout(scroll_widget)
            self._plugin_layout.setContentsMargins(0, 0, 0, 0)
            self._plugin_layout.setSpacing(10)
            self._tool_checkboxes: dict[str, QCheckBox] = {}
            self._plugin_checkboxes: dict[str, QCheckBox] = {}
            # 内置工具
            disabled_tools_str = load_setting(self.settings, 'tools/disabled', '')
            disabled_tools = set(disabled_tools_str.split(',')) if disabled_tools_str.strip() else set()
            for t in TOOL_DEFINITIONS:
                self._tool_checkboxes[t.id] = self._make_tool_card(t, t.id not in disabled_tools)
            # 外部插件
            if self.plugin_manager is not None:
                infos = self.plugin_manager.discovery.get_all_plugins()
                disabled_str = load_setting(self.settings, 'plugins/disabled', '')
                disabled = set(disabled_str.split(',')) if disabled_str.strip() else set()
                for name, info in sorted(infos.items()):
                    sidebar_label = self._label_map.get(f'plugin:{name}', name) if hasattr(self, '_label_map') else name
                    self._plugin_layout.addWidget(self._make_plugin_card(name, info, sidebar_label, name not in disabled))
            if not self._plugin_checkboxes:
                empty = QLabel('暂无已安装的扩展插件。')
                empty.setProperty('cardSub', True)
                self._plugin_layout.addWidget(empty)
            self._plugin_layout.addStretch(1)
            scroll.setWidget(scroll_widget)
            layout.addWidget(scroll, 1)
            return page

        def _make_tool_card(self, tool_def, checked):
            card = QFrame()
            card.setProperty('card', True)
            h = QHBoxLayout(card)
            h.setContentsMargins(18, 14, 18, 14)
            h.setSpacing(12)
            text_col = QVBoxLayout()
            text_col.setSpacing(3)
            name_lbl = QLabel(tool_def.title)
            name_lbl.setProperty('cardTitle', True)
            text_col.addWidget(name_lbl)
            desc_lbl = QLabel(tool_def.sidebar_label)
            desc_lbl.setProperty('cardSub', True)
            text_col.addWidget(desc_lbl)
            h.addLayout(text_col, 1)
            cb = QCheckBox()
            cb.setChecked(checked)
            cb.setMinimumWidth(48)
            self._tool_checkboxes[tool_def.id] = cb
            h.addWidget(cb, 0, Qt.AlignVCenter)
            self._plugin_layout.addWidget(card)
            return cb

        def _make_plugin_card(self, name, info, sidebar_label, checked):
            card = QFrame()
            card.setProperty('card', True)
            h = QHBoxLayout(card)
            h.setContentsMargins(18, 14, 18, 14)
            h.setSpacing(12)
            text_col = QVBoxLayout()
            text_col.setSpacing(3)
            row1 = QHBoxLayout()
            row1.setSpacing(8)
            name_lbl = QLabel(sidebar_label)
            name_lbl.setProperty('cardTitle', True)
            row1.addWidget(name_lbl)
            ver_lbl = QLabel(f'v{info.version}')
            ver_lbl.setProperty('cardSub', True)
            row1.addWidget(ver_lbl)
            row1.addStretch(1)
            text_col.addLayout(row1)
            if info.description:
                desc_lbl = QLabel(info.description)
                desc_lbl.setProperty('cardSub', True)
                desc_lbl.setWordWrap(True)
                text_col.addWidget(desc_lbl)
            h.addLayout(text_col, 1)
            cb = QCheckBox()
            cb.setChecked(checked)
            cb.setMinimumWidth(48)
            self._plugin_checkboxes[name] = cb
            h.addWidget(cb, 0, Qt.AlignVCenter)
            return card

        # ---- order page ----

        def _build_order_page(self):
            page = QWidget()
            layout = QVBoxLayout(page)
            layout.setContentsMargins(24, 22, 24, 16)
            layout.setSpacing(16)
            title = QLabel('导航排序')
            title.setProperty('brandTitle', True)
            layout.addWidget(title)
            hint = QLabel('拖拽调整左侧导航栏工具的显示顺序，保存后立即生效。')
            hint.setProperty('cardSub', True)
            layout.addWidget(hint)
            card = QFrame()
            card.setProperty('card', True)
            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(6, 6, 6, 6)
            card_layout.setSpacing(0)
            self._order_list = _DragScrollList()
            self._order_list.setDragEnabled(True)
            self._order_list.setDragDropMode(QListWidget.InternalMove)
            self._order_list.setDefaultDropAction(Qt.MoveAction)
            self._order_list.setSelectionMode(QListWidget.SingleSelection)
            self._order_list.model().rowsMoved.connect(self._on_order_changed)
            # 读取禁用列表
            disabled_tools_str = load_setting(self.settings, 'tools/disabled', '')
            disabled_tools = set(disabled_tools_str.split(',')) if disabled_tools_str.strip() else set()
            disabled_plugins_str = load_setting(self.settings, 'plugins/disabled', '')
            disabled_plugins = set(disabled_plugins_str.split(',')) if disabled_plugins_str.strip() else set()
            # 读取保存的顺序（包含所有项）
            saved_order = load_setting(self.settings, 'sidebar/order', '')
            full_order = [s.strip() for s in saved_order.split(',') if s.strip()] if saved_order.strip() else []
            # 构建所有可能的 id 集合
            all_ids = [t.id for t in TOOL_DEFINITIONS]
            if self.plugin_manager is not None:
                for name, plugin in self.plugin_manager.discovery.get_all_plugins().items():
                    if plugin.plugin_type == 'gui':
                        all_ids.append(f'plugin:{name}')
            # 补全 saved_order 中缺失的新 id
            for tid in all_ids:
                if tid not in full_order:
                    full_order.append(tid)
            # 只显示已启用的项
            enabled_ids = []
            for tid in full_order:
                if tid.startswith('plugin:'):
                    pname = tid[7:]
                    if pname not in disabled_plugins:
                        enabled_ids.append(tid)
                else:
                    if tid not in disabled_tools:
                        enabled_ids.append(tid)
            self._full_order = full_order
            self._disabled_tools = disabled_tools
            self._disabled_plugins = disabled_plugins
            label_map = {t.id: t.sidebar_label for t in TOOL_DEFINITIONS}
            if self.plugin_manager is not None:
                for name, plugin in self.plugin_manager.discovery.get_all_plugins().items():
                    label_map[f'plugin:{name}'] = plugin.get_sidebar_label() if hasattr(plugin, 'get_sidebar_label') else name
            self._label_map = label_map
            for tid in enabled_ids:
                self._order_list.addItem(label_map.get(tid, tid))
            card_layout.addWidget(self._order_list)
            layout.addWidget(card, 1)
            btn_row = QHBoxLayout()
            btn_row.addStretch(1)
            reset_btn = QPushButton('恢复默认顺序')
            reset_btn.setMinimumHeight(34)
            reset_btn.clicked.connect(self._reset_order)
            btn_row.addWidget(reset_btn)
            layout.addLayout(btn_row)
            return page

        def _on_order_changed(self):
            pass

        def _reset_order(self):
            self._order_list.clear()
            for t in TOOL_DEFINITIONS:
                if t.id not in self._disabled_tools:
                    self._order_list.addItem(self._label_map.get(t.id, t.sidebar_label))
            if self.plugin_manager is not None:
                for name, plugin in self.plugin_manager.discovery.get_all_plugins().items():
                    pid = f'plugin:{name}'
                    if plugin.plugin_type == 'gui' and name not in self._disabled_plugins:
                        self._order_list.addItem(self._label_map.get(pid, name))

        def _get_current_order_ids(self) -> list[str]:
            label_to_id = {v: k for k, v in self._label_map.items()}
            # 可见项（按当前顺序）
            visible = []
            for i in range(self._order_list.count()):
                text = self._order_list.item(i).text()
                visible.append(label_to_id.get(text, text))
            # 禁用项追加到末尾（保持原顺序）
            disabled = []
            for tid in self._full_order:
                if tid not in visible:
                    disabled.append(tid)
            return visible + disabled

        # ---- logic ----

        def _load_current_settings(self):
            remember = load_setting(self.settings, 'auth/remember_password', '0') == '1'
            auto_login = load_setting(self.settings, 'auth/auto_login', '0') == '1'
            self.remember_checkbox.setChecked(remember)
            self.auto_login_checkbox.setChecked(auto_login)

        def _on_remember_toggled(self, checked: bool):
            if not checked and self.auto_login_checkbox.isChecked():
                self.auto_login_checkbox.setChecked(False)

        def _on_auto_login_toggled(self, checked: bool):
            if checked and not self.remember_checkbox.isChecked():
                self.remember_checkbox.setChecked(True)

        def _save_and_close(self):
            save_setting(self.settings, 'auth/remember_password', '1' if self.remember_checkbox.isChecked() else '0')
            save_setting(self.settings, 'auth/auto_login', '1' if self.auto_login_checkbox.isChecked() else '0')
            # 内置工具
            disabled_tools = set()
            enabled_tools = 0
            for tid, cb in self._tool_checkboxes.items():
                if cb.isChecked():
                    enabled_tools += 1
                else:
                    disabled_tools.add(tid)
            # 外部插件（也计入）
            enabled_plugins = 0
            for name, cb in self._plugin_checkboxes.items():
                if cb.isChecked():
                    enabled_plugins += 1
            if enabled_tools + enabled_plugins == 0:
                from toolbox_app.widgets.dialogs import show_themed_warning
                show_themed_warning(self, '无法保存', '至少需要保留一个功能或插件处于启用状态。')
                return
            save_setting(self.settings, 'tools/disabled', ','.join(sorted(disabled_tools)))
            # 外部插件
            if self.plugin_manager is not None:
                disabled = set()
                for name, cb in self._plugin_checkboxes.items():
                    if cb.isChecked():
                        self.plugin_manager.set_plugin_enabled(name, True)
                    else:
                        disabled.add(name)
                        self.plugin_manager.set_plugin_enabled(name, False)
                save_setting(self.settings, 'plugins/disabled', ','.join(sorted(disabled)))
            order_ids = self._get_current_order_ids()
            save_setting(self.settings, 'sidebar/order', ','.join(order_ids))
            self.accept()

        # ---- window drag ----

        def start_window_drag(self, global_pos):
            self._drag_offset = global_pos - self.frameGeometry().topLeft()

        def update_window_drag(self, global_pos):
            if self._drag_offset is None:
                return
            self.move(global_pos - self._drag_offset)

        def stop_window_drag(self):
            self._drag_offset = None

        def toggle_max_restore(self):
            return

    return SettingsDialog
