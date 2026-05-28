from __future__ import annotations

import pytest
import tempfile
from pathlib import Path
from unittest.mock import MagicMock

# 如果安装了 pytest-timeout，为含 time.sleep 的测试类加超时保护
try:
    import pytest_timeout  # noqa: F401
    _has_timeout = True
except ImportError:
    _has_timeout = False

timeout_10s = pytest.mark.timeout(10) if _has_timeout else lambda f: f

# 测试 core 模块
class TestCoreModules:
    """测试核心模块"""

    def test_logger_setup(self):
        """测试日志设置"""
        from toolbox_app.core.logger import setup_logger, get_logger

        # 测试设置日志
        with tempfile.TemporaryDirectory() as tmp:
            manager = setup_logger(tmp)
            assert manager is not None

            # 测试获取日志记录器
            logger = get_logger("test")
            assert logger is not None

    def test_config_manager(self):
        """测试配置管理器"""
        from toolbox_app.core.config import ConfigManager

        with tempfile.TemporaryDirectory() as tmp:
            manager = ConfigManager(tmp)

            # 测试获取配置
            value = manager.get("app", "version")
            assert value is not None

            # 测试设置配置
            manager.set("app", "test_key", "test_value")
            assert manager.get("app", "test_key") == "test_value"

    def test_path_manager(self):
        """测试路径管理器"""
        from toolbox_app.core.paths import PathManager

        manager = PathManager()

        # 测试路径属性
        assert manager.base_dir is not None
        assert manager.resource_dir is not None
        assert manager.temp_dir is not None
        assert manager.log_dir is not None
        assert manager.config_dir is not None

    def test_exceptions(self):
        """测试异常类"""
        from toolbox_app.core.exceptions import (
            ToolboxError, ServiceError, ConfigError,
            ValidationError, ResourceError, TaskError, PluginError
        )

        # 测试基础异常
        error = ToolboxError("test error", "TEST001")
        assert str(error) == "[TEST001] test error"

        # 测试服务异常
        error = ServiceError("service error", "TestService")
        assert "TestService" in str(error)

        # 测试配置异常
        error = ConfigError("config error", "test_key")
        assert "test_key" in str(error)

    def test_worker(self):
        """测试 Worker"""
        from toolbox_app.core.worker import Worker

        worker = Worker()

        # 测试执行任务
        result = worker.execute(lambda: 42)
        assert result == 42
        assert worker.is_running is False

    def test_task_manager(self):
        """测试任务管理器"""
        from toolbox_app.core.task_manager import TaskManager

        manager = TaskManager()

        # 测试提交任务
        def test_task():
            return 42

        worker = manager.execute_task("test", test_task)
        assert worker is not None

    def test_file_utils(self):
        """测试文件工具"""
        from toolbox_app.core.file_utils import file_utils

        with tempfile.TemporaryDirectory() as tmp:
            # 测试创建目录
            test_dir = Path(tmp) / "test_dir"
            file_utils.ensure_dir(test_dir)
            assert test_dir.exists()

            # 测试写入文件
            test_file = test_dir / "test.txt"
            assert file_utils.write_text(test_file, "test content") is True
            assert test_file.exists()

            # 测试读取文件
            content = file_utils.read_text(test_file)
            assert content == "test content"

    def test_events(self):
        """测试事件系统"""
        from toolbox_app.core.events import EventSystem, Event

        system = EventSystem()

        # 测试事件订阅
        received_events = []

        def handler(event: Event):
            received_events.append(event)

        system.on("test_event", handler)

        # 测试触发事件
        system.emit("test_event", {"data": "test"})
        assert len(received_events) == 1

    def test_ui_helpers(self):
        """测试 UI 辅助工具"""
        from toolbox_app.core.ui_helpers import ui_helpers

        # 测试静态方法
        assert hasattr(ui_helpers, 'show_message_box')
        assert hasattr(ui_helpers, 'show_confirmation')
        assert hasattr(ui_helpers, 'show_file_dialog')


