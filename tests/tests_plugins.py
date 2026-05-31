"""Tests for the plugin system: discovery, loading, instantiation, lifecycle."""
from __future__ import annotations

import json
import sys
import textwrap
import tempfile
from pathlib import Path

import pytest

from toolbox_app.plugins.base import PluginBase, PluginInfo
from toolbox_app.plugins.discovery import PluginDiscovery
from toolbox_app.plugins.registry import PluginRegistry
from toolbox_app.plugins.manager import PluginManager, get_plugin_manager, reset_plugin_manager


ROOT = Path(__file__).resolve().parents[1]


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
        "sidebar_label": "Friendly GUI Tool",
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
        assert info.sidebar_label == ""

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
        assert info.sidebar_label == "Friendly GUI Tool"

    def test_discover_single_file_plugin(self, hook_plugin_file, tmp_plugins_dir):
        disc = PluginDiscovery(tmp_plugins_dir)
        found = disc.discover_plugins()
        assert "my_hook" in found
        info = found["my_hook"]
        assert info.plugin_type == "hook"
        assert "MyHookPlugin" in info.entry

    def test_single_file_plugin_metadata_is_trimmed(self, tmp_plugins_dir):
        plugin_file = tmp_plugins_dir / "trimmed_source.py"
        plugin_file.write_text(textwrap.dedent('''\
            from toolbox_app.plugins.base import PluginBase, PluginInfo

            class TrimmedSourcePlugin(PluginBase):
                def get_plugin_info(self):
                    return PluginInfo(
                        name=" trimmed_source ", version=" 1.0 ",
                        description=" d ", author=" a ",
                        plugin_type=" hook ", sidebar_label=" Trimmed Source ",
                    )
                def initialize(self, deps=None):
                    return True
                def cleanup(self):
                    pass
        '''), encoding="utf-8")

        disc = PluginDiscovery(tmp_plugins_dir)
        found = disc.discover_plugins()

        info = found["trimmed_source"]
        assert info.version == "1.0"
        assert info.description == "d"
        assert info.author == "a"
        assert info.plugin_type == "hook"
        assert info.sidebar_label == "Trimmed Source"

    def test_single_file_plugin_invalid_metadata_is_skipped(self, tmp_plugins_dir):
        plugin_file = tmp_plugins_dir / "bad_source.py"
        plugin_file.write_text(textwrap.dedent('''\
            from toolbox_app.plugins.base import PluginBase, PluginInfo

            class BadSourcePlugin(PluginBase):
                def get_plugin_info(self):
                    return PluginInfo(
                        name="bad-source", version="1.0",
                        description="d", author="a",
                        plugin_type="service",
                    )
                def initialize(self, deps=None):
                    return True
                def cleanup(self):
                    pass
        '''), encoding="utf-8")

        disc = PluginDiscovery(tmp_plugins_dir)

        assert "bad-source" not in disc.discover_plugins()

    def test_discover_empty_dir(self, tmp_plugins_dir):
        disc = PluginDiscovery(tmp_plugins_dir)
        found = disc.discover_plugins()
        assert len(found) == 0

    def test_discover_missing_dir_returns_empty(self, tmp_path):
        disc = PluginDiscovery(tmp_path / "missing_plugins")
        assert disc.discover_plugins() == {}

    def test_discover_file_path_returns_empty(self, tmp_path):
        plugin_file = tmp_path / "plugins"
        plugin_file.write_text("not a directory", encoding="utf-8")
        disc = PluginDiscovery(plugin_file)
        assert disc.discover_plugins() == {}

    def test_discover_skips_generated_and_hidden_directories(self, tmp_plugins_dir):
        for dirname in ["__pycache__", "logs", ".codex-pytest-tmp", ".hidden_plugin"]:
            plugin_dir = tmp_plugins_dir / dirname
            plugin_dir.mkdir()
            (plugin_dir / "__init__.py").write_text(textwrap.dedent('''\
                from toolbox_app.plugins.base import PluginBase, PluginInfo
                class ShouldNotLoadPlugin(PluginBase):
                    def get_plugin_info(self):
                        return PluginInfo(
                            name="generated_plugin", version="1.0",
                            description="generated", author="Tester",
                        )
            '''), encoding="utf-8")

        disc = PluginDiscovery(tmp_plugins_dir)
        assert disc.discover_plugins() == {}

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

    def test_manifest_dependency_string_is_normalized(self, tmp_plugins_dir):
        plugin_dir = tmp_plugins_dir / "string_dep"
        plugin_dir.mkdir()
        manifest = {
            "name": "string_dep", "version": "1.0", "description": "d", "author": "a",
            "entry": "plugin.py:X", "dependencies": " dep_tool ",
        }
        (plugin_dir / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
        (plugin_dir / "plugin.py").write_text("pass", encoding="utf-8")

        disc = PluginDiscovery(tmp_plugins_dir)
        found = disc.discover_plugins()

        assert found["string_dep"].dependencies == ["dep_tool"]

    def test_manifest_empty_dependency_name_is_skipped(self, tmp_plugins_dir):
        plugin_dir = tmp_plugins_dir / "empty_dep"
        plugin_dir.mkdir()
        manifest = {
            "name": "empty_dep", "version": "1.0", "description": "d", "author": "a",
            "entry": "plugin.py:X", "dependencies": ["dep_tool", " "],
        }
        (plugin_dir / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
        (plugin_dir / "plugin.py").write_text("pass", encoding="utf-8")

        disc = PluginDiscovery(tmp_plugins_dir)

        assert "empty_dep" not in disc.discover_plugins()

    def test_manifest_invalid_dependency_name_is_skipped(self, tmp_plugins_dir):
        plugin_dir = tmp_plugins_dir / "bad_dep_name"
        plugin_dir.mkdir()
        manifest = {
            "name": "bad_dep_name", "version": "1.0", "description": "d", "author": "a",
            "entry": "plugin.py:X", "dependencies": "bad-name",
        }
        (plugin_dir / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
        (plugin_dir / "plugin.py").write_text("pass", encoding="utf-8")

        disc = PluginDiscovery(tmp_plugins_dir)

        assert "bad_dep_name" not in disc.discover_plugins()

    def test_manifest_self_dependency_is_skipped(self, tmp_plugins_dir):
        plugin_dir = tmp_plugins_dir / "self_dep"
        plugin_dir.mkdir()
        manifest = {
            "name": "self_dep", "version": "1.0", "description": "d", "author": "a",
            "entry": "plugin.py:X", "dependencies": ["self_dep"],
        }
        (plugin_dir / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
        (plugin_dir / "plugin.py").write_text("pass", encoding="utf-8")

        disc = PluginDiscovery(tmp_plugins_dir)

        assert "self_dep" not in disc.discover_plugins()

    def test_manifest_dependency_cycle_is_skipped(self, tmp_plugins_dir):
        for name, dep in (("cycle_a", "cycle_b"), ("cycle_b", "cycle_a")):
            plugin_dir = tmp_plugins_dir / name
            plugin_dir.mkdir()
            manifest = {
                "name": name, "version": "1.0", "description": "d", "author": "a",
                "entry": "plugin.py:X", "dependencies": [dep],
            }
            (plugin_dir / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
            (plugin_dir / "plugin.py").write_text("pass", encoding="utf-8")

        disc = PluginDiscovery(tmp_plugins_dir)
        found = disc.discover_plugins()

        assert "cycle_a" not in found
        assert "cycle_b" not in found

    def test_manifest_invalid_dependencies_type_is_skipped(self, tmp_plugins_dir):
        plugin_dir = tmp_plugins_dir / "bad_deps"
        plugin_dir.mkdir()
        manifest = {
            "name": "bad_deps", "version": "1.0", "description": "d", "author": "a",
            "entry": "plugin.py:X", "dependencies": 123,
        }
        (plugin_dir / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
        (plugin_dir / "plugin.py").write_text("pass", encoding="utf-8")

        disc = PluginDiscovery(tmp_plugins_dir)

        assert "bad_deps" not in disc.discover_plugins()

    def test_manifest_required_text_fields_must_be_non_empty_strings(self, tmp_plugins_dir):
        plugin_dir = tmp_plugins_dir / "bad_name"
        plugin_dir.mkdir()
        manifest = {
            "name": "",
            "version": "1.0",
            "description": "d",
            "author": "a",
            "entry": "plugin.py:X",
        }
        (plugin_dir / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
        (plugin_dir / "plugin.py").write_text("pass", encoding="utf-8")

        disc = PluginDiscovery(tmp_plugins_dir)

        assert "bad_name" not in disc.discover_plugins()

    def test_manifest_plugin_name_must_be_safe_identifier(self, tmp_plugins_dir):
        plugin_dir = tmp_plugins_dir / "bad_plugin_name"
        plugin_dir.mkdir()
        manifest = {
            "name": "bad-name",
            "version": "1.0",
            "description": "d",
            "author": "a",
            "entry": "plugin.py:X",
        }
        (plugin_dir / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
        (plugin_dir / "plugin.py").write_text("pass", encoding="utf-8")

        disc = PluginDiscovery(tmp_plugins_dir)

        assert "bad-name" not in disc.discover_plugins()

    def test_manifest_text_fields_are_trimmed(self, tmp_plugins_dir):
        plugin_dir = tmp_plugins_dir / "trimmed"
        plugin_dir.mkdir()
        manifest = {
            "name": " trimmed_tool ",
            "version": " 1.0 ",
            "description": " d ",
            "author": " a ",
            "entry": " plugin.py:X ",
            "sidebar_label": " Trimmed ",
        }
        (plugin_dir / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
        (plugin_dir / "plugin.py").write_text("pass", encoding="utf-8")

        disc = PluginDiscovery(tmp_plugins_dir)
        found = disc.discover_plugins()

        info = found["trimmed_tool"]
        assert info.version == "1.0"
        assert info.description == "d"
        assert info.author == "a"
        assert info.entry == "plugin.py:X"
        assert info.sidebar_label == "Trimmed"

    def test_manifest_optional_fields_have_strict_types(self, tmp_plugins_dir):
        plugin_dir = tmp_plugins_dir / "bad_enabled"
        plugin_dir.mkdir()
        manifest = {
            "name": "bad_enabled",
            "version": "1.0",
            "description": "d",
            "author": "a",
            "entry": "plugin.py:X",
            "enabled": "yes",
        }
        (plugin_dir / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
        (plugin_dir / "plugin.py").write_text("pass", encoding="utf-8")

        disc = PluginDiscovery(tmp_plugins_dir)

        assert "bad_enabled" not in disc.discover_plugins()

    def test_manifest_type_must_be_known_plugin_type(self, tmp_plugins_dir):
        plugin_dir = tmp_plugins_dir / "bad_type"
        plugin_dir.mkdir()
        manifest = {
            "name": "bad_type",
            "version": "1.0",
            "description": "d",
            "author": "a",
            "entry": "plugin.py:X",
            "type": "service",
        }
        (plugin_dir / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
        (plugin_dir / "plugin.py").write_text("pass", encoding="utf-8")

        disc = PluginDiscovery(tmp_plugins_dir)

        assert "bad_type" not in disc.discover_plugins()

    def test_duplicate_manifest_plugin_names_keep_first_discovered_plugin(self, tmp_plugins_dir):
        first_dir = tmp_plugins_dir / "aaa_first"
        second_dir = tmp_plugins_dir / "zzz_second"
        first_dir.mkdir()
        second_dir.mkdir()
        base_manifest = {
            "name": "shared_tool",
            "version": "1.0",
            "description": "d",
            "author": "a",
            "entry": "plugin.py:X",
        }
        first_manifest = dict(base_manifest, sidebar_label="First")
        second_manifest = dict(base_manifest, sidebar_label="Second")
        (first_dir / "manifest.json").write_text(json.dumps(first_manifest), encoding="utf-8")
        (second_dir / "manifest.json").write_text(json.dumps(second_manifest), encoding="utf-8")
        (first_dir / "plugin.py").write_text("pass", encoding="utf-8")
        (second_dir / "plugin.py").write_text("pass", encoding="utf-8")

        disc = PluginDiscovery(tmp_plugins_dir)
        found = disc.discover_plugins()

        assert found["shared_tool"].plugin_path == str(first_dir)
        assert found["shared_tool"].sidebar_label == "First"


# ---------------------------------------------------------------------------
# PluginRegistry tests
# ---------------------------------------------------------------------------

class TestPluginRegistry:
    def _make_plugin(self, name="test_plugin"):
        class P(PluginBase):
            def get_plugin_info(self_info):
                return PluginInfo(name=name, version="1.0", description="d", author="a")
            def initialize(self_info, deps=None):
                self_info._mark_initialized()
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

    def test_load_plugin_discovers_when_called_directly(self, gui_plugin_dir, tmp_plugins_dir):
        reset_plugin_manager()
        mgr = PluginManager(tmp_plugins_dir)
        assert mgr.load_plugin("my_gui_tool") is True
        assert mgr.get_plugin("my_gui_tool") is not None

    def test_load_hook_plugin(self, hook_plugin_file, tmp_plugins_dir):
        reset_plugin_manager()
        mgr = PluginManager(tmp_plugins_dir)
        results = mgr.load_all_plugins()
        assert results.get("my_hook") is True
        plugin = mgr.get_plugin("my_hook")
        assert plugin is not None
        assert plugin.plugin_info.plugin_type == "hook"

    def test_get_plugin_manager_reuses_same_directory(self, tmp_plugins_dir):
        reset_plugin_manager()
        first = get_plugin_manager(tmp_plugins_dir)
        second = get_plugin_manager(tmp_plugins_dir)
        assert second is first

    def test_get_plugin_manager_rebuilds_when_directory_changes(self, gui_plugin_dir, tmp_plugins_dir, tmp_path):
        reset_plugin_manager()
        first = get_plugin_manager(tmp_plugins_dir)
        first.load_all_plugins()
        module_name = first._loaded_module_names["my_gui_tool"]
        assert module_name in sys.modules

        other_dir = tmp_path / "other_plugins"
        other_dir.mkdir()
        second = get_plugin_manager(other_dir)

        assert second is not first
        assert second.plugins_dir == other_dir
        assert module_name not in sys.modules

    def test_load_with_disabled_names(self, gui_plugin_dir, tmp_plugins_dir):
        reset_plugin_manager()
        mgr = PluginManager(tmp_plugins_dir)
        results = mgr.load_all_plugins(disabled_names={"my_gui_tool"})
        assert results.get("my_gui_tool") is False
        assert mgr.get_plugin("my_gui_tool") is None

    def test_load_plugin_loads_dependencies_first(self, tmp_plugins_dir):
        dep_dir = tmp_plugins_dir / "dep_tool"
        dep_dir.mkdir()
        (dep_dir / "manifest.json").write_text(json.dumps({
            "name": "dep_tool", "version": "1.0", "description": "dep",
            "author": "Tester", "entry": "plugin.py:DepPlugin", "type": "hook",
            "priority": 0,
        }), encoding="utf-8")
        (dep_dir / "plugin.py").write_text(textwrap.dedent('''\
            from toolbox_app.plugins.base import PluginBase, PluginInfo
            class DepPlugin(PluginBase):
                def get_plugin_info(self):
                    return PluginInfo(name="dep_tool", version="1.0", description="dep", author="Tester", plugin_type="hook")
                def initialize(self, deps=None):
                    return True
                def cleanup(self):
                    pass
        '''), encoding="utf-8")
        main_dir = tmp_plugins_dir / "main_tool"
        main_dir.mkdir()
        (main_dir / "manifest.json").write_text(json.dumps({
            "name": "main_tool", "version": "1.0", "description": "main",
            "author": "Tester", "entry": "plugin.py:MainPlugin",
            "dependencies": ["dep_tool"], "priority": 10,
        }), encoding="utf-8")
        (main_dir / "plugin.py").write_text(textwrap.dedent('''\
            from toolbox_app.plugins.base import PluginBase, PluginInfo
            class MainPlugin(PluginBase):
                def get_plugin_info(self):
                    return PluginInfo(name="main_tool", version="1.0", description="main", author="Tester")
                def initialize(self, deps=None):
                    return True
                def cleanup(self):
                    pass
        '''), encoding="utf-8")

        reset_plugin_manager()
        mgr = PluginManager(tmp_plugins_dir)
        results = mgr.load_all_plugins()

        assert results["main_tool"] is True
        assert mgr.has_plugin("dep_tool") is True
        assert mgr.has_plugin("main_tool") is True

    def test_load_plugin_rejects_dependency_cycles(self, tmp_plugins_dir):
        for name, dep in [("first", "second"), ("second", "first")]:
            plugin_dir = tmp_plugins_dir / name
            plugin_dir.mkdir()
            (plugin_dir / "manifest.json").write_text(json.dumps({
                "name": name, "version": "1.0", "description": name,
                "author": "Tester", "entry": "plugin.py:CyclePlugin",
                "dependencies": [dep],
            }), encoding="utf-8")
            (plugin_dir / "plugin.py").write_text(textwrap.dedent(f'''\
                from toolbox_app.plugins.base import PluginBase, PluginInfo
                class CyclePlugin(PluginBase):
                    def get_plugin_info(self):
                        return PluginInfo(name="{name}", version="1.0", description="{name}", author="Tester")
                    def initialize(self, deps=None):
                        return True
                    def cleanup(self):
                        pass
            '''), encoding="utf-8")

        reset_plugin_manager()
        mgr = PluginManager(tmp_plugins_dir)
        results = mgr.load_all_plugins()

        assert "first" not in results
        assert "second" not in results
        assert mgr.get_plugin_count() == 0

    def test_repeated_load_all_plugins_is_idempotent(self, gui_plugin_dir, tmp_plugins_dir):
        reset_plugin_manager()
        mgr = PluginManager(tmp_plugins_dir)
        first = mgr.load_all_plugins()
        plugin = mgr.get_plugin("my_gui_tool")
        second = mgr.load_all_plugins()
        assert first.get("my_gui_tool") is True
        assert second.get("my_gui_tool") is True
        assert mgr.get_plugin("my_gui_tool") is plugin

    def test_real_plugin_converter_loads_on_first_command(self):
        reset_plugin_manager()
        mgr = PluginManager(ROOT / "plugins")
        assert mgr.load_plugin("json_tools") is True
        module = sys.modules[mgr._loaded_module_names["json_tools"]]
        lazy_converter = module._converter
        assert lazy_converter._module is None

        plugin = mgr.get_plugin("json_tools")
        assert plugin.handle_command("validate_json", text='{"a": 1}')["type"] == "dict"
        assert lazy_converter._module is not None

    def test_disabled_plugin_is_unregistered_on_reload(self, gui_plugin_dir, tmp_plugins_dir):
        reset_plugin_manager()
        mgr = PluginManager(tmp_plugins_dir)
        assert mgr.load_all_plugins().get("my_gui_tool") is True
        module_name = mgr._loaded_module_names["my_gui_tool"]
        assert module_name in sys.modules

        results = mgr.load_all_plugins(disabled_names={"my_gui_tool"})

        assert results.get("my_gui_tool") is False
        assert mgr.get_plugin("my_gui_tool") is None
        assert module_name not in sys.modules

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

    def test_cleanup_plugin_unregisters_and_unloads_module(self, gui_plugin_dir, tmp_plugins_dir):
        reset_plugin_manager()
        mgr = PluginManager(tmp_plugins_dir)
        mgr.load_all_plugins()
        module_name = mgr._loaded_module_names["my_gui_tool"]
        assert module_name in sys.modules

        assert mgr.cleanup_plugin("my_gui_tool") is True

        assert mgr.get_plugin("my_gui_tool") is None
        assert mgr.has_plugin("my_gui_tool") is False
        assert module_name not in sys.modules

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

    def test_invalid_plugin_missing_class_does_not_leave_module_loaded(self, tmp_plugins_dir):
        reset_plugin_manager()
        plugin_dir = tmp_plugins_dir / "missing_class"
        plugin_dir.mkdir()
        manifest = {
            "name": "missing_class",
            "version": "1.0",
            "description": "d",
            "author": "a",
            "entry": "plugin.py:MissingClass",
        }
        (plugin_dir / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
        (plugin_dir / "plugin.py").write_text(textwrap.dedent('''\
            from toolbox_app.plugins.base import PluginBase, PluginInfo

            class OtherPlugin(PluginBase):
                def get_plugin_info(self):
                    return PluginInfo(name="missing_class", version="1.0", description="d", author="a")
                def cleanup(self):
                    pass
        '''), encoding="utf-8")

        mgr = PluginManager(tmp_plugins_dir)
        results = mgr.load_all_plugins()

        assert results.get("missing_class") is False
        assert "plugin_missing_class" not in sys.modules

    def test_manifest_entry_class_must_extend_plugin_base_before_instantiation(self, tmp_plugins_dir, tmp_path):
        reset_plugin_manager()
        marker = tmp_path / "plain_class_instantiated.txt"
        plugin_dir = tmp_plugins_dir / "plain_class"
        plugin_dir.mkdir()
        manifest = {
            "name": "plain_class",
            "version": "1.0",
            "description": "d",
            "author": "a",
            "entry": "plugin.py:PlainClass",
        }
        (plugin_dir / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
        (plugin_dir / "plugin.py").write_text(textwrap.dedent(f'''\
            from pathlib import Path

            class PlainClass:
                def __init__(self):
                    Path({str(marker)!r}).write_text("created", encoding="utf-8")
        '''), encoding="utf-8")

        mgr = PluginManager(tmp_plugins_dir)
        results = mgr.load_all_plugins()

        assert results.get("plain_class") is False
        assert not marker.exists()
        assert "plugin_plain_class" not in sys.modules

    def test_manifest_entry_cannot_load_file_from_sibling_plugin_directory(self, tmp_plugins_dir):
        reset_plugin_manager()
        neighbor_dir = tmp_plugins_dir / "neighbor"
        neighbor_dir.mkdir()
        (neighbor_dir / "plugin.py").write_text(textwrap.dedent('''\
            from toolbox_app.plugins.base import PluginBase, PluginInfo

            class EscapePlugin(PluginBase):
                def get_plugin_info(self):
                    return PluginInfo(name="path_escape", version="1.0", description="d", author="a")
                def cleanup(self):
                    pass
        '''), encoding="utf-8")

        plugin_dir = tmp_plugins_dir / "path_escape"
        plugin_dir.mkdir()
        manifest = {
            "name": "path_escape",
            "version": "1.0",
            "description": "d",
            "author": "a",
            "entry": "../neighbor/plugin.py:EscapePlugin",
        }
        (plugin_dir / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")

        mgr = PluginManager(tmp_plugins_dir)

        assert mgr.load_plugin("path_escape") is False
        assert "plugin_path_escape" not in sys.modules

    def test_manifest_name_must_match_plugin_info_name(self, tmp_plugins_dir):
        reset_plugin_manager()
        plugin_dir = tmp_plugins_dir / "manifest_name"
        plugin_dir.mkdir()
        manifest = {
            "name": "manifest_name",
            "version": "1.0",
            "description": "d",
            "author": "a",
            "entry": "plugin.py:MismatchPlugin",
        }
        (plugin_dir / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
        (plugin_dir / "plugin.py").write_text(textwrap.dedent('''\
            from toolbox_app.plugins.base import PluginBase, PluginInfo

            class MismatchPlugin(PluginBase):
                def get_plugin_info(self):
                    return PluginInfo(name="code_name", version="1.0", description="d", author="a")
                def cleanup(self):
                    pass
        '''), encoding="utf-8")

        mgr = PluginManager(tmp_plugins_dir)

        assert mgr.load_plugin("manifest_name") is False
        assert mgr.get_plugin("manifest_name") is None
        assert mgr.get_plugin("code_name") is None
        assert "plugin_manifest_name" not in sys.modules

    def test_plugin_info_error_unloads_imported_module(self, tmp_plugins_dir):
        reset_plugin_manager()
        plugin_dir = tmp_plugins_dir / "bad_info"
        plugin_dir.mkdir()
        manifest = {
            "name": "bad_info",
            "version": "1.0",
            "description": "d",
            "author": "a",
            "entry": "plugin.py:BadInfoPlugin",
        }
        (plugin_dir / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
        (plugin_dir / "plugin.py").write_text(textwrap.dedent('''\
            from toolbox_app.plugins.base import PluginBase

            class BadInfoPlugin(PluginBase):
                def get_plugin_info(self):
                    raise RuntimeError("bad metadata")
                def cleanup(self):
                    pass
        '''), encoding="utf-8")

        mgr = PluginManager(tmp_plugins_dir)

        assert mgr.load_plugin("bad_info") is False
        assert mgr.get_plugin("bad_info") is None
        assert "plugin_bad_info" not in sys.modules

    def test_load_all_plugins_missing_dir_returns_empty(self, tmp_path):
        reset_plugin_manager()
        mgr = PluginManager(tmp_path / "missing_plugins")
        assert mgr.load_all_plugins() == {}

    def test_real_example_plugin_is_disabled_by_default(self):
        reset_plugin_manager()
        mgr = PluginManager(ROOT / "plugins")
        results = mgr.load_all_plugins()
        assert results.get("hello_world") is False
        assert mgr.get_plugin("hello_world") is None
        assert results.get("file_hasher") is True
        assert results.get("json_tools") is True
        assert results.get("timestamp_tools") is True
        assert results.get("url_tools") is True
        assert results.get("uuid_tools") is True
