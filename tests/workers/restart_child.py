"""Synthetic graph child used to kill/restart the actual broker/runner boundary."""

import argparse
import time
from pathlib import Path

import dramatiq

from services.api.db.settings import database_url
from services.workers.broker import QueueBroker
from services.workers.runner import JobRunner
from services.workers.settings import QueueSettings
from services.workers.storage import AudioStore
from src.database.connection import get_engine
from tests.workers.test_durable_jobs import factory


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--marker", required=True)
    parser.add_argument("--block", action="store_true")
    args = parser.parse_args()
    settings = QueueSettings.from_env()
    engine = get_engine(database_url())

    def callback():
        if args.block:
            Path(args.marker).write_text("entered synthetic inference", encoding="utf-8")
            time.sleep(60)

    service, _ = factory(engine, callback=callback)
    broker = QueueBroker(
        settings, JobRunner(engine, AudioStore(settings), settings, "cpu", service)
    )
    worker = dramatiq.Worker(broker.broker, worker_threads=1)
    worker.start()
    try:
        while True:
            broker.dispatch(engine)
            time.sleep(0.1)
    finally:
        worker.stop(timeout=5000)
        broker.broker.close()
        engine.dispose()


if __name__ == "__main__":
    main()
