"""Build, validate and export frozen cut-sheet documents from calc runs.

A cut-sheet document expands a run into one line item per panel (幅). If the
run result already carries a `cut_sheet` row list, those rows are normalized;
otherwise each of the `panels` rows replicates the run's `cut_height`.
"""
from app.repositories import history
from app.services import export_store
from app.services.checksum import content_checksum

SCHEMA = "cut-sheet/v1"


def _norm_line(seq: int, row: dict) -> dict:
    cut_height = round(float(row["cut_height"]), 3)
    meters = round(float(row.get("meters", cut_height)), 3)
    return {"seq": seq, "kind": str(row.get("kind", "panel")), "cut_height": cut_height, "meters": meters}


def build_lines(result: dict) -> list:
    panels = int(result["panels"])
    cut_height = float(result["cut_height"])
    rows = result.get("cut_sheet")
    if not rows:
        rows = [{"cut_height": cut_height} for _ in range(panels)]
    return [_norm_line(i + 1, row) for i, row in enumerate(rows)]


def build_totals(lines: list) -> dict:
    return {"panels": len(lines), "meters": round(sum(line["meters"] for line in lines), 2)}


def build_cut_sheet(run: dict) -> dict:
    """Frozen document for one history run; no wall-clock fields, so the same
    run always exports to identical bytes."""
    result = run["result"]
    lines = build_lines(result)
    totals = build_totals(lines)
    doc = {
        "schema": SCHEMA,
        "source": {
            "run_id": run["id"],
            "window_id": run["window_id"],
            "fabric_id": run["fabric_id"],
        },
        "window_name": run.get("window_name", ""),
        "fabric_name": run.get("fabric_name", ""),
        "panels": totals["panels"],
        "meters": totals["meters"],
        "cut_height": round(float(result["cut_height"]), 3),
        "lines": lines,
        "totals": totals,
    }
    doc["content_checksum"] = content_checksum(lines, totals)
    return doc


def validate_cut_sheet(doc: dict) -> list:
    """Check a frozen document's internal consistency and checksum.

    Returns a list of human-readable errors; empty means the document is a
    valid frozen export. This is executable validation, not documentation.
    """
    errors = []
    for key in ("panels", "meters", "lines", "totals", "content_checksum"):
        if key not in doc:
            errors.append(f"missing key: {key}")
    if errors:
        return errors
    lines, totals = doc["lines"], doc["totals"]
    if not isinstance(lines, list) or not lines:
        errors.append("lines must be a non-empty list")
        return errors
    if [line.get("seq") for line in lines] != list(range(1, len(lines) + 1)):
        errors.append("line seq must run 1..N")
    if doc["panels"] != len(lines):
        errors.append(f"panels {doc['panels']} != line count {len(lines)}")
    if totals.get("panels") != doc["panels"]:
        errors.append("totals.panels != panels")
    for line in lines:
        if float(line.get("meters", 0)) <= 0 or float(line.get("cut_height", 0)) <= 0:
            errors.append(f"line {line.get('seq')} has non-positive meters/cut_height")
    if round(sum(float(line["meters"]) for line in lines), 2) != round(float(totals.get("meters", 0)), 2):
        errors.append("sum of line meters != totals.meters")
    if round(float(totals.get("meters", 0)), 2) != round(float(doc["meters"]), 2):
        errors.append("totals.meters != meters")
    if content_checksum(lines, totals) != doc["content_checksum"]:
        errors.append("content_checksum mismatch")
    return errors


def export_latest_cut_sheet(exports_dir=None) -> dict:
    """Freeze the newest history run to the in-repo JSON export."""
    runs = history.list_runs(1)
    if not runs:
        raise LookupError("no calc runs in history")
    doc = build_cut_sheet(runs[0])
    path = export_store.write_export(doc, exports_dir)
    return {
        "path": str(path),
        "run_id": doc["source"]["run_id"],
        "panels": doc["panels"],
        "meters": doc["meters"],
        "lines": len(doc["lines"]),
        "content_checksum": doc["content_checksum"],
    }
