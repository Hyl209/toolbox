from __future__ import annotations

import importlib.util
import sys
from collections import OrderedDict
from pathlib import Path
from threading import RLock
from types import ModuleType

_MAX_MODULE_CACHE = 32

_MODULE_CACHE: OrderedDict[tuple[str, str], tuple[ModuleType, str]] = OrderedDict()
_MODULE_CACHE_LOCK = RLock()


def _ensure_parent_package(file_path: Path) -> str | None:
    """If file_path is inside a package (has __init__.py), register the
    parent package in sys.modules so relative imports work. Returns the
    package name or None."""
    parent = file_path.parent
    if not (parent / '__init__.py').exists():
        return None
    pkg_name = parent.name.replace('-', '_')
    if pkg_name in sys.modules:
        return pkg_name
    pkg = ModuleType(pkg_name)
    pkg.__path__ = [str(parent)]
    pkg.__package__ = pkg_name
    pkg.__file__ = str(parent / '__init__.py')
    sys.modules[pkg_name] = pkg
    return pkg_name


def load_module_once(module_name: str, file_path: Path) -> ModuleType:
    """Load a file-backed module once per process and reuse it afterwards."""
    resolved_path = Path(file_path).resolve()
    cache_key = (module_name, str(resolved_path))
    with _MODULE_CACHE_LOCK:
        cached = _MODULE_CACHE.get(cache_key)
        if cached is not None:
            return cached[0]

        # Ensure parent package exists for relative imports
        pkg_name = _ensure_parent_package(resolved_path)
        qualified_name = f'{pkg_name}.{module_name}' if pkg_name else module_name

        spec = importlib.util.spec_from_file_location(qualified_name, resolved_path)
        if spec is None or spec.loader is None:
            raise ImportError(f'Cannot load module {module_name!r} from {resolved_path}')

        module = importlib.util.module_from_spec(spec)
        if pkg_name:
            module.__package__ = pkg_name
        sys.modules[qualified_name] = module
        # Also register under short name for backward compat
        if qualified_name != module_name:
            sys.modules[module_name] = module
        parent_dir = str(resolved_path.parent)
        inserted = False
        if parent_dir not in sys.path:
            sys.path.insert(0, parent_dir)
            inserted = True
        try:
            spec.loader.exec_module(module)
        except Exception:
            if sys.modules.get(qualified_name) is module:
                sys.modules.pop(qualified_name, None)
            if sys.modules.get(module_name) is module:
                sys.modules.pop(module_name, None)
            raise
        finally:
            if inserted and sys.path[:1] == [parent_dir]:
                sys.path.pop(0)
        # Cache AFTER successful init — prevents other threads from seeing
        # a partially-initialised module if exec_module is slow or fails.
        _MODULE_CACHE[cache_key] = (module, qualified_name)
        # Evict oldest entries if over capacity
        while len(_MODULE_CACHE) > _MAX_MODULE_CACHE:
            evicted_key, (_, evicted_qname) = _MODULE_CACHE.popitem(last=False)
            evicted_short = evicted_key[0]
            for name in (evicted_short, evicted_qname):
                if name and sys.modules.get(name) is not None:
                    sys.modules.pop(name, None)
        return module


def clear_module_cache() -> None:
    """Test hook for forcing dynamic modules to be reloaded."""
    with _MODULE_CACHE_LOCK:
        _MODULE_CACHE.clear()
