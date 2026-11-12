"""Read an uploaded artifact into a raw-string DataFrame.

Rules:
* every column name becomes a string, empties are preserved as ``""`` (so the
  raw bytes of a cell can be echoed as ``observed_value`` later);
* duplicate header names are rejected with QUAL-2004 and the offending names;
* non-UTF-8 CSV payloads are rejected with QUAL-2003.
"""
import csv
import io
import os
from dataclasses import dataclass, field

import pandas as pd

from app.config.settings import settings
from app.constants.error_codes import AppError, ErrorCode

READERS = {"csv", "parquet", "jsonl", "xlsx"}


@dataclass
class LoadedFrame:
    df: pd.DataFrame
    columns: list[str] = field(default_factory=list)
    row_count: int = 0

    @property
    def column_count(self) -> int:
        return len(self.columns)


def _decode_csv(path: str) -> str:
    with open(path, "rb") as handle:
        raw = handle.read()
    for encoding in ("utf-8", "utf-8-sig"):
        try:
            return raw.decode(encoding)
        except UnicodeDecodeError:
            continue
    raise AppError(
        ErrorCode.ENCODING_ERROR,
        detail={"hint": "请先用 iconv 转成 UTF-8 再上传", "path": os.path.basename(path)},
    )


def _csv_header(text: str) -> list[str]:
    reader = csv.reader(io.StringIO(text))
    try:
        row = next(reader)
    except StopIteration:
        raise AppError(ErrorCode.FORMAT_UNSUPPORTED, message="文件为空，没有表头")
    return [str(cell).strip().lstrip("\ufeff") for cell in row]


def _assert_unique(columns: list[str]) -> None:
    seen: dict[str, int] = {}
    for name in columns:
        seen[name] = seen.get(name, 0) + 1
    duplicated = [name for name, count in seen.items() if count > 1]
    if duplicated:
        raise AppError(
            ErrorCode.DUPLICATE_COLUMN,
            context=", ".join(duplicated[:5]),
            detail={"columns": duplicated},
        )


def _read_csv(path: str) -> LoadedFrame:
    text = _decode_csv(path)
    header = _csv_header(text)
    _assert_unique(header)
    df = pd.read_csv(
        io.StringIO(text),
        dtype=str,
        keep_default_na=False,
        na_filter=False,
        skip_blank_lines=False,
    )
    df.columns = header
    return LoadedFrame(df=df, columns=header, row_count=len(df))


def _read_jsonl(path: str) -> LoadedFrame:
    text = _decode_csv(path)
    df = pd.read_json(io.StringIO(text), lines=True, dtype=str, convert_dates=False)
    df = df.fillna("")
    columns = [str(c) for c in df.columns]
    _assert_unique(columns)
    df.columns = columns
    return LoadedFrame(df=df, columns=columns, row_count=len(df))


def _read_parquet(path: str) -> LoadedFrame:
    try:
        df = pd.read_parquet(path)
    except ImportError as exc:  # pragma: no cover - pyarrow is shipped in requirements
        raise AppError(ErrorCode.FORMAT_UNSUPPORTED, message="读取 Parquet 需要 pyarrow") from exc
    columns = [str(c) for c in df.columns]
    _assert_unique(columns)
    df = df.astype(object).where(df.notna(), "")
    for col in df.columns:
        df[col] = df[col].map(lambda v: "" if v is None else str(v))
    df.columns = columns
    return LoadedFrame(df=df, columns=columns, row_count=len(df))


def _read_xlsx(path: str) -> LoadedFrame:
    df = pd.read_excel(path, dtype=str)
    df = df.fillna("")
    columns = [str(c) for c in df.columns]
    _assert_unique(columns)
    for col in df.columns:
        df[col] = df[col].map(lambda v: "" if v is None else str(v))
    df.columns = columns
    return LoadedFrame(df=df, columns=columns, row_count=len(df))


def load_frame(path: str, source_format: str) -> LoadedFrame:
    if not os.path.exists(path):
        raise AppError(ErrorCode.DATASET_NOT_FOUND, message="数据集文件不在共享卷上", detail={"path": path})
    fmt = (source_format or "csv").lower()
    if fmt not in READERS:
        raise AppError(ErrorCode.FORMAT_UNSUPPORTED, detail={"source_format": fmt})
    loaded = {"csv": _read_csv, "jsonl": _read_jsonl, "parquet": _read_parquet, "xlsx": _read_xlsx}[fmt](path)
    if loaded.row_count > settings.MAX_ROWS:
        raise AppError(
            ErrorCode.ROW_LIMIT_EXCEEDED,
            detail={"row_count": loaded.row_count, "max_rows": settings.MAX_ROWS},
        )
    return loaded


def peek_header(path: str, source_format: str) -> list[str]:
    """Cheap header read used by the upload validator before persisting."""
    fmt = (source_format or "csv").lower()
    if fmt == "csv":
        header = _csv_header(_decode_csv(path))
        _assert_unique(header)
        return header
    loaded = load_frame(path, fmt)
    return loaded.columns