# 测试 task_framework 模块
class TestTaskFramework:
    """测试任务框架"""

    def test_task_base(self):
        """测试任务基类"""
        from toolbox_app.task_framework.task import Task, TaskStatus

        class TestTask(Task):
            def execute(self):
                return "test result"

        task = TestTask("test_task")
        assert task.name == "test_task"
        assert task.status == TaskStatus.PENDING

        # 测试执行任务
        result = task.run()
        assert result == "test result"
        assert task.status == TaskStatus.COMPLETED

    def test_task_signals(self):
        """测试任务信号"""
        from toolbox_app.task_framework.signals import TaskSignals

        signals = TaskSignals()

        # 测试信号连接
        received = []
        signals.task_started.connect(lambda t: received.append(t))

        # 测试信号发射
        mock_task = MagicMock()
        signals.task_started.emit(mock_task)
        assert len(received) == 1

    def test_task_queue(self):
        """测试任务队列"""
        from toolbox_app.task_framework.queue import TaskQueue
        from toolbox_app.task_framework.task import Task

        class SimpleTask(Task):
            def execute(self):
                return None

        queue = TaskQueue(max_workers=2)

        # 测试添加任务
        task1 = SimpleTask("task1")
        task2 = SimpleTask("task2")

        queue.add_task(task1)
        queue.add_task(task2)

    def test_task_manager(self):
        """测试任务管理器"""
        from toolbox_app.task_framework.manager import TaskManager

        manager = TaskManager()

        # 测试提交任务
        def test_func():
            return 42

        task = manager.submit(test_func, name="test")
        assert task is not None


# 测试 services 模块
class TestServices:
    """测试服务层"""

    def test_pdf_service(self):
        """测试 PDF 服务"""
        from toolbox_app.services.pdf_service import PDFService

        service = PDFService()
        assert service is not None

    def test_video_service(self):
        """测试视频服务"""
        from toolbox_app.services.video_service import VideoService

        service = VideoService()
        assert service is not None

    def test_image_service(self):
        """测试图片服务"""
        from toolbox_app.services.image_service import ImageService

        service = ImageService()
        assert service is not None

    def test_download_service(self):
        """测试下载服务"""
        from toolbox_app.services.download_service import DownloadService

        service = DownloadService()
        assert service is not None
        assert service.name == "HTTPDownloader"

    def test_file_service(self):
        """测试文件服务"""
        from toolbox_app.services.file_service import FileService

        service = FileService()
        assert service is not None


# 测试 plugins 模块
class TestPlugins:
    """测试插件系统"""

    def test_plugin_base(self):
        """测试插件基类"""
        from toolbox_app.plugins.base import PluginBase, PluginInfo

        class TestPlugin(PluginBase):
            def get_plugin_info(self):
                return PluginInfo(
                    name="test_plugin",
                    version="1.0.0",
                    description="Test plugin",
                    author="Test"
                )

            def initialize(self):
                return True

            def cleanup(self):
                pass

        plugin = TestPlugin()
        assert plugin.name == "test_plugin"
        assert plugin.version == "1.0.0"

    def test_plugin_registry(self):
        """测试插件注册"""
        from toolbox_app.plugins.registry import PluginRegistry
        from toolbox_app.plugins.base import PluginBase, PluginInfo

        class TestPlugin(PluginBase):
            def get_plugin_info(self):
                return PluginInfo(
                    name="test_plugin",
                    version="1.0.0",
                    description="Test plugin",
                    author="Test"
                )

            def initialize(self):
                return True

            def cleanup(self):
                pass

        registry = PluginRegistry()
        plugin = TestPlugin()

        # 测试注册插件
        assert registry.register(plugin) is True
        assert registry.has_plugin("test_plugin") is True

    def test_plugin_discovery(self):
        """测试插件发现"""
        from toolbox_app.plugins.discovery import PluginDiscovery

        discovery = PluginDiscovery()
        assert discovery is not None

    def test_plugin_manager(self):
        """测试插件管理器"""
        from toolbox_app.plugins.manager import PluginManager

        manager = PluginManager()
        assert manager is not None


