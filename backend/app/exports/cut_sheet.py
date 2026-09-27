"""裁幅清单载荷构建与冻结写盘。

导出即冻结：写盘后主库再发生任何变化，文件字节与 checksum 都保持不变。
只依赖标准库，核对命令可直接复用本模块的构建逻辑。
"""
import json
import os
from pathlib import Path

from app.exports.checksum import content_checksum

SCHEMA = "cut_sheet/v1"


def default_export_dir() -> Path:
    """仓库内 exports/ 目录（可用 EXPORT_DIR 覆盖）。"""
    if os.environ.get("EXPORT_DIR"):
        return Path(os.environ["EXPORT_DIR"])
    return Path(__file__).resolve().parents[3] / "exports"


def build_line_items(result: dict) -> list:
    """按幅展开行项目。

    若 result 已含 cut_sheet 则按它展开；否则用 panels 份数复制 cut_height。
    """
    cut_sheet = result.get("cut_sheet")
    if cut_sheet:
        return [
            {
                "panel_no": i + 1,
                "cut_height": round(float(row["cut_height"]), 3),
                "width": round(float(row.get("width", result["fabric_width"])), 3),
            }
            for i, row in enumerate(cut_sheet)
        ]
    panels = int(result["panels"])
    cut_height = round(float(result["cut_height"]), 3)
    width = round(float(result["fabric_width"]), 3)
    return [
        {"panel_no": i + 1, "cut_height": cut_height, "width": width}
        for i in range(panels)
    ]


def build_payload(run: dict) -> dict:
    """由一条历史 run 构建冻结载荷（含 checksum）。"""
    result = run["result"]
    line_items = build_line_items(result)
    totals = {
        "panels": int(result["panels"]),
        "meters": round(float(result["meters"]), 2),
        "cut_height": round(float(result["cut_height"]), 3),
    }
    payload = {
        "schema": SCHEMA,
        "run_id": run["id"],
        "window_name": run.get("window_name"),
        "fabric_name": run.get("fabric_name"),
        "created_at": run.get("created_at"),
        "panels": totals["panels"],
        "meters": totals["meters"],
        "line_items": line_items,
        "totals": totals,
    }
    payload["content_checksum"] = content_checksum(line_items, totals)
    return payload


def freeze_bytes(payload: dict) -> bytes:
    """冻结序列化：与 checksum 同样的确定性规则，保证字节稳定。"""
    text = json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2)
    return (text + "\n").encode("utf-8")


def export_path_for(run_id: int, export_dir: Path | None = None) -> Path:
    d = export_dir or default_export_dir()
    return d / f"cut_sheet_run_{run_id}.json"


def write_frozen(payload: dict, export_dir: Path | None = None) -> Path:
    """把载荷写成仓库内 JSON 文件，返回路径。已存在则覆盖为相同字节。"""
    path = export_path_for(payload["run_id"], export_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(freeze_bytes(payload))
    return path
