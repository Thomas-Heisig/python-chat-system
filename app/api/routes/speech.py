import json
import logging
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import Response
from pydantic import AliasChoices, BaseModel, ConfigDict, Field, field_validator, model_validator
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import db_session_dependency
from app.db_models.model_config import ModelConfig
from app.speech.service import speech_service

router = APIRouter(prefix="/api/speech", tags=["speech"])
logger = logging.getLogger(__name__)


class TtsRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    model_id: int = Field(validation_alias=AliasChoices("model_id", "modelId"))
    text: str = Field(min_length=1, max_length=20000)
    language: str = Field(default="auto", validation_alias=AliasChoices("language", "lang"))
    speaker: str = Field(default="", validation_alias=AliasChoices("speaker", "voice"))
    speed: float = Field(default=1.0, ge=0.5, le=2.0)
    device: str = Field(default="auto", validation_alias=AliasChoices("device", "compute_device", "computeDevice"))

    @model_validator(mode="before")
    @classmethod
    def _normalize_missing_values(cls, value: Any) -> Any:
        if not isinstance(value, dict):
            return value
        data = dict(value)
        if data.get("model_id") in {None, ""} and data.get("modelId") not in {None, ""}:
            data["model_id"] = data["modelId"]
        if data.get("language") is None:
            data["language"] = "auto"
        if data.get("speaker") is None:
            data["speaker"] = ""
        if data.get("device") is None:
            data["device"] = "auto"
        if data.get("speed") in {None, ""}:
            data["speed"] = 1.0
        return data

    @field_validator("text", mode="before")
    @classmethod
    def _validate_text(cls, value: Any) -> str:
        if value is None:
            raise ValueError("text darf nicht leer sein")
        text = str(value).strip()
        if not text:
            raise ValueError("text darf nicht leer sein")
        return text

    @field_validator("language", mode="before")
    @classmethod
    def _normalize_language(cls, value: Any) -> str:
        if value is None:
            return "auto"
        text = str(value).strip()
        return text or "auto"

    @field_validator("speaker", mode="before")
    @classmethod
    def _normalize_speaker(cls, value: Any) -> str:
        if value is None:
            return ""
        return str(value).strip()

    @field_validator("device", mode="before")
    @classmethod
    def _normalize_device(cls, value: Any) -> str:
        if value is None:
            return "auto"
        text = str(value).strip().lower()
        if text not in {"auto", "cpu", "cuda"}:
            return "auto"
        return text

    @field_validator("speed", mode="before")
    @classmethod
    def _normalize_speed(cls, value: Any) -> float:
        if value in {None, ""}:
            return 1.0
        try:
            return float(value)
        except (TypeError, ValueError):
            return 1.0


async def _speech_model(session: AsyncSession, model_id: int, task: str) -> ModelConfig:
    model = (await session.execute(select(ModelConfig).where(ModelConfig.id == model_id))).scalar_one_or_none()
    if model is None:
        raise HTTPException(404, "Sprachmodell nicht gefunden")
    metadata = speech_service.metadata(model)
    actual = str(metadata.get("task_type") or model.model_type or "")
    if actual != task:
        raise HTTPException(400, f"Modell ist nicht fuer {task} klassifiziert")
    return model


@router.get("/models")
async def speech_models(session: AsyncSession = Depends(db_session_dependency)) -> dict[str, Any]:
    rows = (await session.execute(select(ModelConfig).order_by(ModelConfig.name))).scalars().all()
    items = []
    for model in rows:
        meta = speech_service.metadata(model)
        task = str(meta.get("task_type") or model.model_type or "")
        if task not in {"speech_to_text", "text_to_speech", "voice_activity_detection"}:
            continue
        family = str(meta.get("model_family") or "unknown")
        config: dict[str, Any] = {}
        try:
            config = json.loads((Path(model.model_path) / "config.json").read_text(encoding="utf-8"))
        except Exception:
            pass
        aliases = config.get("voice_aliases", {}) if isinstance(config, dict) else {}
        speakers = list(aliases.keys()) if isinstance(aliases, dict) else []
        if not speakers and family == "qwen" and isinstance(config, dict):
            talker_config = config.get("talker_config")
            if isinstance(talker_config, dict):
                spk_id = talker_config.get("spk_id")
                if isinstance(spk_id, dict):
                    speakers = [str(name) for name in spk_id.keys()]
        if not speakers and (Path(model.model_path) / "voices").is_dir():
            speakers = sorted({item.stem for item in (Path(model.model_path) / "voices").iterdir() if item.is_file()})
        if "kokoro" in model.name.lower():
            # Kokoro has no native German voice model, but "de" is supported via b-voice mapping.
            languages = ["auto", "de", "de-de", "en", "en-gb", "es", "fr", "it", "pt", "ja", "zh"]
        elif family == "qwen" and "tts" in model.name.lower():
            languages = ["auto", "de", "en", "zh", "ja", "ko", "fr", "es", "it", "pt", "ru"]
        elif "deu" in model.name.lower() or model.name.lower().endswith("-de"):
            languages = ["auto", "de"]
        else:
            languages = ["auto", "de", "en", "fr", "es", "it"]
        items.append({
            "id": model.id, "name": model.name, "task": task, "family": family,
            "backend": model.backend, "available": bool(model.is_available),
            "settings": {
                "languages": languages,
                "tasks": ["transcribe", "translate"] if task == "speech_to_text" and family == "whisper" else (["transcribe"] if task == "speech_to_text" else (["synthesize"] if task == "text_to_speech" else ["detect"])),
                "speakers": speakers or meta.get("speakers", []),
                "supports_timestamps": task == "speech_to_text",
                "supports_language": task == "text_to_speech" or family in {"whisper", "mms", "speecht5", "unknown", "qwen"},
            },
        })
    return {"items": items}


