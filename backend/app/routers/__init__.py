from fastapi import APIRouter
from app.routers import estimates, exports, fabrics, history_router, settings, windows
api_router = APIRouter(prefix="/api")
api_router.include_router(windows.router)
api_router.include_router(fabrics.router)
api_router.include_router(estimates.router)
api_router.include_router(history_router.router)
api_router.include_router(settings.router)
api_router.include_router(exports.router)
