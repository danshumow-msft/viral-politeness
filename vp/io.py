"""Small I/O helpers: per-trial record files are JSONL, committed gzip-compressed."""
from __future__ import annotations
import gzip
import json


def open_text(path: str, mode: str = "r"):
    """Open a text file for reading or writing; gzip-compressed when the name ends in .gz."""
    if str(path).endswith(".gz"):
        return gzip.open(path, mode + "t", encoding="utf-8")
    return open(path, mode, encoding="utf-8")


def read_jsonl(path: str) -> list[dict]:
    with open_text(path) as fh:
        return [json.loads(line) for line in fh if line.strip()]


def write_jsonl(path: str, records) -> None:
    with open_text(path, "w") as fh:
        for r in records:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")
