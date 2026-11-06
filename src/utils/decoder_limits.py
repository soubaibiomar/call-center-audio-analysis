"""OS resource limits for the disposable decoder process, not the application."""

import importlib
import os

_job_handle: int | None = None


def apply_decoder_limits(memory_bytes: int = 1024 * 1024 * 1024) -> None:
    """Fail closed when process resource limits cannot be installed."""
    global _job_handle
    if os.name != "nt":
        resource = importlib.import_module("resource")

        resource.setrlimit(resource.RLIMIT_AS, (memory_bytes, memory_bytes))
        resource.setrlimit(resource.RLIMIT_CPU, (30, 30))
        return
    import ctypes
    from ctypes import wintypes

    class Basic(ctypes.Structure):
        _fields_ = [
            ("process_time", ctypes.c_int64),
            ("job_time", ctypes.c_int64),
            ("flags", wintypes.DWORD),
            ("min_working", ctypes.c_size_t),
            ("max_working", ctypes.c_size_t),
            ("active", wintypes.DWORD),
            ("affinity", ctypes.c_size_t),
            ("priority", wintypes.DWORD),
            ("scheduling", wintypes.DWORD),
        ]

    class Limits(ctypes.Structure):
        _fields_ = [
            ("basic", Basic),
            ("io", ctypes.c_uint64 * 6),
            ("process_memory", ctypes.c_size_t),
            ("job_memory", ctypes.c_size_t),
            ("peak_process", ctypes.c_size_t),
            ("peak_job", ctypes.c_size_t),
        ]

    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.CreateJobObjectW.argtypes = [ctypes.c_void_p, wintypes.LPCWSTR]
    kernel.CreateJobObjectW.restype = wintypes.HANDLE
    kernel.GetCurrentProcess.restype = wintypes.HANDLE
    kernel.SetInformationJobObject.argtypes = [
        wintypes.HANDLE,
        ctypes.c_int,
        ctypes.c_void_p,
        wintypes.DWORD,
    ]
    kernel.AssignProcessToJobObject.argtypes = [wintypes.HANDLE, wintypes.HANDLE]
    handle = kernel.CreateJobObjectW(None, None)
    if not handle:
        raise OSError("Cannot create decoder job")
    limits = Limits()
    limits.basic.flags = 0x100 | 0x8 | 0x2
    limits.basic.active = 1
    limits.basic.process_time = 30 * 10_000_000
    limits.process_memory = memory_bytes
    if not kernel.SetInformationJobObject(handle, 9, ctypes.byref(limits), ctypes.sizeof(limits)):
        raise OSError("Cannot configure decoder limits")
    if not kernel.AssignProcessToJobObject(handle, kernel.GetCurrentProcess()):
        raise OSError("Cannot assign decoder limits")
    # Retain until process exit; do not close a job containing our own process.
    _job_handle = handle
