"""核对命令：校验已冻结的裁幅清单 JSON。

用法（backend 目录下）：
    python3 -m app.verify_cut_sheet            # 核对 exports/ 下全部冻结文件
    python3 -m app.verify_cut_sheet <file>     # 核对指定文件

逐项校验：
  1. 文件字节等于自身载荷的冻结序列化（字节稳定）；
  2. content_checksum 等于对 line_items+totals 重算的稳定哈希；
  3. panels/米数与行项目自洽；
  4. 主库可查时：run 仍存在且按当前库数据重算的 checksum 不变（导出即冻结）。

全部通过退出码 0，否则 1。只读，可反复执行。
"""
import json
import sqlite3
import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from app.config import DB_PATH
from app.exports.checksum import content_checksum
from app.exports.cut_sheet import SCHEMA, build_payload, default_export_dir, freeze_bytes


def _fail(path, problems, msg):
    problems.append(f"{path}: {msg}")


def check_file(path: Path, db_runs: dict | None, problems: list) -> bool:
    ok = True
    try:
        raw = path.read_bytes()
        payload = json.loads(raw.decode("utf-8"))
    except (OSError, ValueError) as e:
        _fail(path, problems, f"unreadable or invalid JSON: {e}")
        return False

    if payload.get("schema") != SCHEMA:
        _fail(path, problems, f"schema mismatch: {payload.get('schema')!r}")
        ok = False

    line_items = payload.get("line_items")
    totals = payload.get("totals")
    if not isinstance(line_items, list) or not isinstance(totals, dict):
        _fail(path, problems, "missing line_items/totals")
        return False

    # 2. checksum 重算
    want = content_checksum(line_items, totals)
    if payload.get("content_checksum") != want:
        _fail(path, problems, f"checksum mismatch: file={payload.get('content_checksum')} recomputed={want}")
        ok = False

    # 1. 字节稳定：重新冻结序列化必须逐字节相等
    if freeze_bytes(payload) != raw:
        _fail(path, problems, "bytes not stable: re-frozen serialization differs")
        ok = False

    # 3. 自洽：panels 与行数、米数与合计
    if payload.get("panels") != len(line_items) or totals.get("panels") != len(line_items):
        _fail(path, problems, f"panels inconsistent: payload={payload.get('panels')} totals={totals.get('panels')} rows={len(line_items)}")
        ok = False
    for i, row in enumerate(line_items):
        if row.get("panel_no") != i + 1:
            _fail(path, problems, f"panel_no gap at index {i}")
            ok = False
            break
    if round(sum(float(r["cut_height"]) for r in line_items), 2) != float(totals.get("meters", -1)):
        _fail(path, problems, "sum of cut_height != totals.meters")
        ok = False
    if payload.get("meters") != totals.get("meters"):
        _fail(path, problems, "payload.meters != totals.meters")
        ok = False

    # 4. 主库交叉核对：run 仍在且重算 checksum 不变
    if db_runs is not None:
        run = db_runs.get(payload.get("run_id"))
        if run is None:
            _fail(path, problems, f"run_id={payload.get('run_id')} not found in main DB")
            ok = False
        else:
            rebuilt = build_payload(run)
            if rebuilt["content_checksum"] != payload.get("content_checksum"):
                _fail(path, problems, "frozen checksum differs from checksum rebuilt from current DB run")
                ok = False
    return ok


def _load_runs():
    if not DB_PATH.exists():
        return None
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            """SELECT r.*, w.name window_name, f.name fabric_name FROM calc_runs r
            LEFT JOIN windows w ON w.id=r.window_id LEFT JOIN fabrics f ON f.id=r.fabric_id"""
        ).fetchall()
        conn.close()
    except sqlite3.Error:
        return None
    out = {}
    for row in rows:
        d = dict(row)
        d["result"] = json.loads(d.pop("result_json"))
        out[d["id"]] = d
    return out


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv:
        files = [Path(a) for a in argv]
    else:
        d = default_export_dir()
        files = sorted(d.glob("cut_sheet_run_*.json")) if d.is_dir() else []
    if not files:
        print("FAIL: no frozen cut-sheet files found", file=sys.stderr)
        return 1

    db_runs = _load_runs()
    if db_runs is None:
        print("note: main DB not reachable, skipping DB cross-check", file=sys.stderr)

    problems: list = []
    for f in files:
        if check_file(f, db_runs, problems):
            print(f"OK {f}")
    if problems:
        for p in problems:
            print(f"FAIL {p}", file=sys.stderr)
        return 1
    print(f"verified {len(files)} frozen file(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
