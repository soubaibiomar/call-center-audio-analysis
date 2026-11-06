"""Startup rejection checks; these controlled tests do not claim GPU execution."""

import ctypes

import ctranslate2
import pytest

from services.workers.runtime import verify_cuda_runtime


def test_missing_cuda_device_never_falls_back(monkeypatch):
    monkeypatch.setattr(ctranslate2, "get_cuda_device_count", lambda: 0)
    with pytest.raises(RuntimeError, match="no CPU fallback"):
        verify_cuda_runtime()


@pytest.mark.parametrize("missing", ["libcublas.so.12", "libcublasLt.so.12", "libcudnn.so.9"])
def test_missing_gpu_library_fails_before_job_consumption(monkeypatch, missing):
    monkeypatch.setattr(ctranslate2, "get_cuda_device_count", lambda: 1)

    def load(name):
        if name == missing:
            raise OSError("synthetic missing CUDA library")
        return object()

    monkeypatch.setattr(ctypes, "CDLL", load)
    with pytest.raises(RuntimeError, match=missing):
        verify_cuda_runtime()
