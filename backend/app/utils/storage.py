"""Shared-volume file helpers: upload persistence, checksums, quarantine CSVs."""
import csv
import hashlib
import os
import re
import uuid

from app.config.settings import settings

ALLOWED_FORMATS = {
    ".csv": "csv",
    ".parquet": "parquet",
    ".jsonl": "jsonl",
    ".xlsx": "xlsx",
}
SAFE_NAME = re.compile(r"[^0-9A-Za-z\u4e00-\u9fff._-]+")


def ensure_dirs() -> None:
    os.makedirs(settings.ARTIFACT_DIR, exist_ok=True)
    os.makedirs(settings.QUARANTINE_DIR, exist_ok=True)


def detect_format(filename: str) -> str | None:
    ext = os.path.splitext(filename or "")[1].lower()
    return ALLOWED_FORMATS.get(ext)


def safe_filename(name: str) -> str:
    base = os.path.basename(name or "dataset.csv")
    cleaned = SAFE_NAME.sub("_", base).strip("._") or "dataset.csv"
    return cleaned[:120]


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def sha256_file(path: str) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def save_upload(filename: str, payload: bytes) -> tuple[str, str, str]:
    """Persist one upload on the shared volume. Returns (path, checksum, safe_name)."""
    ensure_dirs()
    name = safe_filename(filename)
    stem, ext = os.path.splitext(name)
    stored = f"{stem}-{uuid.uuid4().hex[:8]}{ext}"
    path = os.path.join(settings.ARTIFACT_DIR, stored)
    with open(path, "wb") as handle:
        handle.write(payload)
    return path, sha256_bytes(payload), name


def write_dataset_file(filename: str, payload: bytes) -> tuple[str, str]:
    """Idempotent write for seed data: same filename => same path, rewritten bytes."""
    ensure_dirs()
    name = safe_filename(filename)
    path = os.path.join(settings.ARTIFACT_DIR, name)
    with open(path, "wb") as handle:
        handle.write(payload)
    return path, sha256_bytes(payload)


def remove_file(path: str) -> bool:
    try:
        os.remove(path)
        return True
    except FileNotFoundError:
        return False
    except OSError:
        return False


def quarantine_path(run_id: int) -> str:
    ensure_dirs()
    return os.path.join(settings.QUARANTINE_DIR, f"run_{run_id:06d}_quarantine.csv")


def write_quarantine(run_id: int, header: list[str], rows: list[list[str]]) -> str | None:
    """Write isolated violating rows for one batch. Returns the file path."""
    if not rows:
        return None
    path = quarantine_path(run_id)
    with open(path, "w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(header)
        writer.writerows(rows)
    return path
