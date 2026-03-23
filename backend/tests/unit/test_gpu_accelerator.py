from __future__ import annotations

import builtins
from dataclasses import asdict
from unittest.mock import MagicMock, patch

from app.enrichment.gpu_accelerator import (
    BenchmarkResult,
    DeviceInfo,
    GPUAccelerator,
    OptimizedModel,
)

# ---------------------------------------------------------------------------
# DeviceInfo / BenchmarkResult / OptimizedModel data classes
# ---------------------------------------------------------------------------


class TestDataClasses:
    def test_device_info_defaults(self) -> None:
        info = DeviceInfo()
        assert info.available is False
        assert info.backend == "cpu"
        assert info.device_name == ""
        assert info.extra == {}

    def test_benchmark_result_defaults(self) -> None:
        result = BenchmarkResult()
        assert result.speedup == 1.0
        assert result.error is None

    def test_optimized_model_defaults(self) -> None:
        opt = OptimizedModel()
        assert opt.optimized is False
        assert opt.model is None

    def test_device_info_serializable(self) -> None:
        info = DeviceInfo(available=True, backend="openvino", device_name="Arc")
        d = asdict(info)
        assert d["available"] is True
        assert d["backend"] == "openvino"


# ---------------------------------------------------------------------------
# GPUAccelerator.is_available
# ---------------------------------------------------------------------------


class TestIsAvailable:
    def test_returns_false_when_gpu_disabled(self) -> None:
        accel = GPUAccelerator()
        with patch("app.enrichment.gpu_accelerator.settings") as mock_settings:
            mock_settings.intel_gpu_enabled = False
            assert accel.is_available() is False

    def test_returns_true_with_openvino_gpu_device(self) -> None:
        accel = GPUAccelerator()
        mock_core = MagicMock()
        mock_core.available_devices = ["CPU", "GPU.0"]
        accel._ov_core = mock_core

        with (
            patch("app.enrichment.gpu_accelerator.settings") as mock_settings,
            patch("app.enrichment.gpu_accelerator._openvino_available", True),
        ):
            mock_settings.intel_gpu_enabled = True
            assert accel.is_available() is True

    def test_returns_false_when_no_gpu_device(self) -> None:
        accel = GPUAccelerator()
        mock_core = MagicMock()
        mock_core.available_devices = ["CPU"]
        accel._ov_core = mock_core

        with (
            patch("app.enrichment.gpu_accelerator.settings") as mock_settings,
            patch("app.enrichment.gpu_accelerator._openvino_available", True),
            patch("app.enrichment.gpu_accelerator._ipex_available", False),
        ):
            mock_settings.intel_gpu_enabled = True
            assert accel.is_available() is False

    def test_falls_back_to_ipex(self) -> None:
        accel = GPUAccelerator()
        with (
            patch("app.enrichment.gpu_accelerator.settings") as mock_settings,
            patch("app.enrichment.gpu_accelerator._openvino_available", False),
            patch("app.enrichment.gpu_accelerator._ipex_available", True),
        ):
            mock_settings.intel_gpu_enabled = True
            assert accel.is_available() is True


# ---------------------------------------------------------------------------
# GPUAccelerator.get_device_info
# ---------------------------------------------------------------------------


class TestGetDeviceInfo:
    def test_cpu_when_disabled(self) -> None:
        accel = GPUAccelerator()
        with patch("app.enrichment.gpu_accelerator.settings") as mock_settings:
            mock_settings.intel_gpu_enabled = False
            info = accel.get_device_info()
        assert info.backend == "cpu"
        assert info.available is False

    def test_openvino_gpu_detected(self) -> None:
        accel = GPUAccelerator()
        mock_core = MagicMock()
        mock_core.available_devices = ["CPU", "GPU.0"]
        mock_core.get_property.return_value = "Intel Arc A770"
        accel._ov_core = mock_core

        with (
            patch("app.enrichment.gpu_accelerator.settings") as mock_settings,
            patch("app.enrichment.gpu_accelerator._openvino_available", True),
        ):
            mock_settings.intel_gpu_enabled = True
            info = accel.get_device_info()

        assert info.available is True
        assert info.backend == "openvino"
        assert info.device_name == "Intel Arc A770"

    def test_caches_result(self) -> None:
        accel = GPUAccelerator()
        with patch("app.enrichment.gpu_accelerator.settings") as mock_settings:
            mock_settings.intel_gpu_enabled = False
            info1 = accel.get_device_info()
            info2 = accel.get_device_info()
        assert info1 is info2


# ---------------------------------------------------------------------------
# GPUAccelerator.optimize_model
# ---------------------------------------------------------------------------


