import json
import os
import subprocess
import sys
from pathlib import Path

import pytest
from fastapi import HTTPException

from app import seed
from app.engines.curtain_math import fabric_meters
from app.repositories import history
from app.routers import exports as exports_router
from app.services import cut_sheet, export_store

BACKEND_DIR = Path(__file__).resolve().parents[2]
VERIFY_CMD = BACKEND_DIR / "scripts" / "verify_cut_sheet.py"


def _save_run(note="src"):
    return history.insert_run(1, 1, fabric_meters(3.0, 2.6, 2.0, 0.10, 0.15, 1.4), note)


@pytest.fixture(autouse=True)
def _db():
    seed.init_db()


def test_export_writes_lines_totals_checksum():
    _save_run()
    out = exports_router.export_cut_sheet()
    path = export_store.export_path()
    doc = json.loads(path.read_bytes())
    assert doc["panels"] == 5
    assert doc["meters"] == 14.25
    # 无 cut_sheet 时按 panels 份数复制 cut_height 生成行
    assert [line["cut_height"] for line in doc["lines"]] == [2.85] * 5
    assert [line["seq"] for line in doc["lines"]] == [1, 2, 3, 4, 5]
    assert doc["totals"] == {"panels": 5, "meters": 14.25}
    assert doc["content_checksum"] == out["content_checksum"]
    assert cut_sheet.validate_cut_sheet(doc) == []


def test_reexport_same_run_is_byte_identical():
    _save_run()
    cut_sheet.export_latest_cut_sheet()
    first = export_store.export_path().read_bytes()
    cut_sheet.export_latest_cut_sheet()
    assert export_store.export_path().read_bytes() == first


def test_export_freezes_snapshot_against_later_runs():
    _save_run()
    out = exports_router.export_cut_sheet()
    path = export_store.export_path()
    frozen = path.read_bytes()
    # 导出后再在主库额外保存一单；不重新导出，JSON 字节与 checksum 不变
    history.insert_run(2, 2, fabric_meters(2.2, 1.5, 2.0, 0.10, 0.15, 1.4), "later run")
    assert path.read_bytes() == frozen
    assert json.loads(path.read_bytes())["content_checksum"] == out["content_checksum"]


def test_verify_command_twice_exit_zero():
    _save_run()
    cut_sheet.export_latest_cut_sheet()
    for _ in range(2):
        r = subprocess.run([sys.executable, str(VERIFY_CMD)], capture_output=True, text=True)
        assert r.returncode == 0, r.stderr
        assert "OK" in r.stdout


def test_tamper_breaks_verification(tmp_path):
    _save_run()
    cut_sheet.export_latest_cut_sheet(exports_dir=tmp_path)
    path = export_store.export_path(tmp_path)
    doc = json.loads(path.read_text(encoding="utf-8"))
    doc["lines"][0]["meters"] = 99.0
    path.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    assert cut_sheet.validate_cut_sheet(doc)
    env = dict(os.environ, EXPORTS_DIR=str(tmp_path))
    r = subprocess.run([sys.executable, str(VERIFY_CMD)], capture_output=True, text=True, env=env)
    assert r.returncode == 1


def test_existing_cut_sheet_rows_are_used():
    result = {
        "panels": 2,
        "cut_height": 2.85,
        "meters": 6.1,
        "cut_sheet": [{"cut_height": 2.85}, {"cut_height": 3.25, "kind": "drop"}],
    }
    run = {"id": 1, "window_id": 1, "fabric_id": 1,
           "window_name": "w", "fabric_name": "f", "result": result}
    doc = cut_sheet.build_cut_sheet(run)
    assert [line["cut_height"] for line in doc["lines"]] == [2.85, 3.25]
    assert doc["lines"][1]["kind"] == "drop"
    assert doc["totals"] == {"panels": 2, "meters": 6.1}
    assert cut_sheet.validate_cut_sheet(doc) == []


def test_export_api_404_without_runs(monkeypatch):
    monkeypatch.setattr(history, "list_runs", lambda limit=50: [])
    with pytest.raises(HTTPException):
        exports_router.export_cut_sheet()
