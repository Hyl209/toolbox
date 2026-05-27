from __future__ import annotations

from pathlib import Path
from types import ModuleType

from toolbox_app.loaders import load_module_once


ModuleSpec = tuple[str, Path]


class DynamicModuleLoader:
    def __init__(self, modules: dict[str, ModuleSpec]):
        self._modules = dict(modules)

    def load(self, key: str) -> ModuleType:
        module_name, file_path = self._modules[key]
        return self.load_path(module_name, file_path)

    def load_path(self, module_name: str, file_path: Path) -> ModuleType:
        return load_module_once(module_name, file_path)

