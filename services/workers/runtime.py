"""One dedicated CPU or GPU worker, one inference thread, durable DB dispatcher."""

import argparse
import ctypes
import logging
import os
import signal
from threading import Event

import dramatiq

from services.api.db.settings import database_url
from services.workers.broker import QueueBroker
from services.workers.runner import JobRunner
from services.workers.settings import QueueSettings
from services.workers.storage import AudioStore
from src.database.connection import get_engine, init_db
from src.services.contracts import AnalysisPort


def verify_cuda_runtime() -> None:
    """Fail before consuming a GPU job if its user-space runtime is incomplete."""
    import ctranslate2

    if ctranslate2.get_cuda_device_count() < 1:
        raise RuntimeError("GPU queue requires a working CUDA device; no CPU fallback")
    for library in ("libcublas.so.12", "libcublasLt.so.12", "libcudnn.so.9"):
        try:
            ctypes.CDLL(library)
        except OSError as error:
            raise RuntimeError(f"GPU runtime cannot load {library}; use Dockerfile.gpu") from error


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("queue", choices=["cpu", "gpu"])
    args = parser.parse_args()
    if args.queue == "cpu":
        os.environ["CUDA_VISIBLE_DEVICES"] = ""
        os.environ["WHISPER_DEVICE"] = "cpu"
    else:
        verify_cuda_runtime()
        os.environ["WHISPER_DEVICE"] = "cuda"
    settings, url = QueueSettings.from_env(), database_url()
    if settings is None or not url or not settings.tenants:
        raise ValueError("Private database/queue configuration and allowed tenants are required")
    engine = get_engine(url)
    init_db(engine)

    def factory() -> AnalysisPort:
        from src.graph.workflow import compile_workflow
        from src.security.audit import AuditLogger
        from src.services.analysis import AnalysisService
        from src.utils.config import load_config

        return AnalysisService(
            compile_workflow(load_config(), db_engine=engine), engine, AuditLogger(engine=engine)
        )

    runner = JobRunner(engine, AudioStore(settings), settings, args.queue, factory)
    queue = QueueBroker(settings, runner)
    worker = dramatiq.Worker(
        queue.broker, queues={f"analysis_{args.queue}"}, worker_threads=1, worker_timeout=500
    )
    stop = Event()
    signal.signal(signal.SIGTERM, lambda *_: stop.set())
    signal.signal(signal.SIGINT, lambda *_: stop.set())
    worker.start()
    try:
        while not stop.is_set():
            try:
                queue.dispatch(engine)
            except Exception:
                logging.getLogger(__name__).warning(
                    "Job dispatcher unavailable; durable requests retained"
                )
            stop.wait(1)
    finally:
        worker.stop(timeout=30000)
        queue.broker.close()
        engine.dispose()


if __name__ == "__main__":
    main()
