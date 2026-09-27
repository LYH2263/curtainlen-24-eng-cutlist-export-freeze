from fastapi import APIRouter, HTTPException
from app.repositories import cut_sheet_orders
from app.services import export_service

router = APIRouter()


@router.post("/exports/cut-sheet")
def export_cut_sheet():
    try:
        return export_service.export_latest_run()
    except LookupError as e:
        raise HTTPException(404, str(e))


@router.get("/exports/cut-sheet/orders")
def list_cut_sheet_orders(limit: int = 50):
    return {"items": cut_sheet_orders.list_orders(limit)}
