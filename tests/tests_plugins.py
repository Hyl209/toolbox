"""Tests for the plugin system: discovery, loading, instantiation, lifecycle."""
from __future__ import annotations

import json
import textwrap
import tempfile
from pathlib import Path

import pytest

from toolbox_app.plugins.base import PluginBase, PluginInfo
from toolbox_app.plugins.discovery import PluginDiscovery
from toolbox_app.plugins.registry import PluginRegistry
from toolbox_app.plugins.manager import PluginManager, reset_plugin_manager


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def tmp_plugins_dir(tmp_path):
    """Create a temporary plugins directory."""
    d = tmp_path / "plugins"
    d.mkdir()
    return d


@pytest.fixture
def gui_plugin_dir(tmp_plugins_dir):
    """Create a sample GUI plugin directory with manifest."""
    plugin_dir = tmp_plugins_dir / "my_gui_tool"
    plugin_dir.mkdir()
    manifest = {
        "name": "my_gui_tool",
        "version": "1.0.0",
        "description": "Test GUI plugin",
        "author": "Tester",
        "entry": "plugin.py:MyGuiPlugin",
        "type": "gui",
    }
    (plugin_dir / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    (plugin_dir / "plugin.py").write_text(textwrap.dedent('''\
        from toolbox_app.plugins.base import PluginBase, PluginInfo

        class MyGuiPlugin(PluginBase):
            def get_plugin_info(self):
                return PluginInfo(
                    name="my_gui_tool", version="1.0.0",
                    description="Test GUI plugin", author="Tester",
                    plugin_type="gui",
                )
            def initialize(self, deps=None):
                self._deps = deps or {}
                return True
            def get_sidebar_label(self):
                return "My GUI Tool"
            def get_tab_widget(self):
                return "fake_widget"
            def cleanup(self):
                pass
    '''), encoding="utf-8")
    return plugin_dir


@pytest.fixture
def hook_plugin_file(tmp_plugins_dir):
    """Create a single-file hook plugin."""
    plugin_file = tmp_plugins_dir / "my_hook.py"
    plugin_file.write_text(textwrap.dedent('''\
        from toolbox_app.plugins.base import PluginBase, PluginInfo

        class MyHookPlugin(PluginBase):
            def get_plugin_info(self):
                return PluginInfo(
                    name="my_hook", version="1.0.0",
                    description="Test hook plugin", author="Tester",
                    plugin_type="hook",
                )
            def initialize(self, deps=None):
                return True
            def cleanup(self):
                pass
    '''), encoding="utf-8")
    return plugin_file


# ---------------------------------------------------------------------------
# PluginBase tests
# ---------------------------------------------------------------------------

class TestPluginBase:
    def test_plugin_info_defaults(self):
        info = PluginInfo(name="test", version="1.0", description="d", author="a")
        assert info.dependencies == []
        assert info.enabled is True
        assert info.priority == 0
        assert info.plugin_type == "gui"
        assert info.entry == ""
        assert info.plugin_path == ""

    def test_plugin_info_custom(self):
        info = PluginInfo(
            name="x", version="2.0", description="d", author="a",
            plugin_type="hook", entry="p.py:C", plugin_path="/tmp/p",
        )
        assert info.plugin_type == "hook"
        assert info.entry == "p.py:C"


# ---------------------------------------------------------------------------
# PluginDiscovery tests
# ---------------------------------------------------------------------------

class TestPluginDiscovery:
    def test_discover_manifest_plugin(self, gui_plugin_dir, tmp_plugins_dir):
        disc = PluginDiscovery(tmp_plugins_dir)
        found = disc.discover_plugins()
        assert "my_gui_tool" in found
        info = found["my_gui_tool"]
        assert info.version == "1.0.0"
        assert info.plugin_type == "gui"
        assert info.entry == "plugin.py:MyGuiPlugin"
        assert info.plugin_path == str(gui_plugin_dir)

    def test_discover_single_file_plugin(self, hook_plugin_file, tmp_plugins_dir):
        disc = PluginDiscovery(tmp_plugins_dir)
        found = disc.discover_plugins()
        assert "my_hook" in found
        info = found["my_hook"]
        assert info.plugin_type == "hook"
        assert "MyHookPlugin" in info.entry

    def test_discover_empty_dir(self, tmp_plugins_dir):
        disc = PluginDiscovery(tmp_plugins_dir)
        found = disc.discover_plugins()
        assert len(found) == 0

    def test_validate_missing_dependency(self, tmp_plugins_dir):
        plugin_dir = tmp_plugins_dir / "dep_plugin"
        plugin_dir.mkdir()
        manifest = {
            "name": "dep_plugin", "version": "1.0", "description": "d", "author": "a",
            "entry": "plugin.py:X", "dependencies": ["nonexistent"],
        }
        (plugin_dir / "manifest.json").write_text(json.dumps(manifest))
        (plugin_dir / "plugin.py").write_text("pass")
        disc = PluginDiscovery(tmp_plugins_dir)
        disc.discover_plugins()
        assert disc.validate_plugin("dep_plugin") is False


# ---------------------------------------------------------------------------
# PluginRegistry tests
# ---------------------------------------------------------------------------

class TestPluginRegistry:
    def _make_plugin(self, name="test_plugin"):
        class P(PluginBase):
            def get_plugin_info(self_info):
                return PluginInfo(name=name, version="1.0", description="d", author="a")
            def initialize(self_info, deps=None):
                self_info._is_initialized = True
                return True
            def cleanup(self_info):
                pass
        return P()

    def test_register_and_get(self):
        reg = PluginRegistry()
        p = self._make_plugin()
        assert reg.register(p) is True
        assert reg.get_plugin("test_plugin") is p
        assert reg.has_plugin("test_plugin") is True

    def test_duplicate_register_raises(self):
        reg = PluginRegistry()
        reg.register(self._make_plugin())
        assert reg.register(self._make_plugin()) is False

    def test_initialize_with_deps(self):
        reg = PluginRegistry()
        p = self._make_plugin()
        reg.register(p)
        deps = {"QWidget": object}
        assert reg.initialize_plugin("test_plugin", deps) is True
        assert p.is_initialized is True

    def test_cleanup_all(self):
        reg = PluginRegistry()
        p = self._make_plugin()
        reg.register(p)
        reg.cleanup_all()
        assert reg.get_plugin_count() == 0

    def test_enable_disable(self):
        reg = PluginRegistry()
        p = self._make_plugin()
        reg.register(p)
        reg.disable_plugin("test_plugin")
        assert p.is_enabled is False
        reg.enable_plugin("test_plugin")
        assert p.is_enabled is True


# ---------------------------------------------------------------------------
# PluginManager tests (full integration)
# ---------------------------------------------------------------------------

class TestPluginManager:
    def test_load_gui_plugin(self, gui_plugin_dir, tmp_plugins_dir):
        reset_plugin_manager()
        mgr = PluginManager(tmp_plugins_dir)
        results = mgr.load_all_plugins()
        assert results.get("my_gui_tool") is True
        plugin = mgr.get_plugin("my_gui_tool")
        assert plugin is not None
        assert plugin.plugin_info.plugin_type == "gui"
        assert plugin.get_sidebar_label() == "My GUI Tool"

    def test_load_hook_plugin(self, hook_plugin_file, tmp_plugins_dir):
        reset_plugin_manager()
        mgr = PluginManager(tmp_plugins_dir)
        results = mgr.load_all_plugins()
        assert results.get("my_hook") is True
        plugin = mgr.get_plugin("my_hook")
        assert plugin is not None
        assert plugin.plugin_info.plugin_type == "hook"

    def test_load_with_disabled_names(self, gui_plugin_dir, tmp_plugins_dir):
        reset_plugin_manager()
        mgr = PluginManager(tmp_plugins_dir)
        results = mgr.load_all_plugins(disabled_names={"my_gui_tool"})
        assert results.get("my_gui_tool") is False
        assert mgr.get_plugin("my_gui_tool") is None

    def test_initialize_with_deps(self, gui_plugin_dir, tmp_plugins_dir):
        reset_plugin_manager()
        mgr = PluginManager(tmp_plugins_dir)
        mgr.load_all_plugins()
        deps = {"QWidget": object, "QVBoxLayout": object, "QLabel": object}
        results = mgr.initialize_all_plugins(deps)
        assert results.get("my_gui_tool") is True
        plugin = mgr.get_plugin("my_gui_tool")
        assert plugin.is_initialized is True

    def test_cleanup_all(self, gui_plugin_dir, tmp_plugins_dir):
        reset_plugin_manager()
        mgr = PluginManager(tmp_plugins_dir)
        mgr.load_all_plugins()
        mgr.cleanup_all_plugins()
        assert mgr.get_plugin_count() == 0

    def test_disabled_persistence(self, gui_plugin_dir, tmp_plugins_dir):
        reset_plugin_manager()
        mgr = PluginManager(tmp_plugins_dir)
        mgr.load_all_plugins()
        mgr.disable_plugin("my_gui_tool")
        disabled = mgr.get_disabled_plugin_names()
        assert "my_gui_tool" in disabled

    def test_load_invalid_plugin(self, tmp_plugins_dir):
        """Plugin with bad entry should not crash the manager."""
        reset_plugin_manager()
        plugin_dir = tmp_plugins_dir / "bad_plugin"
        plugin_dir.mkdir()
        manifest = {
            "name": "bad_plugin", "version": "1.0", "description": "d", "author": "a",
            "entry": "nonexistent.py:Foo",
        }
        (plugin_dir / "manifest.json").write_text(json.dumps(manifest))
        (plugin_dir / "plugin.py").write_text("pass")
        mgr = PluginManager(tmp_plugins_dir)
        results = mgr.load_all_plugins()
        assert results.get("bad_plugin") is False
