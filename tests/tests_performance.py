from __future__ import annotations

import pytest
import time
import tempfile
from pathlib import Path

try:
    import pytest_timeout  # noqa: F401
    _has_timeout = True
except ImportError:
    _has_timeout = False

timeout_10s = pytest.mark.timeout(10) if _has_timeout else lambda f: f

# 测试性能监控
@timeout_10s
class TestPerformance:
    """测试性能监控"""

    def test_performance_monitor(self):
        """测试性能监控器"""
        from toolbox_app.core.performance import PerformanceMonitor

        monitor = PerformanceMonitor()

        # 测试计时
        monitor.start_timer("test")
        time.sleep(0.1)
        elapsed = monitor.stop_timer("test")

        assert elapsed >= 0.1
        assert monitor.get_count("test") == 1
        assert monitor.get_average("test") >= 0.1

    def test_timer_decorator(self):
        """测试计时装饰器"""
        from toolbox_app.core.performance import timer, get_performance_monitor

        @timer("test_func")
        def test_func():
            time.sleep(0.1)
            return 42

        result = test_func()
        assert result == 42

        monitor = get_performance_monitor()
        assert monitor.get_count("test_func") == 1

    def test_memory_monitor(self):
        """测试内存监控器"""
        from toolbox_app.core.performance import MemoryMonitor

        monitor = MemoryMonitor()

        # 测试获取快照
        snapshot = monitor.take_snapshot("test")
        # psutil 可能未安装，所以 snapshot 可能为 None
        if snapshot is not None:
            assert 'rss' in snapshot
            assert 'vms' in snapshot

    def test_performance_stats(self):
        """测试性能统计"""
        from toolbox_app.core.performance import PerformanceMonitor

        monitor = PerformanceMonitor()

        # 多次计时
        for _ in range(5):
            monitor.start_timer("test")
            time.sleep(0.01)
            monitor.stop_timer("test")

        stats = monitor.get_stats("test")
        assert stats['count'] == 5
        assert stats['average'] >= 0.01
        assert stats['min'] >= 0.01
        assert stats['max'] >= 0.01


# 测试文件操作性能
class TestFilePerformance:
    """测试文件操作性能"""

    def test_file_utils_performance(self):
        """测试文件工具性能"""
        from toolbox_app.core.file_utils import file_utils
        from toolbox_app.core.performance import timer

        with tempfile.TemporaryDirectory() as tmp:
            # 测试批量写入性能
            @timer("batch_write")
            def batch_write():
                for i in range(100):
                    file_path = Path(tmp) / f"file_{i}.txt"
                    file_utils.write_text(file_path, f"content {i}")

            batch_write()

            # 测试批量读取性能
            @timer("batch_read")
            def batch_read():
                for i in range(100):
                    file_path = Path(tmp) / f"file_{i}.txt"
                    content = file_utils.read_text(file_path)
                    assert content == f"content {i}"

            batch_read()


# 测试任务框架性能
class TestTaskPerformance:
    """测试任务框架性能"""

    def test_task_queue_performance(self):
        """测试任务队列性能"""
        from toolbox_app.task_framework.queue import TaskQueue
        from toolbox_app.task_framework.task import Task
        from toolbox_app.core.performance import timer

        class SimpleTask(Task):
            def execute(self):
                return None

        @timer("queue_performance")
        def test_queue():
            queue = TaskQueue(max_workers=10)

            # 添加多个任务
            for i in range(50):
                task = SimpleTask(f"task_{i}")
                queue.add_task(task)

        test_queue()


# 测试配置性能
class TestConfigPerformance:
    """测试配置性能"""

    def test_config_performance(self):
        """测试配置性能"""
        from toolbox_app.core.config import ConfigManager
        from toolbox_app.core.performance import timer

        with tempfile.TemporaryDirectory() as tmp:
            manager = ConfigManager(tmp)

            @timer("config_operations")
            def test_config_ops():
                # 批量写入
                for i in range(100):
                    manager.set("test", f"key_{i}", f"value_{i}")

                # 批量读取
                for i in range(100):
                    value = manager.get("test", f"key_{i}")
                    assert value == f"value_{i}"

            test_config_ops()


# 运行测试
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
