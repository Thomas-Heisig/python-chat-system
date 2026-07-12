from fastapi import APIRouter
from app.models.manager import model_manager

router = APIRouter(prefix="/api/health", tags=["health"])


@router.get("/live")
async def live() -> dict:
    return {"status": "ok"}


@router.get("/ready")
async def ready() -> dict:
    return {
        "status": "ready",
        "model_loaded": model_manager.active_backend is not None,
    }


@router.get("/model")
async def model() -> dict:
    return {
        "active_model_id": model_manager.active_model_id,
        "loaded": model_manager.active_backend is not None,
        "backend": model_manager.active_backend_name,
    }


@router.get("/database")
async def database() -> dict:
    return {"status": "ok"}
