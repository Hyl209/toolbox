from __future__ import annotations

import pytest
import tempfile
from pathlib import Path
from unittest.mock import MagicMock

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


# 运行测试
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
