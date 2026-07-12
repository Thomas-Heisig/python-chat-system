from app.models.backends.transformers_backend import TransformersBackend


class _FakeTensor:
    def __init__(self, length: int) -> None:
        self.shape = (1, length)

    def to(self, _device: str):
        return self


class _FakeTokenizer:
    def __init__(self) -> None:
        self.apply_args = None
        self.fallback_calls = 0

    def apply_chat_template(self, messages, **kwargs):
        self.apply_args = {
            "messages": messages,
            **kwargs,
        }
        return {
            "input_ids": _FakeTensor(4),
            "attention_mask": _FakeTensor(4),
        }

    def __call__(self, _prompt: str, return_tensors: str = "pt"):
        self.fallback_calls += 1
        return {
            "input_ids": _FakeTensor(3),
            "attention_mask": _FakeTensor(3),
        }

    def decode(self, _generated, skip_special_tokens: bool = True):
        return "Antwort"


class _FakeModel:
    def __init__(self) -> None:
        self.kwargs = None

    def generate(self, **kwargs):
        self.kwargs = kwargs
        return [[1, 2, 3, 4, 5, 6]]


def test_transformers_backend_uses_tokenizer_chat_template_for_structured_messages() -> None:
    backend = TransformersBackend()
    backend._loaded = True
    backend._device = "cpu"
    backend._tokenizer = _FakeTokenizer()
    backend._model = _FakeModel()

    result = backend.generate(
        prompt="legacy prompt should not be used",
        config={
            "chat_messages": [
                {"role": "system", "content": "Du bist hilfreich."},
                {"role": "user", "content": "Hallo"},
            ],
            "max_new_tokens": 32,
        },
    )

    tokenizer = backend._tokenizer
    model = backend._model
    assert result == "Antwort"
    assert tokenizer.apply_args is not None
    assert tokenizer.apply_args["add_generation_prompt"] is True
    assert tokenizer.apply_args["tokenize"] is True
    assert tokenizer.apply_args["return_dict"] is True
    assert tokenizer.apply_args["return_tensors"] == "pt"
    assert tokenizer.fallback_calls == 0
    assert model.kwargs is not None
