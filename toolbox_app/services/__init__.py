from __future__ import annotations

from importlib import import_module

__all__ = [
    'PDFService',
    'VideoService',
    'OCRService',
    'ImageService',
    'DownloadService',
    'FileService',
]

_SERVICE_MODULES = {
    'PDFService': '.pdf_service',
    'VideoService': '.video_service',
    'OCRService': '.ocr_service',
    'ImageService': '.image_service',
    'DownloadService': '.download_service',
    'FileService': '.file_service',
}


def __getattr__(name: str):
    if name not in _SERVICE_MODULES:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    module = import_module(_SERVICE_MODULES[name], __name__)
    value = getattr(module, name)
    globals()[name] = value
    return value
