"""Export API: freeze the latest history run as an in-repo cut-sheet JSON."""
from fastapi import APIRouter, HTTPException

from app.services import cut_sheet, export_store

router = APIRouter()


@router.post("/exports/cut-sheet")
def export_cut_sheet():
    try:
        return cut_sheet.export_latest_cut_sheet()
    except LookupError as exc:
        raise HTTPException(404, str(exc))


@router.get("/exports/cut-sheet")
def read_cut_sheet():
    path = export_store.export_path()
    if not path.exists():
        raise HTTPException(404, "no frozen cut-sheet export")
    return export_store.read_export()
