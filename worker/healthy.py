"""Compose healthcheck for the Celery worker.

Reads the heartbeat file refreshed every 5s by worker/entrypoint.sh; older than
60 seconds counts as unhealthy.
"""
import os
import sys
import time

HEARTBEAT = "/tmp/qualiscope-worker-heartbeat"
MAX_AGE_SECONDS = 60


def main() -> int:
    try:
        age = time.time() - os.path.getmtime(HEARTBEAT)
    except OSError:
        print(f"heartbeat file {HEARTBEAT} missing")
        return 1
    if age > MAX_AGE_SECONDS:
        print(f"heartbeat stale: {age:.1f}s > {MAX_AGE_SECONDS}s")
        return 1
    print(f"worker healthy: heartbeat age {age:.1f}s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
