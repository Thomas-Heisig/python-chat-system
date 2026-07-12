from collections.abc import AsyncIterator


async def as_sse(event: str, data: str) -> AsyncIterator[bytes]:
    payload = f"event: {event}\ndata: {data}\n\n"
    yield payload.encode("utf-8")