# =========================================================================
# Edge-case 测试
# =========================================================================
class TestConfigManagerEdgeCases:
    """ConfigManager 边界测试"""

    def test_empty_config_dir_returns_defaults(self):
        from toolbox_app.core.config import ConfigManager
        with tempfile.TemporaryDirectory() as tmp:
            manager = ConfigManager(tmp)
            assert manager.get("app", "version") == "1.0.0"
            assert manager.get("app", "theme") == "dark"

    def test_corrupted_json_handled_gracefully(self):
        from toolbox_app.core.config import ConfigManager
        with tempfile.TemporaryDirectory() as tmp:
            cfg_file = Path(tmp) / "app.json"
            cfg_file.write_text("{bad json!!", encoding="utf-8")
            manager = ConfigManager(tmp)
            # 应该回退到默认配置
            assert manager.get("app", "version") == "1.0.0"

    def test_nonexistent_key_returns_none(self):
        from toolbox_app.core.config import ConfigManager
        with tempfile.TemporaryDirectory() as tmp:
            manager = ConfigManager(tmp)
            assert manager.get("app", "nonexistent_key") is None

    def test_nonexistent_key_with_default(self):
        from toolbox_app.core.config import ConfigManager
        with tempfile.TemporaryDirectory() as tmp:
            manager = ConfigManager(tmp)
            assert manager.get("app", "missing", "fallback") == "fallback"

    def test_nonexistent_config_name_returns_empty(self):
        from toolbox_app.core.config import ConfigManager
        with tempfile.TemporaryDirectory() as tmp:
            manager = ConfigManager(tmp)
            assert manager.get("no_such_config", "key") is None

    def test_set_and_reload(self):
        from toolbox_app.core.config import ConfigManager
        with tempfile.TemporaryDirectory() as tmp:
            manager = ConfigManager(tmp)
            manager.set("app", "custom", 42)
            assert manager.get("app", "custom") == 42
            manager.reload("app")
            assert manager.get("app", "custom") == 42

    def test_update_batch(self):
        from toolbox_app.core.config import ConfigManager
        with tempfile.TemporaryDirectory() as tmp:
            manager = ConfigManager(tmp)
            manager.update("app", {"k1": "v1", "k2": "v2"})
            assert manager.get("app", "k1") == "v1"
            assert manager.get("app", "k2") == "v2"

    def test_get_all_returns_copy(self):
        from toolbox_app.core.config import ConfigManager
        with tempfile.TemporaryDirectory() as tmp:
            manager = ConfigManager(tmp)
            all_cfg = manager.get_all("app")
            all_cfg["injected"] = True
            assert manager.get("app", "injected") is None


class TestFileUtilsEdgeCases:
    """FileUtils 边界测试"""

    def test_read_empty_file(self):
        from toolbox_app.core.file_utils import FileUtils
        with tempfile.TemporaryDirectory() as tmp:
            f = Path(tmp) / "empty.txt"
            f.write_text("", encoding="utf-8")
            assert FileUtils.read_text(f) == ""
            assert FileUtils.get_file_size(f) == 0

    def test_write_and_read_special_chars(self):
        from toolbox_app.core.file_utils import FileUtils
        with tempfile.TemporaryDirectory() as tmp:
            f = Path(tmp) / "special.txt"
            content = "中文\n日本語\n한국어\némojis 🎵"
            assert FileUtils.write_text(f, content) is True
            assert FileUtils.read_text(f) == content

    def test_resolve_name_conflict_no_conflict(self):
        from toolbox_app.core.file_utils import FileUtils
        with tempfile.TemporaryDirectory() as tmp:
            f = Path(tmp) / "unique.txt"
            assert FileUtils.resolve_name_conflict(f) == f

    def test_resolve_name_conflict_with_existing(self):
        from toolbox_app.core.file_utils import FileUtils
        with tempfile.TemporaryDirectory() as tmp:
            f = Path(tmp) / "test.txt"
            f.write_text("x", encoding="utf-8")
            resolved = FileUtils.resolve_name_conflict(f)
            assert resolved != f
            assert "(1)" in resolved.name

    def test_safe_delete_nonexistent(self):
        from toolbox_app.core.file_utils import FileUtils
        result = FileUtils.safe_delete("/nonexistent/path/xyz")
        assert result is True  # safe_delete returns True even if not exists

    def test_safe_copy_src_not_exist(self):
        from toolbox_app.core.file_utils import FileUtils
        result = FileUtils.safe_copy("/nonexistent/src", "/tmp/dst")
        assert result is False

    def test_safe_copy_no_overwrite(self):
        from toolbox_app.core.file_utils import FileUtils
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp) / "src.txt"
            dst = Path(tmp) / "dst.txt"
            src.write_text("a", encoding="utf-8")
            dst.write_text("b", encoding="utf-8")
            result = FileUtils.safe_copy(src, dst, overwrite=False)
            assert result is False

    def test_safe_move_src_not_exist(self):
        from toolbox_app.core.file_utils import FileUtils
        result = FileUtils.safe_move("/nonexistent/src", "/tmp/dst")
        assert result is False

    def test_get_file_extension(self):
        from toolbox_app.core.file_utils import FileUtils
        assert FileUtils.get_file_extension("photo.JPG") == ".jpg"
        assert FileUtils.get_file_extension("noext") == ""

    def test_format_size(self):
        from toolbox_app.core.file_utils import FileUtils
        assert "B" in FileUtils.format_size(500)
        assert "KB" in FileUtils.format_size(2048)
        assert "MB" in FileUtils.format_size(5 * 1024 * 1024)
        assert "GB" in FileUtils.format_size(3 * 1024 * 1024 * 1024)

    def test_list_files_empty_dir(self):
        from toolbox_app.core.file_utils import FileUtils
        with tempfile.TemporaryDirectory() as tmp:
            assert FileUtils.list_files(tmp) == []

    def test_get_directory_size(self):
        from toolbox_app.core.file_utils import FileUtils
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "a.bin").write_bytes(b"x" * 100)
            (Path(tmp) / "b.bin").write_bytes(b"y" * 200)
            assert FileUtils.get_directory_size(tmp) == 300


