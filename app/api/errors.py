from __future__ import annotations

from typing import Any

from fastapi import HTTPException


def build_error_envelope(
    *,
    code: str,
    message: str,
    retryable: bool,
    retry_after_seconds: int | None = None,
    details: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "error": {
            "code": code,
            "message": message,
            "retry": {
                "retryable": retryable,
                "after_seconds": retry_after_seconds,
            },
            "details": details or {},
        }
    }


def api_http_error(
    *,
    status_code: int,
    code: str,
    message: str,
    retryable: bool = False,
    retry_after_seconds: int | None = None,
    details: dict[str, Any] | None = None,
) -> HTTPException:
    return HTTPException(
        status_code=status_code,
        detail=build_error_envelope(
            code=code,
            message=message,
            retryable=retryable,
            retry_after_seconds=retry_after_seconds,
            details=details,
        ),
    )
