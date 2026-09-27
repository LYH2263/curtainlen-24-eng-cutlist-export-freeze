from datetime import datetime, timezone
from app.db import connect


def insert_order(run_id, path, checksum):
    """导出后在主库额外保存一单（只追加，不回写已冻结文件）。"""
    c = connect()
    try:
        cur = c.execute(
            "INSERT INTO cut_sheet_orders(run_id,path,checksum,created_at) VALUES (?,?,?,?)",
            (run_id, str(path), checksum, datetime.now(timezone.utc).isoformat()),
        )
        c.commit()
        return int(cur.lastrowid)
    finally:
        c.close()


def list_orders(limit=50):
    c = connect()
    try:
        rows = c.execute(
            "SELECT * FROM cut_sheet_orders ORDER BY id DESC LIMIT ?", (limit,)
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        c.close()


def latest_order():
    rows = list_orders(1)
    return rows[0] if rows else None