@timeout_10s
class TestTaskManagerEdgeCases:
    """TaskManager 边界测试"""

    def test_cancel_task(self):
        from toolbox_app.core.task_manager import TaskManager
        manager = TaskManager()
        worker = manager.execute_task("cancel_test", lambda: 42)
        import time
        time.sleep(0.1)
        worker.cancel()
        assert worker.is_cancelled is True

    def test_duplicate_task_id_raises(self):
        from toolbox_app.core.task_manager import TaskManager
        from toolbox_app.core.exceptions import TaskError
        manager = TaskManager()
        manager.create_worker("dup_id")
        with pytest.raises(TaskError):
            manager.create_worker("dup_id")

    def test_remove_worker(self):
        from toolbox_app.core.task_manager import TaskManager
        manager = TaskManager()
        manager.create_worker("to_remove")
        assert manager.remove_worker("to_remove") is True
        assert manager.get_worker("to_remove") is None

    def test_remove_nonexistent_worker(self):
        from toolbox_app.core.task_manager import TaskManager
        manager = TaskManager()
        assert manager.remove_worker("nope") is False

    def test_get_task_status(self):
        from toolbox_app.core.task_manager import TaskManager
        manager = TaskManager()
        worker = manager.execute_task("status_test", lambda: 99)
        import time
        time.sleep(0.1)
        status = manager.get_task_status("status_test")
        assert status is not None
        assert status["task_id"] == "status_test"

    def test_get_task_status_nonexistent(self):
        from toolbox_app.core.task_manager import TaskManager
        manager = TaskManager()
        assert manager.get_task_status("nope") is None

    def test_cancel_all(self):
        from toolbox_app.core.task_manager import TaskManager
        manager = TaskManager()
        manager.execute_task("t1", lambda: 1)
        manager.execute_task("t2", lambda: 2)
        manager.cancel_all()
        # 队列应该被清空
        assert manager.get_queued_tasks() == []

    def test_cleanup_completed(self):
        from toolbox_app.core.task_manager import TaskManager
        manager = TaskManager()
        worker = manager.execute_task("cleanup_test", lambda: 42)
        import time
        time.sleep(0.2)
        manager.cleanup_completed()
        assert manager.get_worker("cleanup_test") is None


