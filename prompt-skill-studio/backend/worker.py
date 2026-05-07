"""RQ worker entrypoint. Mirrors the pattern in ai-document-processor/worker/worker.py."""
from __future__ import annotations

import logging
import os

from rq import Queue, Worker

from app.core.redis_client import get_redis

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
log = logging.getLogger("worker")


def main() -> None:
    queue_names = os.getenv("RQ_QUEUES", "default").split(",")
    conn = get_redis()
    queues = [Queue(name.strip(), connection=conn) for name in queue_names]
    log.info("starting RQ worker on queues=%s", [q.name for q in queues])
    Worker(queues, connection=conn).work(with_scheduler=True)


if __name__ == "__main__":
    main()
