import json

import pytest

from app import seed
from app.engines.curtain_math import fabric_meters
from app.exports.checksum import content_checksum
from app.exports.cut_sheet import build_line_items, build_payload
from app.repositories import cut_sheet_orders, history
from app.services import export_service
from app.verify_cut_sheet import main as verify_main


@pytest.fixture()
def db(tmp_path, monkeypatch):
    monkeypatch.setattr("app.db.DB_PATH", tmp_path / "app.db")
    monkeypatch.setattr("app.config.DB_PATH", tmp_path / "app.db")
    monkeypatch.setattr("app.verify_cut_sheet.DB_PATH", tmp_path / "app.db")
    seed.init_db()
    return tmp_path / "app.db"


@pytest.fixture()
def export_dir(tmp_path, monkeypatch):
    d = tmp_path / "exports"
    monkeypatch.setenv("EXPORT_DIR", str(d))
    return d


def _save_run(note=""):
    calc = fabric_meters(3.0, 2.6, 2.0, 0.10, 0.15, 1.4)
    return history.insert_run(1, 1, calc, note)


def test_export_freeze_survives_later_writes(db, export_dir):
    _save_run("first")
    out = export_service.export_latest_run()
    frozen = export_dir / f"cut_sheet_run_{out['run_id']}.json"
    bytes_before = frozen.read_bytes()
    checksum_before = out["content_checksum"]

    # 导出后再在主库额外保存一单（新 run + 新 order），不重新导出
    _save_run("after-export")
    cut_sheet_orders.insert_order(999, "/tmp/elsewhere.json", "sha256:whatever")

    assert frozen.read_bytes() == bytes_before
    assert json.loads(frozen.read_text())["content_checksum"] == checksum_before


def test_verify_command_twice_exit_zero(db, export_dir):
    _save_run()
    export_service.export_latest_run()
    assert verify_main([]) == 0
    assert verify_main([]) == 0


def test_verify_detects_tamper(db, export_dir):
    _save_run()
    out = export_service.export_latest_run()
    frozen = export_dir / f"cut_sheet_run_{out['run_id']}.json"
    payload = json.loads(frozen.read_text())
    payload["line_items"][0]["cut_height"] = 9.99
    frozen.write_text(json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2) + "\n")
    assert verify_main([]) == 1


def test_line_items_fallback_copies_cut_height():
    result = {"panels": 3, "cut_height": 2.85, "fabric_width": 1.4}
    items = build_line_items(result)
    assert len(items) == 3
    assert [i["panel_no"] for i in items] == [1, 2, 3]
    assert all(i["cut_height"] == 2.85 for i in items)


def test_line_items_prefer_existing_cut_sheet():
    result = {
        "panels": 2,
        "cut_height": 2.85,
        "fabric_width": 1.4,
        "cut_sheet": [{"cut_height": 2.85, "width": 1.4}, {"cut_height": 2.8, "width": 1.4}],
    }
    items = build_line_items(result)
    assert [i["cut_height"] for i in items] == [2.85, 2.8]


def test_payload_contains_required_fields(db):
    _save_run()
    run = history.list_runs(1)[0]
    p = build_payload(run)
    assert p["panels"] == 5 and p["meters"] == 14.25
    assert len(p["line_items"]) == 5
    assert p["content_checksum"] == content_checksum(p["line_items"], p["totals"])


def test_checksum_is_stable_against_key_order():
    items = [{"panel_no": 1, "cut_height": 2.85, "width": 1.4}]
    totals = {"panels": 1, "meters": 2.85, "cut_height": 2.85}
    a = content_checksum(items, totals)
    b = content_checksum(
        [dict(reversed(list(items[0].items())))],
        dict(reversed(list(totals.items()))),
    )
    assert a == b
    assert a.startswith("sha256:")
