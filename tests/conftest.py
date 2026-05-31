import pytest
from pathlib import Path
from toolbox_app.plugins.manager import PluginManager, reset_plugin_manager

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="session")
def shared_plugin_manager():
    """Session-scoped plugin manager that loads all plugins once."""
    reset_plugin_manager()
    mgr = PluginManager(ROOT / "plugins")
    mgr.discover_plugins()
    mgr.load_all_plugins()
    yield mgr
