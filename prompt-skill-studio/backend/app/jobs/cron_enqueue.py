"""Single-shot entrypoint Railway's cron service runs on a schedule.

Pushes a `sync_vendor_docs` job onto the default RQ queue and exits.
"""
from __future__ import annotations

import logging
import sys

from rq import Queue

from app.core.redis_client import get_redis

log = logging.getLogger(__name__)


def main() -> int:
    q = Queue("default", connection=get_redis())
    job = q.enqueue("app.jobs.sync_vendor_docs.sync_vendor_docs", job_timeout=900)
    print(f"enqueued sync_vendor_docs job_id={job.id}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
