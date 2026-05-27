from __future__ import annotations


class ToolboxError(Exception):
    """工具箱基础异常类"""

    def __init__(self, message: str, code: str = None):
        super().__init__(message)
        self.message = message
        self.code = code

    def __str__(self):
        if self.code:
            return f"[{self.code}] {self.message}"
        return self.message


class ServiceError(ToolboxError):
    """服务层异常"""

    def __init__(self, message: str, service: str = None, code: str = None):
        super().__init__(message, code)
        self.service = service

    def __str__(self):
        if self.service:
            return f"服务 {self.service}: {self.message}"
        return self.message


class ConfigError(ToolboxError):
    """配置相关异常"""

    def __init__(self, message: str, config_key: str = None, code: str = None):
        super().__init__(message, code)
        self.config_key = config_key

    def __str__(self):
        if self.config_key:
            return f"配置 {self.config_key}: {self.message}"
        return self.message


class ValidationError(ToolboxError):
    """数据验证异常"""

    def __init__(self, message: str, field: str = None, code: str = None):
        super().__init__(message, code)
        self.field = field

    def __str__(self):
        if self.field:
            return f"字段 {self.field}: {self.message}"
        return self.message


class ResourceError(ToolboxError):
    """资源相关异常"""

    def __init__(self, message: str, resource: str = None, code: str = None):
        super().__init__(message, code)
        self.resource = resource

    def __str__(self):
        if self.resource:
            return f"资源 {self.resource}: {self.message}"
        return self.message


class TaskError(ToolboxError):
    """任务相关异常"""

    def __init__(self, message: str, task_id: str = None, code: str = None):
        super().__init__(message, code)
        self.task_id = task_id

    def __str__(self):
        if self.task_id:
            return f"任务 {self.task_id}: {self.message}"
        return self.message


class PluginError(ToolboxError):
    """插件相关异常"""

    def __init__(self, message: str, plugin_name: str = None, code: str = None):
        super().__init__(message, code)
        self.plugin_name = plugin_name

    def __str__(self):
        if self.plugin_name:
            return f"插件 {self.plugin_name}: {self.message}"
        return self.message
