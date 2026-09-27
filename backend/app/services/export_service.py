"""裁幅清单导出：历史首条 run → 冻结 JSON + 主库追加一单。

刻意不依赖 fastapi，保证导出链路在核对命令/测试里可直接复用。
"""
from app.exports.cut_sheet import build_payload, write_frozen
from app.repositories import cut_sheet_orders, history


def export_latest_run():
    runs = history.list_runs(1)
    if not runs:
        raise LookupError("no runs to export")
    run = runs[0]
    payload = build_payload(run)
    path = write_frozen(payload)
    order_id = cut_sheet_orders.insert_order(
        run["id"], path, payload["content_checksum"]
    )
    return {
        "order_id": order_id,
        "run_id": run["id"],
        "path": str(path),
        "panels": payload["panels"],
        "meters": payload["meters"],
        "content_checksum": payload["content_checksum"],
    }
