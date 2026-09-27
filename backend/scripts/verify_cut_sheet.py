#!/usr/bin/env python3
"""Verify the frozen cut-sheet export against its content_checksum.

Read-only: checks the in-repo JSON's line items, totals and checksum without
touching the database or rewriting the file, so repeated runs always behave
the same. Exit code 0 = frozen export is intact; 1 = missing or corrupted.

Usage: python backend/scripts/verify_cut_sheet.py
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.services import export_store  # noqa: E402
from app.services.cut_sheet import validate_cut_sheet  # noqa: E402


def main() -> int:
    path = export_store.export_path()
    if not path.exists():
        print(f"FAIL: export not found: {path}", file=sys.stderr)
        return 1
    try:
        doc = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        print(f"FAIL: {path} is not valid JSON: {exc}", file=sys.stderr)
        return 1
    errors = validate_cut_sheet(doc)
    if errors:
        for err in errors:
            print(f"FAIL: {err}", file=sys.stderr)
        return 1
    print(
        f"OK: {path} panels={doc['panels']} meters={doc['meters']} "
        f"lines={len(doc['lines'])} checksum={doc['content_checksum']}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
