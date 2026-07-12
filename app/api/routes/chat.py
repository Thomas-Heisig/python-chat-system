import json
import asyncio
import importlib.util
import os
import threading
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse

from app.api.dependencies import chat_service_dependency
from app.api.errors import build_error_envelope
from app.chat.diagnostics_store import prompt_diagnostics_store
from app.chat.service import ChatService
from app.schemas.chat import ChatRequest

router = APIRouter(prefix="/api/chat", tags=["chat"])


def _diagnostics_api_enabled() -> bool:
    flag = os.getenv("LOCAL_PROMPT_DIAGNOSTICS", "").strip().lower()
    return flag in {"1", "true", "yes", "on"}


def _has_module(module_name: str) -> bool:
    try:
        return importlib.util.find_spec(module_name) is not None
    except Exception:
        return False


@router.get("/context-usage")
async def get_context_usage(
    user_id: int = 1,
    conversation_id: int | None = None,
    user_message: str = "",
    service: ChatService = Depends(chat_service_dependency),
) -> dict[str, object]:
    try:
        return await service.get_context_usage(
            user_id=user_id,
            conversation_id=conversation_id,
            user_message=user_message,
        )
    except ValueError as exc:
        if str(exc) == "conversation_not_found":
            raise HTTPException(status_code=404, detail="Conversation not found")
        raise


@router.get("/diagnostics/prompts")
async def get_prompt_diagnostics(
    user_id: int | None = None,
    limit: int = 20,
) -> dict[str, object]:
    if not _diagnostics_api_enabled():
        raise HTTPException(status_code=404, detail="Prompt diagnostics endpoint is disabled")

    entries = prompt_diagnostics_store.list_entries(user_id=user_id, limit=limit)
    return {
        "enabled": True,
        "items": entries,
        "dependencies": {
            "onnxruntime_installed": _has_module("onnxruntime"),
            "llama_cpp_installed": _has_module("llama_cpp"),
            "transformers_installed": _has_module("transformers"),
        },
    }


@router.post("/generate")
async def generate_chat_response(
    payload: ChatRequest,
    request: Request,
    service: ChatService = Depends(chat_service_dependency),
):
    if payload.stream:
        cancel_event = threading.Event()

        async def wait_for_disconnect() -> None:
            while not cancel_event.is_set():
                if await request.is_disconnected():
                    cancel_event.set()
                    return
                await asyncio.sleep(0.1)

        def build_event(event: str, payload_obj: dict[str, object]) -> str:
            return f"event: {event}\\ndata: {json.dumps(payload_obj, ensure_ascii=True)}\\n\\n"

        async def stream_gen():
            disconnect_task = asyncio.create_task(wait_for_disconnect())
            try:
                try:
                    async for item in service.stream_response(payload, cancel_event=cancel_event):
                        event = str(item.get("event", "token"))
                        data = item.get("data")
                        if not isinstance(data, dict):
                            data = {}
                        yield build_event(event, data)
                except ValueError as exc:
                    if str(exc) == "conversation_not_found":
                        yield build_event(
                            "error",
                            build_error_envelope(
                                code="conversation.not_found",
                                message="Conversation not found",
                                retryable=False,
                                details={
                                    "conversation_id": payload.conversation_id,
                                    "user_id": payload.user_id,
                                },
                            ),
                        )
                        return
                    raise
                except Exception:
                    yield build_event(
                        "error",
                        build_error_envelope(
                            code="stream.internal_error",
                            message="Streaming failed",
                            retryable=False,
                            details={
                                "conversation_id": payload.conversation_id,
                                "user_id": payload.user_id,
                            },
                        ),
                    )
                    return
            finally:
                cancel_event.set()
                disconnect_task.cancel()

        headers = {
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }

        return StreamingResponse(stream_gen(), media_type="text/event-stream", headers=headers)

    try:
        result = await service.generate_response(payload)
    except ValueError as exc:
        if str(exc) == "conversation_not_found":
            raise HTTPException(status_code=404, detail="Conversation not found")
        raise
    return result.model_dump()
