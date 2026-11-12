#!/usr/bin/env bash
# Wait for MySQL + Redis, start the heartbeat writer, then the Celery worker.
set -euo pipefail

echo "[worker] waiting for db/redis ..."
python - <<'PY'
import sys, time
from sqlalchemy import create_engine, text
from redis import Redis
from app.config.settings import settings

for attempt in range(60):
    try:
        engine = create_engine(settings.database_url, pool_pre_ping=True)
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        Redis.from_url(settings.REDIS_URL, socket_timeout=1).ping()
        print("[worker] db and redis are ready")
        sys.exit(0)
    except Exception as exc:
        if attempt % 5 == 0:
            print(f"[worker] not ready ({type(exc).__name__}); retrying", flush=True)
        time.sleep(3)
print("[worker] dependencies never became ready", flush=True)
sys.exit(1)
PY

# heartbeat file consumed by compose healthcheck (worker/healthy.py)
( while true; do date +%s > /tmp/qualiscope-worker-heartbeat; sleep 5; done ) &

exec celery -A app.config.celery_app worker \
  --loglevel=info \
  --concurrency=2 \
  --hostname=qualiscope-worker@%h \
  --without-gossip --without-mingle --without-heartbeat
