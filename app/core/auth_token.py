from __future__ import annotations

import base64
import hashlib
import hmac
import json
from datetime import datetime, timedelta, timezone

from app.core.config import get_config

TOKEN_TTL_HOURS = 12


def _urlsafe_b64encode(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")


def _urlsafe_b64decode(raw: str) -> bytes:
    padding = "=" * (-len(raw) % 4)
    return base64.urlsafe_b64decode((raw + padding).encode("ascii"))


def _sign(payload_b64: str) -> str:
    secret = get_config().secret_key.encode("utf-8")
    digest = hmac.new(secret, payload_b64.encode("ascii"), hashlib.sha256).digest()
    return _urlsafe_b64encode(digest)


def issue_access_token(user_id: int, ttl_hours: int = TOKEN_TTL_HOURS) -> str:
    expires_at = datetime.now(timezone.utc) + timedelta(hours=max(1, ttl_hours))
    payload = {
        "uid": int(user_id),
        "exp": int(expires_at.timestamp()),
    }
    payload_raw = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    payload_b64 = _urlsafe_b64encode(payload_raw)
    signature = _sign(payload_b64)
    return f"{payload_b64}.{signature}"


def verify_access_token(token: str) -> int | None:
    if not token or "." not in token:
        return None

    try:
        payload_b64, signature = token.split(".", 1)
    except ValueError:
        return None

    expected_signature = _sign(payload_b64)
    if not hmac.compare_digest(signature, expected_signature):
        return None

    try:
        payload = json.loads(_urlsafe_b64decode(payload_b64).decode("utf-8"))
        user_id = int(payload["uid"])
        expires_epoch = int(payload["exp"])
    except (ValueError, TypeError, KeyError, json.JSONDecodeError):
        return None

    now_epoch = int(datetime.now(timezone.utc).timestamp())
    if expires_epoch <= now_epoch:
        return None

    return user_id