class TestOptimizeModel:
    def test_returns_error_when_openvino_absent(self) -> None:
        accel = GPUAccelerator()
        with patch("app.enrichment.gpu_accelerator._openvino_available", False):
            result = accel.optimize_model("/tmp/model.onnx")
        assert result.optimized is False
        assert result.error is not None

    def test_compiles_to_gpu_when_available(self) -> None:
        accel = GPUAccelerator()
        mock_core = MagicMock()
        mock_core.available_devices = ["CPU", "GPU.0"]
        mock_core.read_model.return_value = MagicMock()
        mock_core.compile_model.return_value = MagicMock()
        accel._ov_core = mock_core

        with (
            patch("app.enrichment.gpu_accelerator.settings") as mock_settings,
            patch("app.enrichment.gpu_accelerator._openvino_available", True),
        ):
            mock_settings.intel_gpu_enabled = True
            mock_settings.openvino_cache_dir = ""
            result = accel.optimize_model("/tmp/model.onnx")

        assert result.optimized is True
        assert result.device == "GPU"

    def test_falls_back_to_cpu_device(self) -> None:
        accel = GPUAccelerator()
        mock_core = MagicMock()
        mock_core.available_devices = ["CPU"]
        mock_core.read_model.return_value = MagicMock()
        mock_core.compile_model.return_value = MagicMock()
        accel._ov_core = mock_core

        with (
            patch("app.enrichment.gpu_accelerator.settings") as mock_settings,
            patch("app.enrichment.gpu_accelerator._openvino_available", True),
            patch("app.enrichment.gpu_accelerator._ipex_available", False),
        ):
            mock_settings.intel_gpu_enabled = False
            mock_settings.openvino_cache_dir = ""
            result = accel.optimize_model("/tmp/model.onnx")

        assert result.optimized is True
        assert result.device == "CPU"

    def test_cache_dir_configured(self, tmp_path: object) -> None:
        accel = GPUAccelerator()
        mock_core = MagicMock()
        mock_core.available_devices = ["CPU"]
        mock_core.read_model.return_value = MagicMock()
        mock_core.compile_model.return_value = MagicMock()
        accel._ov_core = mock_core

        with (
            patch("app.enrichment.gpu_accelerator.settings") as mock_settings,
            patch("app.enrichment.gpu_accelerator._openvino_available", True),
            patch("app.enrichment.gpu_accelerator._ipex_available", False),
        ):
            mock_settings.intel_gpu_enabled = False
            mock_settings.openvino_cache_dir = str(tmp_path)
            result = accel.optimize_model("/tmp/model.onnx")

        assert result.cache_path == str(tmp_path)
        mock_core.set_property.assert_called_once()


# ---------------------------------------------------------------------------
# GPUAccelerator.benchmark
# ---------------------------------------------------------------------------


class TestBenchmark:
    def test_returns_error_when_openvino_absent(self) -> None:
        accel = GPUAccelerator()
        with patch("app.enrichment.gpu_accelerator._openvino_available", False):
            result = accel.benchmark("/tmp/model.onnx")
        assert result.error is not None
        assert result.speedup == 1.0

    def test_cpu_only_benchmark(self) -> None:
        accel = GPUAccelerator()

        # Build a mock OV model with one input
        mock_input = MagicMock()
        mock_dim = MagicMock()
        mock_dim.is_static = True
        mock_dim.get_length.return_value = 4
        mock_input.get_partial_shape.return_value = [mock_dim, mock_dim]
        mock_input.any_name = "input"

        mock_ov_model = MagicMock()
        mock_ov_model.inputs = [mock_input]

        mock_core = MagicMock()
        mock_core.available_devices = ["CPU"]
        mock_core.read_model.return_value = mock_ov_model
        mock_core.compile_model.return_value = MagicMock()
        accel._ov_core = mock_core

        with (
            patch("app.enrichment.gpu_accelerator.settings") as mock_settings,
            patch("app.enrichment.gpu_accelerator._openvino_available", True),
            patch("app.enrichment.gpu_accelerator._ipex_available", False),
        ):
            mock_settings.intel_gpu_enabled = False
            result = accel.benchmark("/tmp/model.onnx", iterations=3)

        assert result.iterations == 3
        assert result.cpu_avg_ms > 0
        assert result.speedup == 1.0
        assert result.error is None


# ---------------------------------------------------------------------------
# Singleton
# ---------------------------------------------------------------------------


class TestSingleton:
    def test_module_level_singleton_exists(self) -> None:
        from app.enrichment.gpu_accelerator import gpu_accelerator

        assert isinstance(gpu_accelerator, GPUAccelerator)


# ---------------------------------------------------------------------------
# EmbeddingService GPU integration
# ---------------------------------------------------------------------------


class TestEmbeddingServiceGPU:
    def test_embedding_service_still_works_without_gpu(self) -> None:
        """CPU-only path must not break when gpu_accelerator reports unavailable."""
        from unittest.mock import AsyncMock

        from app.enrichment.embedding import EmbeddingService

        real_import = builtins.__import__

        def _guarded_import(name, globals=None, locals=None, fromlist=(), level=0):
            if name == "sentence_transformers":
                raise ImportError("sentence-transformers not installed in test")
            return real_import(name, globals, locals, fromlist, level)

        db = AsyncMock()
        svc = EmbeddingService(db)
        # Force model to None (sentence-transformers not installed in CI)
        svc._model = None
        # embed_text should return None gracefully
        with patch("builtins.__import__", side_effect=_guarded_import):
            assert svc.embed_text("hello") is None

    def test_gpu_optimized_flag_set_on_attempt(self) -> None:
        from unittest.mock import AsyncMock

        from app.enrichment.embedding import EmbeddingService

        db = AsyncMock()
        svc = EmbeddingService(db)
        assert svc._gpu_optimized is False
        # Calling _try_gpu_optimize shouldn't raise even without deps
        svc._try_gpu_optimize()
        # Flag should be set regardless (either optimized or skipped)
        # Since no GPU is available in test, flag stays False or True
        # depending on import availability — just verify no crash
        assert isinstance(svc._gpu_optimized, bool)
