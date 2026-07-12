from fastapi import APIRouter


router = APIRouter(prefix="/api/meta", tags=["meta"])


@router.get("/capabilities")
async def get_capabilities() -> dict[str, object]:
    return {
        "service": "python-chat-system",
        "version": "0.1.0",
        "features": {
            "meta.capabilities": True,
            "models.capabilities": True,
            "auth.users_presence": True,
            "auth.heartbeat": True,
            "chat.streaming_sse": True,
        },
    }
