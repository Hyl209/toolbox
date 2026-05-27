"""GPU 加速管理器 — 提供 GPU 检测与信息查询接口。"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


class GPUManager:
    """GPU 加速管理器，不强制依赖任何 GPU 库。"""

    def __init__(self) -> None:
        self._backend: str | None = None
        self._device_info: dict[str, Any] | None = None
        self._detect_backend()

    # ------------------------------------------------------------------
    # 公开接口
    # ------------------------------------------------------------------

    def is_available(self) -> bool:
        """检测当前环境是否有可用的 GPU 加速后端。"""
        return self._backend is not None

    def get_device_info(self) -> dict[str, Any]:
        """返回 GPU 设备信息字典。无 GPU 时返回空字典。"""
        if self._device_info is None:
            return {}
        return dict(self._device_info)

    def get_supported_operations(self) -> list[str]:
        """返回当前后端支持的 GPU 加速操作列表。"""
        if self._backend is None:
            return []
        ops_map: dict[str, list[str]] = {
            "cuda": [
                "matrix_multiply",
                "convolution",
                "image_transform",
                "batch_processing",
                "inference",
            ],
            "directml": [
                "matrix_multiply",
                "image_transform",
                "inference",
            ],
            "opencl": [
                "matrix_multiply",
                "image_transform",
            ],
        }
        return ops_map.get(self._backend, [])

    # ------------------------------------------------------------------
    # 内部检测
    # ------------------------------------------------------------------

    def _detect_backend(self) -> None:
        """按优先级依次尝试 CUDA -> DirectML -> OpenCL。"""
        if self._try_cuda():
            return
        if self._try_directml():
            return
        self._try_opencl()

    def _try_cuda(self) -> bool:
        try:
            import torch  # type: ignore[import-untyped]

            if torch.cuda.is_available():
                idx = torch.cuda.current_device()
                self._backend = "cuda"
                self._device_info = {
                    "backend": "cuda",
                    "name": torch.cuda.get_device_name(idx),
                    "memory_total_mb": round(
                        torch.cuda.get_device_properties(idx).total_mem / 1024 / 1024
                    ),
                    "compute_capability": ".".join(
                        str(v)
                        for v in torch.cuda.get_device_properties(idx)
                        .major_minor
                    ),
                }
                logger.info("CUDA detected: %s", self._device_info["name"])
                return True
        except Exception:
            pass
        return False

    def _try_directml(self) -> bool:
        try:
            import torch  # type: ignore[import-untyped]
            import torch_directml  # type: ignore[import-untyped]

            dml_device = torch_directml.device()
            self._backend = "directml"
            self._device_info = {
                "backend": "directml",
                "name": torch_directml.device_name(dml_device),
            }
            logger.info("DirectML detected: %s", self._device_info["name"])
            return True
        except Exception:
            pass
        return False

    def _try_opencl(self) -> bool:
        try:
            import pyopencl as cl  # type: ignore[import-untyped]

            platforms = cl.get_platforms()
            if platforms:
                devices = platforms[0].get_devices(cl.device_type.GPU)
                if devices:
                    dev = devices[0]
                    self._backend = "opencl"
                    self._device_info = {
                        "backend": "opencl",
                        "name": dev.name.strip(),
                        "vendor": dev.vendor.strip(),
                        "memory_mb": round(dev.global_mem_size / 1024 / 1024),
                    }
                    logger.info("OpenCL detected: %s", self._device_info["name"])
                    return True
        except Exception:
            pass
        return False
