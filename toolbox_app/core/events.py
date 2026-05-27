from __future__ import annotations

from typing import Any, Callable
from .logger import get_logger

logger = get_logger(__name__)


class Event:
    """事件对象"""

    def __init__(self, name: str, data: Any = None):
        self.name = name
        self.data = data
        self._stopped = False

    def stop(self):
        """停止事件传播"""
        self._stopped = True

    @property
    def is_stopped(self) -> bool:
        return self._stopped


class EventSystem:
    """事件系统"""

    def __init__(self):
        self._listeners: dict[str, list[Callable[[Event], None]]] = {}
        self._once_listeners: dict[str, list[Callable[[Event], None]]] = {}

    def on(self, event_name: str, callback: Callable[[Event], None]):
        """注册事件监听器"""
        if event_name not in self._listeners:
            self._listeners[event_name] = []
        self._listeners[event_name].append(callback)

    def once(self, event_name: str, callback: Callable[[Event], None]):
        """注册一次性事件监听器"""
        if event_name not in self._once_listeners:
            self._once_listeners[event_name] = []
        self._once_listeners[event_name].append(callback)

    def off(self, event_name: str, callback: Callable[[Event], None] = None):
        """移除事件监听器"""
        if callback is None:
            # 移除所有监听器
            self._listeners.pop(event_name, None)
            self._once_listeners.pop(event_name, None)
        else:
            # 移除指定监听器
            if event_name in self._listeners:
                self._listeners[event_name] = [
                    cb for cb in self._listeners[event_name] if cb != callback
                ]
            if event_name in self._once_listeners:
                self._once_listeners[event_name] = [
                    cb for cb in self._once_listeners[event_name] if cb != callback
                ]

    def emit(self, event_name: str, data: Any = None) -> Event:
        """触发事件"""
        event = Event(event_name, data)

        # 执行普通监听器
        for callback in self._listeners.get(event_name, []):
            if event.is_stopped:
                break
            try:
                callback(event)
            except Exception as e:
                logger.error(f"事件监听器执行失败 {event_name}: {e}")

        # 执行一次性监听器
        for callback in self._once_listeners.get(event_name, []):
            if event.is_stopped:
                break
            try:
                callback(event)
            except Exception as e:
                logger.error(f"一次性事件监听器执行失败 {event_name}: {e}")

        # 清空一次性监听器
        self._once_listeners.pop(event_name, None)

        return event

    def has_listeners(self, event_name: str) -> bool:
        """检查是否有监听器"""
        return bool(
            self._listeners.get(event_name) or
            self._once_listeners.get(event_name)
        )

    def clear(self):
        """清空所有监听器"""
        self._listeners.clear()
        self._once_listeners.clear()


# 全局事件系统实例
_event_system: EventSystem = None


def get_event_system() -> EventSystem:
    """获取全局事件系统实例"""
    global _event_system
    if _event_system is None:
        _event_system = EventSystem()
    return _event_system