class TestEventSystemEdgeCases:
    """EventSystem 边界测试"""

    def test_emit_with_no_listeners(self):
        from toolbox_app.core.events import EventSystem
        system = EventSystem()
        event = system.emit("no_one_listening", {"data": 1})
        assert event.name == "no_one_listening"
        assert event.data == {"data": 1}

    def test_listener_exception_does_not_propagate(self):
        from toolbox_app.core.events import EventSystem
        system = EventSystem()

        def bad_handler(event):
            raise ValueError("boom")

        def good_handler(event):
            good_handler.called = True
        good_handler.called = False

        system.on("evt", bad_handler)
        system.on("evt", good_handler)
        system.emit("evt")
        # good_handler 仍然应该被调用
        assert good_handler.called is True

    def test_nested_event_emit(self):
        from toolbox_app.core.events import EventSystem
        system = EventSystem()
        call_order = []

        def outer_handler(event):
            call_order.append("outer")
            system.emit("inner_event")

        def inner_handler(event):
            call_order.append("inner")

        system.on("outer_event", outer_handler)
        system.on("inner_event", inner_handler)
        system.emit("outer_event")
        assert call_order == ["outer", "inner"]

    def test_once_listener_fires_only_once(self):
        from toolbox_app.core.events import EventSystem
        system = EventSystem()
        count = {"n": 0}

        def handler(event):
            count["n"] += 1

        system.once("evt", handler)
        system.emit("evt")
        system.emit("evt")
        assert count["n"] == 1

    def test_off_specific_callback(self):
        from toolbox_app.core.events import EventSystem
        system = EventSystem()
        count = {"n": 0}

        def handler(event):
            count["n"] += 1

        system.on("evt", handler)
        system.emit("evt")
        system.off("evt", handler)
        system.emit("evt")
        assert count["n"] == 1

    def test_off_all_callbacks(self):
        from toolbox_app.core.events import EventSystem
        system = EventSystem()
        count = {"n": 0}

        def handler(event):
            count["n"] += 1

        system.on("evt", handler)
        system.off("evt")
        system.emit("evt")
        assert count["n"] == 0

    def test_event_stop_propagation(self):
        from toolbox_app.core.events import EventSystem
        system = EventSystem()
        call_order = []

        def first(event):
            call_order.append("first")
            event.stop()

        def second(event):
            call_order.append("second")

        system.on("evt", first)
        system.on("evt", second)
        system.emit("evt")
        assert call_order == ["first"]

    def test_has_listeners(self):
        from toolbox_app.core.events import EventSystem
        system = EventSystem()
        assert system.has_listeners("evt") is False
        system.on("evt", lambda e: None)
        assert system.has_listeners("evt") is True

    def test_clear(self):
        from toolbox_app.core.events import EventSystem
        system = EventSystem()
        system.on("a", lambda e: None)
        system.on("b", lambda e: None)
        system.clear()
        assert system.has_listeners("a") is False
        assert system.has_listeners("b") is False


class TestWorkerEdgeCases:
    """Worker 边界测试"""

    def test_worker_callbacks(self):
        from toolbox_app.core.worker import Worker
        worker = Worker()
        results = {"progress": [], "completed": None, "error": None, "cancelled": False}

        worker.on_progress(lambda p: results["progress"].append(p))
        worker.on_completed(lambda r: results.__setitem__("completed", r))
        worker.on_error(lambda e: results.__setitem__("error", e))
        worker.on_cancelled(lambda: results.__setitem__("cancelled", True))

        worker.execute(lambda: 42)
        assert results["completed"] == 42
        assert results["cancelled"] is False

    def test_worker_execute_raises(self):
        from toolbox_app.core.worker import Worker
        worker = Worker()
        error_caught = {"value": None}
        worker.on_error(lambda e: error_caught.__setitem__("value", e))

        with pytest.raises(ValueError):
            worker.execute(lambda: (_ for _ in ()).throw(ValueError("fail")))
        assert error_caught["value"] is not None

    def test_worker_cancel_triggers_callback(self):
        from toolbox_app.core.worker import Worker
        worker = Worker()
        cancelled = {"flag": False}
        worker.on_cancelled(lambda: cancelled.__setitem__("flag", True))
        worker.cancel()
        assert cancelled["flag"] is True
        assert worker.is_cancelled is True


