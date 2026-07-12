from collections.abc import Mapping
from typing import Any, cast

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.types import ExceptionHandler

from app.api.errors import build_error_envelope
from app.core.exceptions import ChatSystemError


def _default_code_for_status(status_code: int) -> str:
    mapping = {
        400: "bad_request",
        401: "unauthorized",
        403: "forbidden",
        404: "not_found",
        409: "conflict",
        422: "validation_error",
        429: "rate_limited",
        500: "internal_error",
        503: "service_unavailable",
    }
    return mapping.get(status_code, f"http_{status_code}")


def _parse_retry_after(headers: Mapping[str, str] | None) -> int | None:
    if not headers:
        return None
    value = headers.get("Retry-After") or headers.get("retry-after")
    if value is None:
        return None
    value = value.strip()
    return int(value) if value.isdigit() else None


def _normalize_http_detail(
    *,
    status_code: int,
    detail: object,
    request: Request,
    retry_after_seconds: int | None,
) -> dict[str, Any]:
    default_retryable = status_code in {429, 503, 504}
    default_details: dict[str, Any] = {
        "path": request.url.path,
        "method": request.method,
    }

    if isinstance(detail, dict):
        detail_map = cast(dict[str, Any], detail)
        existing_error = detail_map.get("error")
        if isinstance(existing_error, dict):
            error_map = cast(dict[str, Any], existing_error)
            code_raw = error_map.get("code")
            code = str(code_raw) if code_raw is not None else _default_code_for_status(status_code)
            message_raw = error_map.get("message")
            message = str(message_raw) if message_raw is not None else "Request failed"

            retry = error_map.get("retry")
            retryable = default_retryable
            after_seconds = retry_after_seconds
            if isinstance(retry, dict):
                retry_map = cast(dict[str, Any], retry)
                retryable_raw = retry_map.get("retryable")
                if isinstance(retryable_raw, bool):
                    retryable = retryable_raw
                retry_after_raw = retry_map.get("after_seconds")
                if isinstance(retry_after_raw, int):
                    after_seconds = retry_after_raw

            details_raw = error_map.get("details")
            details = dict(default_details)
            if isinstance(details_raw, dict):
                details.update(cast(dict[str, Any], details_raw))

            return build_error_envelope(
                code=code,
                message=message,
                retryable=retryable,
                retry_after_seconds=after_seconds,
                details=details,
            )

        return build_error_envelope(
            code=_default_code_for_status(status_code),
            message="Request failed",
            retryable=default_retryable,
            retry_after_seconds=retry_after_seconds,
            details={**default_details, "detail": detail},
        )

    if isinstance(detail, str):
        return build_error_envelope(
            code=_default_code_for_status(status_code),
            message=detail,
            retryable=default_retryable,
            retry_after_seconds=retry_after_seconds,
            details=default_details,
        )

    return build_error_envelope(
        code=_default_code_for_status(status_code),
        message="Request failed",
        retryable=default_retryable,
        retry_after_seconds=retry_after_seconds,
        details={**default_details, "detail": detail},
    )


async def chat_error_handler(request: Request, exc: Exception) -> JSONResponse:
    if not isinstance(exc, ChatSystemError):
        exc = ChatSystemError(str(exc))
    return JSONResponse(
        status_code=400,
        content=build_error_envelope(
            code=exc.__class__.__name__.lower(),
            message=str(exc),
            retryable=False,
            details={"path": request.url.path, "method": request.method},
        ),
    )


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    retry_after_seconds = _parse_retry_after(exc.headers)
    content = _normalize_http_detail(
        status_code=exc.status_code,
        detail=exc.detail,
        request=request,
        retry_after_seconds=retry_after_seconds,
    )
    return JSONResponse(
        status_code=exc.status_code,
        content=content,
        headers=exc.headers,
    )


async def request_validation_error_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    return JSONResponse(
        status_code=422,
        content=build_error_envelope(
            code="validation_error",
            message="Request validation failed",
            retryable=False,
            details={
                "path": request.url.path,
                "method": request.method,
                "errors": exc.errors(),
            },
        ),
    )


async def unhandled_exception_handler(request: Request, _: Exception) -> JSONResponse:
    return JSONResponse(
        status_code=500,
        content=build_error_envelope(
            code="internal_error",
            message="Unexpected server error",
            retryable=False,
            details={"path": request.url.path, "method": request.method},
        ),
    )


def register_error_handlers(app: FastAPI) -> None:
    app.add_exception_handler(ChatSystemError, cast(ExceptionHandler, chat_error_handler))
    app.add_exception_handler(HTTPException, cast(ExceptionHandler, http_exception_handler))
    app.add_exception_handler(RequestValidationError, cast(ExceptionHandler, request_validation_error_handler))
    app.add_exception_handler(Exception, cast(ExceptionHandler, unhandled_exception_handler))
