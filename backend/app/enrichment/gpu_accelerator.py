from __future__ import annotations

import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import structlog

from app.config import settings

logger = structlog.get_logger()

# ---------------------------------------------------------------------------
# Optional dependency imports — these are NOT required packages.
# Everything degrades gracefully to CPU when absent.
# ---------------------------------------------------------------------------

_openvino_available = False
_ipex_available = False

try:
    from openvino.runtime import Core as OVCore

    _openvino_available = True
except ImportError:
    OVCore = None

try:
    import intel_extension_for_pytorch as _unused_ipex

    _ipex_available = True
except ImportError:
    _unused_ipex = None


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------


@dataclass
class DeviceInfo:
    available: bool = False
    backend: str = "cpu"
    device_name: str = ""
    driver_version: str = ""
    memory_mb: int = 0
    extra: dict[str, str] = field(default_factory=dict)


@dataclass
class BenchmarkResult:
    cpu_avg_ms: float = 0.0
    gpu_avg_ms: float = 0.0
    speedup: float = 1.0
    iterations: int = 0
    model_path: str = ""
    error: str | None = None


@dataclass
class OptimizedModel:
    model: Any = None
    device: str = "CPU"
    original_path: str = ""
    cache_path: str = ""
    optimized: bool = False
    error: str | None = None


# ---------------------------------------------------------------------------
# GPUAccelerator
# ---------------------------------------------------------------------------


class GPUAccelerator:
    """Detect and use Intel iGPU acceleration via OpenVINO or IPEX.

    All methods degrade gracefully when optional deps are absent.
    """

    def __init__(self) -> None:
        self._ov_core: Any | None = None
        self._device_info: DeviceInfo | None = None

    # -- OpenVINO core (lazy) -----------------------------------------------

    @property
    def _core(self) -> Any | None:
        if self._ov_core is None and _openvino_available and OVCore is not None:
            try:
                self._ov_core = OVCore()
            except Exception as exc:
                logger.warning("openvino_core_init_failed", error=str(exc))
        return self._ov_core

    # -- Public API ---------------------------------------------------------

    def is_available(self) -> bool:
        """Return True when Intel GPU acceleration is possible."""
        if not settings.intel_gpu_enabled:
            return False

        if _openvino_available and self._core is not None:
            try:
                devices = self._core.available_devices
                return any(d.startswith("GPU") for d in devices)
            except Exception:
                pass

        return _ipex_available

    def get_device_info(self) -> DeviceInfo:
        """Return information about the detected Intel GPU (or CPU fallback)."""
        if self._device_info is not None:
            return self._device_info

        info = DeviceInfo()

        if not settings.intel_gpu_enabled:
            info.backend = "cpu"
            self._device_info = info
            return info

        # Try OpenVINO first
        if _openvino_available and self._core is not None:
            try:
                devices = self._core.available_devices
                gpu_devices = [d for d in devices if d.startswith("GPU")]
                if gpu_devices:
                    gpu_dev = gpu_devices[0]
                    info.available = True
                    info.backend = "openvino"
                    info.device_name = self._core.get_property(
                        gpu_dev, "FULL_DEVICE_NAME"
                    )
                    info.extra["openvino_devices"] = ",".join(devices)
                    self._device_info = info
                    return info
            except Exception as exc:
                logger.debug("openvino_device_query_failed", error=str(exc))

        # Try IPEX
        if _ipex_available:
            try:
                import torch

                if hasattr(torch, "xpu") and torch.xpu.is_available():
                    info.available = True
                    info.backend = "ipex"
                    info.device_name = torch.xpu.get_device_name(0)
                    info.extra["xpu_device_count"] = str(torch.xpu.device_count())
                    self._device_info = info
                    return info
            except Exception as exc:
                logger.debug("ipex_device_query_failed", error=str(exc))

        info.backend = "cpu"
        self._device_info = info
        return info

    def optimize_model(self, model_path: str) -> OptimizedModel:
        """Convert an ONNX model to OpenVINO IR and compile for Intel GPU.

        Falls back to CPU compilation when GPU is unavailable.
        """
        result = OptimizedModel(original_path=model_path)

        if not _openvino_available or self._core is None:
            result.error = "openvino not available"
            return result

        target_device = "GPU" if self.is_available() else "CPU"
        result.device = target_device

        try:
            ov_model = self._core.read_model(model_path)

            # Apply cache directory if configured
            cache_dir = settings.openvino_cache_dir
            if cache_dir:
                cache_path = Path(cache_dir)
                cache_path.mkdir(parents=True, exist_ok=True)
                self._core.set_property({"CACHE_DIR": str(cache_path)})
                result.cache_path = str(cache_path)

            compiled = self._core.compile_model(ov_model, target_device)
            result.model = compiled
            result.optimized = True
            logger.info(
                "model_optimized",
                model_path=model_path,
                device=target_device,
                cache_dir=cache_dir or "",
            )
        except Exception as exc:
            result.error = str(exc)
            logger.warning(
                "model_optimization_failed",
                model_path=model_path,
                device=target_device,
                error=str(exc),
            )

        return result

    def benchmark(
        self, model_path: str, iterations: int = 10
    ) -> BenchmarkResult:
        """Compare CPU vs GPU inference time for an ONNX model.

        Returns a ``BenchmarkResult`` with timings and speedup ratio.
        """
        result = BenchmarkResult(model_path=model_path, iterations=iterations)

        if not _openvino_available or self._core is None:
            result.error = "openvino not available"
            return result

        try:
            ov_model = self._core.read_model(model_path)
        except Exception as exc:
            result.error = f"model read failed: {exc}"
            return result

        # Build a dummy input matching the model's expected shapes
        try:
            import numpy as np

            dummy_inputs: dict[str, Any] = {}
            for inp in ov_model.inputs:
                shape = list(inp.get_partial_shape())
                concrete = [s.get_length() if s.is_static else 1 for s in shape]
                dummy_inputs[inp.any_name] = np.ones(concrete, dtype=np.float32)
        except Exception as exc:
            result.error = f"dummy input creation failed: {exc}"
            return result

        # CPU benchmark
        try:
            cpu_compiled = self._core.compile_model(ov_model, "CPU")
            cpu_times: list[float] = []
            for _ in range(iterations):
                start = time.perf_counter()
                cpu_compiled(dummy_inputs)
                cpu_times.append((time.perf_counter() - start) * 1000)
            result.cpu_avg_ms = sum(cpu_times) / len(cpu_times)
        except Exception as exc:
            result.error = f"cpu benchmark failed: {exc}"
            return result

        # GPU benchmark (only if available)
        if self.is_available():
            try:
                gpu_compiled = self._core.compile_model(ov_model, "GPU")
                gpu_times: list[float] = []
                # Warm-up
                gpu_compiled(dummy_inputs)
                for _ in range(iterations):
                    start = time.perf_counter()
                    gpu_compiled(dummy_inputs)
                    gpu_times.append((time.perf_counter() - start) * 1000)
                result.gpu_avg_ms = sum(gpu_times) / len(gpu_times)
                if result.gpu_avg_ms > 0:
                    result.speedup = result.cpu_avg_ms / result.gpu_avg_ms
            except Exception as exc:
                result.error = f"gpu benchmark failed: {exc}"
                result.gpu_avg_ms = 0.0
                result.speedup = 1.0
        else:
            result.gpu_avg_ms = result.cpu_avg_ms
            result.speedup = 1.0

        return result


# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------

gpu_accelerator = GPUAccelerator()