# =========================================================================
# 插件系统测试
# =========================================================================
class TestPluginRegistryEdgeCases:
    """PluginRegistry 边界测试"""

    def _make_plugin(self, name="test_plugin", version="1.0.0"):
        from toolbox_app.plugins.base import PluginBase, PluginInfo

        class _Plugin(PluginBase):
            def get_plugin_info(self):
                return PluginInfo(name=name, version=version, description="desc", author="auth")
            def initialize(self, deps=None):
                self._is_initialized = True
                return True
            def cleanup(self):
                pass
        return _Plugin()

    def test_register_and_unregister(self):
        from toolbox_app.plugins.registry import PluginRegistry
        registry = PluginRegistry()
        plugin = self._make_plugin()
        assert registry.register(plugin) is True
        assert registry.has_plugin("test_plugin") is True
        assert registry.unregister("test_plugin") is True
        assert registry.has_plugin("test_plugin") is False

    def test_duplicate_register_returns_false(self):
        from toolbox_app.plugins.registry import PluginRegistry
        registry = PluginRegistry()
        p1 = self._make_plugin()
        p2 = self._make_plugin()
        assert registry.register(p1) is True
        assert registry.register(p2) is False

    def test_unregister_nonexistent(self):
        from toolbox_app.plugins.registry import PluginRegistry
        registry = PluginRegistry()
        assert registry.unregister("nope") is False

    def test_enable_disable_plugin(self):
        from toolbox_app.plugins.registry import PluginRegistry
        registry = PluginRegistry()
        plugin = self._make_plugin()
        registry.register(plugin)
        assert registry.disable_plugin("test_plugin") is True
        assert plugin.is_enabled is False
        assert registry.enable_plugin("test_plugin") is True
        assert plugin.is_enabled is True

    def test_enable_disable_nonexistent(self):
        from toolbox_app.plugins.registry import PluginRegistry
        registry = PluginRegistry()
        assert registry.enable_plugin("nope") is False
        assert registry.disable_plugin("nope") is False

    def test_initialize_plugin(self):
        from toolbox_app.plugins.registry import PluginRegistry
        registry = PluginRegistry()
        plugin = self._make_plugin()
        registry.register(plugin)
        assert registry.initialize_plugin("test_plugin") is True
        assert plugin.is_initialized is True

    def test_initialize_nonexistent(self):
        from toolbox_app.plugins.registry import PluginRegistry
        registry = PluginRegistry()
        assert registry.initialize_plugin("nope") is False

    def test_get_plugin_count(self):
        from toolbox_app.plugins.registry import PluginRegistry
        registry = PluginRegistry()
        assert registry.get_plugin_count() == 0
        registry.register(self._make_plugin("p1"))
        registry.register(self._make_plugin("p2"))
        assert registry.get_plugin_count() == 2

    def test_get_enabled_plugins(self):
        from toolbox_app.plugins.registry import PluginRegistry
        registry = PluginRegistry()
        p1 = self._make_plugin("p1")
        p2 = self._make_plugin("p2")
        registry.register(p1)
        registry.register(p2)
        registry.disable_plugin("p2")
        enabled = registry.get_enabled_plugins()
        assert "p1" in enabled
        assert "p2" not in enabled


class TestPluginDiscoveryEdgeCases:
    """PluginDiscovery 边界测试"""

    def test_discover_empty_directory(self):
        from toolbox_app.plugins.discovery import PluginDiscovery
        with tempfile.TemporaryDirectory() as tmp:
            discovery = PluginDiscovery(tmp)
            result = discovery.discover_plugins()
            assert result == {}

    def test_discover_invalid_manifest(self):
        from toolbox_app.plugins.discovery import PluginDiscovery
        with tempfile.TemporaryDirectory() as tmp:
            plugin_dir = Path(tmp) / "bad_plugin"
            plugin_dir.mkdir()
            manifest = plugin_dir / "manifest.json"
            manifest.write_text('{"name": "bad"}', encoding="utf-8")  # 缺少必需字段
            discovery = PluginDiscovery(tmp)
            result = discovery.discover_plugins()
            # 应该跳过无效 manifest，不崩溃
            assert isinstance(result, dict)

    def test_discover_corrupted_manifest(self):
        from toolbox_app.plugins.discovery import PluginDiscovery
        with tempfile.TemporaryDirectory() as tmp:
            plugin_dir = Path(tmp) / "corrupt"
            plugin_dir.mkdir()
            manifest = plugin_dir / "manifest.json"
            manifest.write_text("{not json!!!", encoding="utf-8")
            discovery = PluginDiscovery(tmp)
            result = discovery.discover_plugins()
            assert isinstance(result, dict)

    def test_get_plugin_info_not_found(self):
        from toolbox_app.plugins.discovery import PluginDiscovery
        with tempfile.TemporaryDirectory() as tmp:
            discovery = PluginDiscovery(tmp)
            discovery.discover_plugins()
            assert discovery.get_plugin_info("nonexistent") is None

    def test_validate_plugin_not_found(self):
        from toolbox_app.plugins.discovery import PluginDiscovery
        with tempfile.TemporaryDirectory() as tmp:
            discovery = PluginDiscovery(tmp)
            discovery.discover_plugins()
            assert discovery.validate_plugin("nonexistent") is False

    def test_discover_valid_manifest(self):
        from toolbox_app.plugins.discovery import PluginDiscovery
        with tempfile.TemporaryDirectory() as tmp:
            plugin_dir = Path(tmp) / "good_plugin"
            plugin_dir.mkdir()
            manifest = plugin_dir / "manifest.json"
            manifest.write_text(
                '{"name": "good", "version": "1.0", "description": "ok", "author": "me", "entry": "main.py"}',
                encoding="utf-8"
            )
            discovery = PluginDiscovery(tmp)
            result = discovery.discover_plugins()
            assert "good" in result
            assert result["good"].version == "1.0"


