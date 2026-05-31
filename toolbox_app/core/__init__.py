"""core 包 — 延迟加载子模块，避免启动时全部导入"""
import importlib as _importlib

_LAZY_IMPORTS = {
    'setup_logger': '.logger',
    'get_logger': '.logger',
    'ConfigManager': 'config.manager',
    'PathManager': '.paths',
    'ToolboxError': '.exceptions',
    'ServiceError': '.exceptions',
    'Worker': '.worker',
    'TaskManager': 'toolbox_app.task_framework.manager',
    'file_utils': '.file_utils',
    'DownloaderBase': '.downloader_base',
    'EventSystem': '.events',
    'ui_helpers': '.ui_helpers',
    'GPUManager': '.gpu_manager',
    'CrashRecoveryManager': '.crash_recovery',
}

__all__ = list(_LAZY_IMPORTS)


def __getattr__(name: str):
    if name in _LAZY_IMPORTS:
        module_path = _LAZY_IMPORTS[name]
        mod = _importlib.import_module(module_path, __name__)
        val = getattr(mod, name)
        globals()[name] = val
        return val
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
