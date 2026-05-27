from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from threading import RLock
from types import ModuleType


_MODULE_CACHE: dict[tuple[str, str], ModuleType] = {}
_MODULE_CACHE_LOCK = RLock()


def load_module_once(module_name: str, file_path: Path) -> ModuleType:
    """Load a file-backed module once per process and reuse it afterwards."""
    resolved_path = Path(file_path).resolve()
    cache_key = (module_name, str(resolved_path))
    with _MODULE_CACHE_LOCK:
        cached = _MODULE_CACHE.get(cache_key)
        if cached is not None:
            return cached

        spec = importlib.util.spec_from_file_location(module_name, resolved_path)
        if spec is None or spec.loader is None:
            raise ImportError(f'Cannot load module {module_name!r} from {resolved_path}')

        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        parent_dir = str(resolved_path.parent)
        inserted = False
        if parent_dir not in sys.path:
            sys.path.insert(0, parent_dir)
            inserted = True
        _MODULE_CACHE[cache_key] = module
        try:
            spec.loader.exec_module(module)
        except Exception:
            _MODULE_CACHE.pop(cache_key, None)
            if sys.modules.get(module_name) is module:
                sys.modules.pop(module_name, None)
            raise
        finally:
            if inserted and sys.path[:1] == [parent_dir]:
                sys.path.pop(0)
        return module


def clear_module_cache() -> None:
    """Test hook for forcing dynamic modules to be reloaded."""
    with _MODULE_CACHE_LOCK:
        _MODULE_CACHE.clear()