# =========================================================================
# 回归测试
# =========================================================================
@timeout_10s
class TestRegression:
    """回归测试 — 验证核心功能不退化"""

    def test_logger_singleton(self):
        """验证 logger 管理器是单例"""
        from toolbox_app.core.logger import setup_logger, get_logger
        import toolbox_app.core.logger as _mod
        import logging

        old = _mod._logger_manager
        _mod._logger_manager = None
        try:
            with tempfile.TemporaryDirectory() as tmp:
                mgr1 = setup_logger(tmp)
                mgr2 = setup_logger(tmp)
                assert mgr1 is mgr2
                logger_a = get_logger("singleton_test")
                logger_b = get_logger("singleton_test")
                assert logger_a is logger_b
                # 关闭所有 handler 释放文件锁（Windows 需要）
                root = logging.getLogger()
                for h in root.handlers[:]:
                    h.close()
                    root.removeHandler(h)
        finally:
            _mod._logger_manager = old

    def test_config_persistence(self):
        """验证配置写入后能读回"""
        from toolbox_app.core.config import ConfigManager
        with tempfile.TemporaryDirectory() as tmp:
            mgr = ConfigManager(tmp)
            mgr.set("app", "regression_key", "regression_value")
            # 新实例应能读回
            mgr2 = ConfigManager(tmp)
            assert mgr2.get("app", "regression_key") == "regression_value"

    def test_event_system_no_leak(self):
        """验证事件系统 off/clear 后不泄漏监听器"""
        from toolbox_app.core.events import EventSystem
        system = EventSystem()
        for i in range(100):
            system.on("leak_test", lambda e: None)
        assert system.has_listeners("leak_test") is True
        system.clear()
        assert system.has_listeners("leak_test") is False
        assert system._listeners.get("leak_test", []) == []

    def test_task_manager_cleanup(self):
        """验证任务管理器清理已完成任务"""
        from toolbox_app.core.task_manager import TaskManager
        import time

        manager = TaskManager()
        worker = manager.execute_task("regression_cleanup", lambda: 99)
        time.sleep(0.2)
        assert manager.get_worker("regression_cleanup") is not None
        manager.cleanup_completed()
        assert manager.get_worker("regression_cleanup") is None


class TestTaskFrameworkRegression:
    """Task framework regression tests — cancel, failure, concurrency."""

    def test_submit_and_complete(self):
        from toolbox_app.task_framework.manager import TaskManager
        import time

        manager = TaskManager(max_workers=2)
        results = []

        def work(x):
            time.sleep(0.05)
            return x * 2

        task = manager.submit(work, 5, name="double")
        time.sleep(0.3)
        assert task.result == 10
        assert task.status.name == 'COMPLETED'

    def test_submit_failure(self):
        from toolbox_app.task_framework.manager import TaskManager
        import time

        manager = TaskManager(max_workers=2)

        def fail():
            raise ValueError("boom")

        task = manager.submit(fail, name="fail_task")
        time.sleep(0.3)
        assert task.error is not None
        assert "boom" in str(task.error)

    def test_concurrency_limit(self):
        from toolbox_app.task_framework.manager import TaskManager
        import time

        manager = TaskManager(max_workers=1)
        running = []

        def slow(n):
            running.append(n)
            time.sleep(0.1)
            running.remove(n)
            return n

        tasks = [manager.submit(slow, i, name=f"task_{i}") for i in range(3)]
        time.sleep(0.05)
        # With max_workers=1, only 1 should be running at a time
        assert len(running) <= 1
        time.sleep(0.5)
        # All should eventually complete
        assert all(t.result is not None for t in tasks)

    def test_queue_history(self):
        from toolbox_app.task_framework.manager import TaskManager
        import time

        manager = TaskManager(max_workers=2)
        manager.submit(lambda: 1, name="h1")
        manager.submit(lambda: 2, name="h2")
        time.sleep(0.3)
        assert len(manager._task_history) == 2


# 运行测试
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
