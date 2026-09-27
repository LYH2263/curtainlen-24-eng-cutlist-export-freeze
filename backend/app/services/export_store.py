"""Disk persistence for frozen cut-sheet exports.

Writes are deterministic (sorted keys, fixed indent, trailing newline) and
atomic (tmp file + os.replace), so an exported file only ever changes when a
new export is explicitly requested.
"""
import json
import os
from pathlib import Path

from app.config import EXPORTS_DIR

EXPORT_FILE = "cut_sheet_freeze.json"


def export_path(exports_dir=None) -> Path:
    base = Path(exports_dir) if exports_dir is not None else EXPORTS_DIR
    return base / EXPORT_FILE


def write_export(doc: dict, exports_dir=None) -> Path:
    """Serialize doc to stable bytes and atomically replace the export file."""
    path = export_path(exports_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(doc, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    os.replace(tmp, path)
    return path


def read_export(exports_dir=None) -> dict:
    path = export_path(exports_dir)
    return json.loads(path.read_text(encoding="utf-8"))