@router.post("/detect-activity")
async def detect_activity(
    model_id: int = Form(...), audio: UploadFile = File(...), threshold: float = Form(0.5), device: str = Form("auto"),
    session: AsyncSession = Depends(db_session_dependency),
) -> dict[str, Any]:
    model = await _speech_model(session, model_id, "voice_activity_detection")
    data = await audio.read()
    if not data or len(data) > 50 * 1024 * 1024:
        raise HTTPException(413, "Audiodatei ist leer oder groesser als 50 MB")
    try:
        return speech_service.detect_voice_activity(model, data, {"threshold": threshold, "device": device})
    except Exception as exc:
        raise HTTPException(422, f"VAD fehlgeschlagen: {exc}") from exc


@router.post("/transcribe")
async def transcribe(
    model_id: int = Form(...), audio: UploadFile = File(...), language: str = Form("auto"),
    task: str = Form("transcribe"), return_timestamps: bool = Form(False), chunk_length_s: int = Form(30),
    stride_length_s: int = Form(5), device: str = Form("auto"),
    vad_enabled: bool = Form(False), vad_model_id: int | None = Form(None), vad_threshold: float = Form(0.5),
    vad_padding_ms: int = Form(120), vad_merge_gap_ms: int = Form(180),
    session: AsyncSession = Depends(db_session_dependency),
) -> dict[str, Any]:
    model = await _speech_model(session, model_id, "speech_to_text")
    data = await audio.read()
    if not data or len(data) > 50 * 1024 * 1024:
        raise HTTPException(413, "Audiodatei ist leer oder groesser als 50 MB")

    vad_result: dict[str, Any] | None = None
    if vad_enabled and vad_model_id:
        vad_model = await _speech_model(session, vad_model_id, "voice_activity_detection")
        try:
            vad_result = speech_service.detect_voice_activity(
                vad_model,
                data,
                {"threshold": vad_threshold, "device": device},
            )
            if not bool(vad_result.get("speaking")):
                return {
                    "text": "",
                    "chunks": [],
                    "vad": vad_result,
                    "note": "no_speech_detected",
                }
            data = speech_service.apply_vad_precut(
                data,
                vad_result,
                padding_ms=vad_padding_ms,
                merge_gap_ms=vad_merge_gap_ms,
            )
        except Exception as exc:
            raise HTTPException(422, f"VAD-Precut fehlgeschlagen: {exc}") from exc

    try:
        result = speech_service.transcribe(model, data, locals())
        if vad_result is not None:
            result["vad"] = vad_result
        return result
    except Exception as exc:
        raise HTTPException(422, f"Transkription fehlgeschlagen: {exc}") from exc


@router.post("/synthesize")
async def synthesize(payload: TtsRequest, session: AsyncSession = Depends(db_session_dependency)) -> Response:
    model = await _speech_model(session, payload.model_id, "text_to_speech")
    try:
        wav, sample_rate = speech_service.synthesize(model, payload.text, payload.model_dump())
    except Exception as exc:
        logger.exception("TTS synthesis failed for model_id=%s", payload.model_id)
        raise HTTPException(422, f"Sprachausgabe fehlgeschlagen: {exc}") from exc
    return Response(wav, media_type="audio/wav", headers={"X-Sample-Rate": str(sample_rate)})
