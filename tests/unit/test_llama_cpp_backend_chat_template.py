import asyncio

from app.models.backends.llama_cpp_backend import LlamaCppBackend


class _FakeLlama:
    def __init__(self) -> None:
        self.chat_called = False
        self.completion_called = False

    def create_chat_completion(self, **kwargs):
        self.chat_called = True
        return {
            "choices": [
                {
                    "message": {
                        "content": "Antwort aus Chat-Template",
                    }
                }
            ]
        }

    def create_completion(self, **kwargs):
        self.completion_called = True
        return {
            "choices": [
                {
                    "text": "Fallback-Antwort",
                }
            ]
        }


class _FakeLlamaStream(_FakeLlama):
    def create_chat_completion(self, **kwargs):
        self.chat_called = True
        chunks = [
            {"choices": [{"delta": {"content": "Hallo"}}]},
            {"choices": [{"delta": {"content": " Welt"}}]},
        ]
        return iter(chunks)


def test_llama_cpp_backend_prefers_chat_completion_with_structured_messages() -> None:
    backend = LlamaCppBackend()
    backend._loaded = True
    backend._llm = _FakeLlama()

    result = backend.generate(
        prompt="legacy prompt",
        config={
            "chat_messages": [
                {"role": "system", "content": "Du bist hilfreich."},
                {"role": "user", "content": "Hallo"},
            ]
        },
    )

    llm = backend._llm
    assert result == "Antwort aus Chat-Template"
    assert llm.chat_called is True
    assert llm.completion_called is False


def test_llama_cpp_backend_stream_uses_chat_completion_with_structured_messages() -> None:
    backend = LlamaCppBackend()
    backend._loaded = True
    backend._llm = _FakeLlamaStream()

    async def _collect() -> str:
        chunks = []
        async for token in backend.stream(
            prompt="legacy prompt",
            config={
                "chat_messages": [
                    {"role": "system", "content": "Du bist hilfreich."},
                    {"role": "user", "content": "Hallo"},
                ]
            },
        ):
            chunks.append(token)
        return "".join(chunks)

    result = asyncio.run(_collect())

    llm = backend._llm
    assert result == "Hallo Welt"
    assert llm.chat_called is True
    assert llm.completion_called is False
