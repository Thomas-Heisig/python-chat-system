from __future__ import annotations

import io
import json
import os
import re
import tempfile
import threading
import wave
import inspect
from glob import glob
from pathlib import Path
from typing import Any

from app.db_models.model_config import ModelConfig


class SpeechService:
    """Lazily owns speech pipelines without interfering with the active chat model."""

    def __init__(self) -> None:
        self._pipelines: dict[tuple[int, str, str], Any] = {}
        self._lock = threading.RLock()

    @staticmethod
    def metadata(model: ModelConfig) -> dict[str, Any]:
        try:
            value = json.loads(model.metadata_json or "{}")
            return value if isinstance(value, dict) else {}
        except Exception:
            return {}

    def _pipeline(self, model: ModelConfig, task: str, device: str) -> Any:
        normalized_device = device if device in {"auto", "cpu", "cuda"} else "auto"
        key = (model.id, task, normalized_device)
        with self._lock:
            if key in self._pipelines:
                return self._pipelines[key]
            try:
                import torch
                from transformers import pipeline
            except ImportError as exc:
                raise RuntimeError("transformers und torch werden fuer lokale Sprachmodelle benoetigt") from exc
            device_index = -1
            if normalized_device == "cuda" or (normalized_device == "auto" and torch.cuda.is_available()):
                device_index = 0
            pipe = pipeline(task, model=str(Path(model.model_path).resolve()), device=device_index)
            self._pipelines[key] = pipe
            return pipe

    @staticmethod
    def _is_kokoro_model(model: ModelConfig) -> bool:
        model_path = Path(model.model_path)
        if "kokoro" in model.name.lower():
            return True
        if (model_path / "kokoro-v1_0.pth").is_file() and (model_path / "voices").is_dir():
            return True
        return False

    @staticmethod
    def _is_qwen3_tts_model(model: ModelConfig) -> bool:
        name = model.name.lower()
        if "qwen3-tts" in name:
            return True
        config_path = Path(model.model_path) / "config.json"
        try:
            payload = json.loads(config_path.read_text(encoding="utf-8"))
            return str(payload.get("model_type") or "").strip().lower() == "qwen3_tts"
        except Exception:
            return False

    @staticmethod
    def _is_kitten_tts_model(model: ModelConfig) -> bool:
        model_path = Path(model.model_path)
        if "kitten" in model.name.lower():
            return True
        if (model_path / "voices.npz").is_file() and any(model_path.glob("*.onnx")):
            return True
        return False

    @staticmethod
    def _kokoro_lang_code(language: str, speaker: str) -> str:
        speaker_value = speaker.strip().lower()
        if speaker_value and "_" in speaker_value and speaker_value[0].isalpha():
            return speaker_value[0]

        normalized = language.strip().lower()
        mapping = {
            "en": "a",
            "en-us": "a",
            "en-gb": "b",
            "de": "b",
            "de-de": "b",
            "de-at": "b",
            "de-ch": "b",
            "german": "b",
            "ja": "j",
            "zh": "z",
            "es": "e",
            "fr": "f",
            "hi": "h",
            "it": "i",
            "pt": "p",
            "pt-br": "p",
        }
        if normalized in mapping:
            return mapping[normalized]
        return "a"

    @staticmethod
    def _qwen3_tts_language(value: str) -> str:
        normalized = (value or "").strip().lower()
        mapping = {
            "": "German",
            "auto": "German",
            "de": "German",
            "de-de": "German",
            "en": "English",
            "en-us": "English",
            "en-gb": "English",
            "fr": "French",
            "es": "Spanish",
            "it": "Italian",
            "pt": "Portuguese",
            "ru": "Russian",
            "ja": "Japanese",
            "ko": "Korean",
            "zh": "Chinese",
        }
        return mapping.get(normalized, (normalized.capitalize() if normalized else "German"))

    @staticmethod
    def _qwen3_tts_default_speaker(model_path: Path) -> str:
        config_path = model_path / "config.json"
        try:
            payload = json.loads(config_path.read_text(encoding="utf-8"))
        except Exception:
            return "Ryan"
        talker = payload.get("talker_config") if isinstance(payload, dict) else None
        if not isinstance(talker, dict):
            return "Ryan"
        spk_id = talker.get("spk_id")
        if isinstance(spk_id, dict) and spk_id:
            for preferred in ("ryan", "aiden", "vivian", "serena"):
                for name in spk_id:
                    if str(name).strip().lower() == preferred:
                        return str(name)
            first = next(iter(spk_id.keys()))
            return str(first)
        return "Ryan"

    @staticmethod
    def _default_kokoro_speaker(model_path: Path, lang_code: str) -> str:
        voices_dir = model_path / "voices"
        if not voices_dir.is_dir():
            return "af_heart"
        candidates = sorted(Path(item).stem for item in glob(str(voices_dir / f"{lang_code}*_*.pt")))
        if candidates:
            return candidates[0]
        all_candidates = sorted(Path(item).stem for item in glob(str(voices_dir / "*.pt")))
        if all_candidates:
            return all_candidates[0]
        return "af_heart"

    def _kokoro_pipeline(self, model: ModelConfig, lang_code: str, device: str) -> Any:
        normalized_device = device if device in {"auto", "cpu", "cuda"} else "auto"
        key = (model.id, f"kokoro:{lang_code}", normalized_device)
        with self._lock:
            if key in self._pipelines:
                return self._pipelines[key]
            try:
                from kokoro import KModel, KPipeline
            except ImportError as exc:
                raise RuntimeError(
                    "Kokoro-TTS benoetigt das Paket 'kokoro'. Installiere z. B. 'pip install kokoro>=0.9.2'."
                ) from exc

            model_path = Path(model.model_path).resolve()
            preferred_device = normalized_device
            if preferred_device == "auto":
                try:
                    import torch
                    preferred_device = "cuda" if torch.cuda.is_available() else "cpu"
                except Exception:
                    preferred_device = "cpu"

            pipeline: Any
            config_path = model_path / "config.json"
            weights = sorted(model_path.glob("kokoro-*.pth"))
            if config_path.is_file() and weights:
                local_model = KModel(config=str(config_path), model=str(weights[0]))
                try:
                    local_model = local_model.to(preferred_device).eval()
                except Exception:
                    local_model = local_model.to("cpu").eval()
                pipeline = KPipeline(
                    lang_code=lang_code,
                    repo_id="hexgrad/Kokoro-82M",
                    model=local_model,
                )
            else:
                pipeline = KPipeline(
                    lang_code=lang_code,
                    repo_id="hexgrad/Kokoro-82M",
                    device=preferred_device,
                )

            self._pipelines[key] = pipeline
            return pipeline

    def _synthesize_kokoro(self, model: ModelConfig, text: str, options: dict[str, Any]) -> tuple[bytes, int]:
        language = str(options.get("language") or "auto")
        speaker = str(options.get("speaker") or "").strip()
        speed = float(options.get("speed", 1.0))
        lang_code = self._kokoro_lang_code(language, speaker)

        model_path = Path(model.model_path)
        if not speaker:
            speaker = self._default_kokoro_speaker(model_path, lang_code)
        voice_path = model_path / "voices" / f"{speaker}.pt"
        voice = str(voice_path) if voice_path.is_file() else speaker

        pipeline = self._kokoro_pipeline(model, lang_code, str(options.get("device", "auto")))

        try:
            generator = pipeline(text, voice=voice, speed=speed)
        except TypeError:
            generator = pipeline(text, voice=voice)

        chunks: list[Any] = []
        for item in generator:
            audio_chunk: Any = None
            if hasattr(item, "audio"):
                audio_chunk = getattr(item, "audio")
            elif isinstance(item, tuple) and len(item) >= 3:
                audio_chunk = item[2]
            if audio_chunk is None:
                continue
            chunks.append(audio_chunk)

        if not chunks:
            raise RuntimeError("Kokoro lieferte keine Audiodaten.")

        try:
            import numpy as np
        except ImportError as exc:
            raise RuntimeError("numpy wird fuer Kokoro-TTS benoetigt.") from exc

        audio = np.concatenate([np.asarray(chunk, dtype=np.float32).reshape(-1) for chunk in chunks])
        sample_rate = 24000
        return self._wav(audio, sample_rate, speed), sample_rate

    def _qwen3_tts_runtime(self, model: ModelConfig, device: str) -> Any:
        normalized_device = device if device in {"auto", "cpu", "cuda"} else "auto"
        key = (model.id, "qwen3-tts", normalized_device)
        with self._lock:
            if key in self._pipelines:
                return self._pipelines[key]
            try:
                import torch
                import transformers.masking_utils as masking_utils
                import transformers.modeling_utils as modeling_utils
                import transformers.modeling_rope_utils as rope_utils
                import transformers.utils.generic as transformers_generic

                # qwen-tts only needs the decorator for model-input tracing.
                # In this environment the wrapped variant is brittle, so we
                # replace it with a no-op to preserve the original signature.
                check_fn = getattr(transformers_generic, "check_model_inputs", None)
                if callable(check_fn):
                    def _compat_check_model_inputs(func: Any = None, *args: Any, **kwargs: Any) -> Any:
                        if func is None:
                            def _decorator(inner: Any) -> Any:
                                return inner

                            return _decorator
                        return func

                    transformers_generic.check_model_inputs = _compat_check_model_inputs

                # qwen-tts and transformers variants disagree on
                # `input_embeds` vs `inputs_embeds` in create_causal_mask.
                causal_mask_fn = getattr(masking_utils, "create_causal_mask", None)
                if callable(causal_mask_fn):
                    try:
                        causal_sig = inspect.signature(causal_mask_fn)
                        accepts_input_embeds = "input_embeds" in causal_sig.parameters
                        accepts_inputs_embeds = "inputs_embeds" in causal_sig.parameters

                        def _compat_create_causal_mask(*args: Any, **kwargs: Any) -> Any:
                            config = kwargs.get("config")
                            input_embeds = kwargs.get("input_embeds", kwargs.get("inputs_embeds"))
                            attention_mask = kwargs.get("attention_mask")
                            cache_pos = kwargs.get("cache_position")
                            position_ids = kwargs.get("position_ids")
                            past_key_values = kwargs.get("past_key_values")
                            or_mask_function = kwargs.get("or_mask_function")
                            and_mask_function = kwargs.get("and_mask_function")

                            if cache_pos is None:
                                cache_pos = position_ids
                            if cache_pos is None and input_embeds is not None:
                                try:
                                    import torch

                                    cache_pos = torch.arange(
                                        input_embeds.shape[1], device=getattr(input_embeds, "device", None)
                                    )
                                except Exception:
                                    cache_pos = None

                            if cache_pos is None:
                                raise TypeError("create_causal_mask() missing cache_position compatibility input")

                            if input_embeds is None and len(args) > 1:
                                input_embeds = args[1]
                            if attention_mask is None and len(args) > 2:
                                attention_mask = args[2]
                            if past_key_values is None and len(args) > 4:
                                past_key_values = args[4]
                            if position_ids is None and len(args) > 5:
                                position_ids = args[5]

                            return causal_mask_fn(
                                config,
                                input_embeds,
                                attention_mask,
                                cache_pos,
                                past_key_values,
                                position_ids=position_ids,
                                or_mask_function=or_mask_function,
                                and_mask_function=and_mask_function,
                            )

                        masking_utils.create_causal_mask = _compat_create_causal_mask
                        if hasattr(modeling_utils, "create_causal_mask"):
                            modeling_utils.create_causal_mask = _compat_create_causal_mask
                    except Exception:
                        pass

                # qwen-tts expects a legacy "default" RoPE init key which is
                # no longer present in newer transformers versions.
                rope_inits = getattr(rope_utils, "ROPE_INIT_FUNCTIONS", None)
                if isinstance(rope_inits, dict) and "default" not in rope_inits and "linear" in rope_inits:
                    linear_rope_init = rope_inits["linear"]

                    def _compat_default_rope(config: Any = None, device: Any = None, seq_len: int | None = None, layer_type: str | None = None) -> Any:
                        if config is not None:
                            rope_scaling = getattr(config, "rope_scaling", None)
                            if isinstance(rope_scaling, dict):
                                rope_scaling.setdefault("factor", 1.0)
                                rope_scaling.setdefault("rope_type", "linear")
                                setattr(config, "rope_scaling", rope_scaling)
                            elif rope_scaling is None:
                                setattr(config, "rope_scaling", {"rope_type": "linear", "factor": 1.0})
                        return linear_rope_init(config=config, device=device, seq_len=seq_len, layer_type=layer_type)

                    rope_inits["default"] = _compat_default_rope

                from qwen_tts import Qwen3TTSModel
                from qwen_tts.core.models.configuration_qwen3_tts import Qwen3TTSTalkerConfig
            except ImportError as exc:
                raise RuntimeError(
                    "Qwen3-TTS benoetigt das Paket 'qwen-tts' (inkl. passender Transformers-Version)."
                ) from exc
            except Exception as exc:
                raise RuntimeError(
                    "Qwen3-TTS Runtime konnte nicht geladen werden. Bitte `qwen-tts` mit kompatibler "
                    "Transformers-Version (z. B. 4.57.x) in einer separaten Umgebung installieren."
                ) from exc

            # Some qwen-tts builds expect talker_config.pad_token_id, while the
            # shipped config only exposes codec_pad_id. Add a runtime bridge.
            if not hasattr(Qwen3TTSTalkerConfig, "pad_token_id"):
                def _get_pad_token_id(self: Any) -> int:
                    return int(getattr(self, "codec_pad_id", 0) or 0)

                def _set_pad_token_id(self: Any, value: Any) -> None:
                    setattr(self, "codec_pad_id", int(value) if value is not None else 0)

                Qwen3TTSTalkerConfig.pad_token_id = property(_get_pad_token_id, _set_pad_token_id)

            model_path = str(Path(model.model_path).resolve())

            target_device = normalized_device
            if target_device == "auto":
                target_device = "cuda" if torch.cuda.is_available() else "cpu"
            dtype = torch.float16 if target_device == "cuda" else torch.float32
            try:
                runtime = Qwen3TTSModel.from_pretrained(
                    model_path,
                    device_map=target_device,
                    dtype=dtype,
                    attn_implementation="eager",
                )
            except Exception as exc:
                raise RuntimeError(
                    "Qwen3-TTS konnte nicht initialisiert werden. Die lokale Runtime ist vermutlich "
                    "inkompatibel zur installierten Transformers-Version."
                ) from exc
            self._pipelines[key] = runtime
            return runtime

    def _synthesize_qwen3_tts(self, model: ModelConfig, text: str, options: dict[str, Any]) -> tuple[bytes, int]:
        language = self._qwen3_tts_language(str(options.get("language") or "auto"))
        speaker = str(options.get("speaker") or "").strip()
        model_path = Path(model.model_path)
        if not speaker:
            speaker = self._qwen3_tts_default_speaker(model_path)
        runtime = self._qwen3_tts_runtime(model, str(options.get("device", "auto")))

        instruct = str(options.get("instruct") or "").strip()
        kwargs: dict[str, Any] = {
            "text": text,
            "language": language,
            "speaker": speaker,
        }
        if instruct:
            kwargs["instruct"] = instruct

        try:
            wavs, sample_rate = runtime.generate_custom_voice(**kwargs)
        except Exception as exc:
            message = str(exc)
            message_lower = message.lower()
            if (
                "cuda error" in message_lower
                or "device-side assert triggered" in message_lower
            ) and str(options.get("device", "auto")).strip().lower() in {"auto", "cuda"}:
                # Recover by forcing CPU runtime for this request.
                with self._lock:
                    self._pipelines.pop((model.id, "qwen3-tts", "cuda"), None)
                    self._pipelines.pop((model.id, "qwen3-tts", "auto"), None)
                try:
                    cpu_runtime = self._qwen3_tts_runtime(model, "cpu")
                    wavs, sample_rate = cpu_runtime.generate_custom_voice(**kwargs)
                except Exception as cpu_exc:
                    raise RuntimeError(
                        "Qwen3-TTS CUDA-Laufzeitfehler (device-side assert). "
                        "CPU-Fallback ist ebenfalls fehlgeschlagen. Bitte Backend neu starten und "
                        "kompatible Versionen pinnen (empfohlen: transformers 4.57.x)."
                    ) from cpu_exc
            elif "create_causal_mask" in message or "size of tensor" in message or "mat1 and mat2" in message:
                raise RuntimeError(
                    "Qwen3-TTS ist im aktuellen System noch nicht voll kompatibel. "
                    "Bitte `qwen-tts` und `transformers` in derselben .venv auf ein kompatibles Pair pinnen "
                    f"(empfohlen: transformers 4.57.x). Originalfehler: {message}"
                ) from exc
            else:
                raise
        if isinstance(wavs, (list, tuple)):
            if not wavs:
                raise RuntimeError("Qwen3-TTS lieferte keine Audiodaten.")
            audio = wavs[0]
        else:
            audio = wavs
        return self._wav(audio, int(sample_rate), float(options.get("speed", 1.0))), int(sample_rate)

    def _kitten_tts_runtime(self, model: ModelConfig) -> Any:
        key = (model.id, "kitten-tts", "cpu")
        with self._lock:
            if key in self._pipelines:
                return self._pipelines[key]
            try:
                from kittentts import KittenTTS
            except ImportError as exc:
                raise RuntimeError("Kitten-TTS benoetigt das Paket 'kittentts'.") from exc

            # Ensure phonemizer can find espeak-ng on Windows installations where
            # espeak is bundled via Python wheels instead of system PATH.
            try:
                from espeakng_loader import get_data_path, get_library_path
                from phonemizer.backend.espeak.wrapper import EspeakWrapper

                espeak_lib = str(get_library_path())
                espeak_data = str(get_data_path())
                os.environ.setdefault("PHONEMIZER_ESPEAK_LIBRARY", espeak_lib)
                os.environ.setdefault("PHONEMIZER_ESPEAK_DATA_PATH", espeak_data)
                EspeakWrapper.set_library(espeak_lib)
                EspeakWrapper.set_data_path(espeak_data)
            except Exception:
                # If loader wiring fails we still try normal system espeak lookup.
                pass

            model_path = Path(model.model_path).resolve()
            config_path = model_path / "config.json"
            config_payload: dict[str, Any] = {}
            try:
                config_payload = json.loads(config_path.read_text(encoding="utf-8"))
            except Exception:
                config_payload = {}

            model_file = str(config_payload.get("model_file") or "").strip()
            voices_file = str(config_payload.get("voices") or "").strip()
            onnx_candidates = [model_path / model_file] if model_file else []
            onnx_candidates.extend(sorted(model_path.glob("*.onnx")))
            onnx_path = next((candidate for candidate in onnx_candidates if candidate.is_file()), None)
            if onnx_path is None:
                raise RuntimeError("Kitten-TTS ONNX-Datei wurde im Modellordner nicht gefunden.")

            voices_candidates = [model_path / voices_file] if voices_file else []
            voices_candidates.append(model_path / "voices.npz")
            voices_path = next((candidate for candidate in voices_candidates if candidate.is_file()), None)
            if voices_path is None:
                raise RuntimeError("Kitten-TTS voices.npz wurde im Modellordner nicht gefunden.")

            runtime = KittenTTS(model_path=str(onnx_path), voices_path=str(voices_path))
            self._pipelines[key] = runtime
            return runtime

    def _synthesize_kitten_tts(self, model: ModelConfig, text: str, options: dict[str, Any]) -> tuple[bytes, int]:
        runtime = self._kitten_tts_runtime(model)
        speaker = str(options.get("speaker") or "").strip() or "Bella"
        config_path = Path(model.model_path) / "config.json"
        try:
            config_payload = json.loads(config_path.read_text(encoding="utf-8"))
        except Exception:
            config_payload = {}
        aliases = config_payload.get("voice_aliases") if isinstance(config_payload, dict) else None
        if isinstance(aliases, dict):
            mapped = aliases.get(speaker)
            if isinstance(mapped, str) and mapped.strip():
                speaker = mapped.strip()
        speed = float(options.get("speed", 1.0))
        import numpy as np

        phonemes = runtime._phonemizer.phonemize([text])[0]
        sequence = ' '.join(re.findall(r"\w+|[^\w\s]", phonemes))
        token_ids = [runtime._word_index_dictionary[c] for c in sequence if c in runtime._word_index_dictionary]
        if not token_ids:
            raise RuntimeError("Kitten-TTS konnte keine gueltigen Phoneme aus dem Text erzeugen.")

        voice_matrix = np.asarray(runtime._voices[speaker], dtype=np.float32)
        if voice_matrix.ndim == 1:
            style_array = voice_matrix.reshape(1, -1)
        else:
            index = min(max(len(token_ids) - 1, 0), voice_matrix.shape[0] - 1)
            style_array = np.asarray(voice_matrix[index], dtype=np.float32).reshape(1, -1)

        output = runtime._session.run(
            None,
            {
                "input_ids": np.array([[0, *token_ids, 0]], dtype=np.int64),
                "style": style_array,
                "speed": np.array([speed], dtype=np.float32),
            },
        )
        audio = output[0]
        sample_rate = int(getattr(runtime, "sample_rate", 24000) or 24000)
        return self._wav(audio, sample_rate, 1.0), sample_rate

    def transcribe(self, model: ModelConfig, audio: bytes, options: dict[str, Any]) -> dict[str, Any]:
        if (Path(model.model_path) / "model.bin").exists() and "faster-whisper" in model.name.lower():
            return self._transcribe_faster_whisper(model, audio, options)
        pipe = self._pipeline(model, "automatic-speech-recognition", str(options.get("device", "auto")))
        generate_kwargs: dict[str, Any] = {}
        language = str(options.get("language") or "").strip()
        if language and language != "auto":
            generate_kwargs["language"] = language
        task = str(options.get("task") or "transcribe")
        if task in {"transcribe", "translate"}:
            generate_kwargs["task"] = task
        kwargs: dict[str, Any] = {
            "return_timestamps": bool(options.get("return_timestamps", False)),
            "generate_kwargs": generate_kwargs,
        }
        chunk = int(options.get("chunk_length_s", 30))
        if chunk > 0:
            kwargs["chunk_length_s"] = max(5, min(chunk, 120))
            kwargs["stride_length_s"] = max(0, min(int(options.get("stride_length_s", 5)), chunk // 2))
        result = pipe(audio, **kwargs)
        if isinstance(result, str):
            return {"text": result, "chunks": []}
        return {"text": str(result.get("text", "")).strip(), "chunks": result.get("chunks", [])}

    @staticmethod
    def _decode_audio_mono(audio: bytes, target_sr: int = 16000) -> tuple[Any, int]:
        import numpy as np

        def _guess_suffix(payload: bytes) -> str:
            if payload.startswith(b"RIFF") and payload[8:12] == b"WAVE":
                return ".wav"
            if payload.startswith(b"OggS"):
                return ".ogg"
            if payload.startswith(b"fLaC"):
                return ".flac"
            if payload.startswith(b"ID3"):
                return ".mp3"
            if len(payload) > 2 and payload[0] == 0xFF and (payload[1] & 0xE0) == 0xE0:
                return ".mp3"
            if payload.startswith(bytes.fromhex("1A45DFA3")):
                return ".webm"
            if b"ftyp" in payload[:32]:
                return ".m4a"
            return ".audio"

        try:
            import soundfile as sf

            waveform, sample_rate = sf.read(io.BytesIO(audio), dtype="float32", always_2d=False)
            data = np.asarray(waveform, dtype=np.float32)
            if data.ndim > 1:
                data = data.mean(axis=1)
        except Exception:
            decode_errors: list[str] = []

            try:
                import torchaudio

                suffix = _guess_suffix(audio)
                with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                    tmp.write(audio)
                    tmp_path = tmp.name
                try:
                    waveform_tensor, sample_rate = torchaudio.load(tmp_path)
                finally:
                    try:
                        Path(tmp_path).unlink(missing_ok=True)
                    except Exception:
                        pass
                waveform_np = waveform_tensor.detach().cpu().numpy().astype(np.float32)
                data = waveform_np.mean(axis=0) if waveform_np.ndim > 1 else waveform_np
            except Exception as torchaudio_exc:
                decode_errors.append(f"torchaudio: {torchaudio_exc}")
                try:
                    import av

                    chunks: list[Any] = []
                    sample_rate = 0
                    with av.open(io.BytesIO(audio), mode="r") as container:
                        audio_stream = next((stream for stream in container.streams if stream.type == "audio"), None)
                        if audio_stream is None:
                            raise RuntimeError("kein Audiostream gefunden")
                        for frame in container.decode(audio_stream):
                            frame_data = frame.to_ndarray()
                            mono = frame_data.mean(axis=0) if frame_data.ndim > 1 else frame_data
                            chunks.append(np.asarray(mono, dtype=np.float32).reshape(-1))
                            if frame.sample_rate:
                                sample_rate = int(frame.sample_rate)

                    if not chunks:
                        raise RuntimeError("keine Audiopakete dekodiert")
                    data = np.concatenate(chunks).astype(np.float32)
                    sample_rate = sample_rate or target_sr
                except Exception as av_exc:
                    decode_errors.append(f"pyav: {av_exc}")
                    try:
                        import librosa

                        suffix_candidates = [
                            _guess_suffix(audio),
                            ".webm",
                            ".ogg",
                            ".wav",
                            ".mp3",
                            ".m4a",
                            ".audio",
                        ]
                        last_exc: Exception | None = None
                        for suffix in dict.fromkeys(suffix_candidates):
                            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                                tmp.write(audio)
                                tmp_path = tmp.name
                            try:
                                data, sample_rate = librosa.load(tmp_path, sr=None, mono=True)
                                data = np.asarray(data, dtype=np.float32)
                                last_exc = None
                                break
                            except Exception as load_exc:
                                last_exc = load_exc
                            finally:
                                try:
                                    Path(tmp_path).unlink(missing_ok=True)
                                except Exception:
                                    pass

                        if last_exc is not None:
                            raise last_exc
                    except Exception as librosa_exc:
                        decode_errors.append(f"librosa: {librosa_exc}")
                        raise RuntimeError(
                            "Audio konnte fuer VAD nicht dekodiert werden. "
                            + " | ".join(decode_errors)
                        ) from librosa_exc

        if sample_rate not in {8000, 16000}:
            try:
                import librosa

                data = librosa.resample(data, orig_sr=sample_rate, target_sr=target_sr)
                sample_rate = target_sr
            except Exception as exc:
                raise RuntimeError("Audio-Samplingrate konnte nicht fuer VAD normalisiert werden.") from exc

        if sample_rate == 8000:
            return data, 8000
        return data, 16000

    def detect_voice_activity(self, model: ModelConfig, audio: bytes, options: dict[str, Any]) -> dict[str, Any]:
        import numpy as np

        model_path = Path(model.model_path).resolve()
        onnx_path = model_path / "silero_vad.onnx"
        if not onnx_path.is_file():
            candidates = sorted(model_path.glob("*.onnx"))
            onnx_path = candidates[0] if candidates else onnx_path
        if not onnx_path.is_file():
            raise RuntimeError("Silero-VAD ONNX-Datei wurde nicht gefunden.")

        requested = str(options.get("device") or "auto").strip().lower()
        providers = ["CPUExecutionProvider"]
        if requested in {"auto", "cuda"}:
            try:
                import onnxruntime as ort

                available = set(ort.get_available_providers())
                if "CUDAExecutionProvider" in available:
                    providers = ["CUDAExecutionProvider", "CPUExecutionProvider"]
            except Exception:
                providers = ["CPUExecutionProvider"]

        key = (model.id, "vad", providers[0])
        with self._lock:
            runtime = self._pipelines.get(key)
            if runtime is None:
                try:
                    import onnxruntime as ort
                except ImportError as exc:
                    raise RuntimeError("onnxruntime wird fuer Silero-VAD benoetigt.") from exc
                runtime = ort.InferenceSession(str(onnx_path), providers=providers)
                self._pipelines[key] = runtime

        waveform, sample_rate = self._decode_audio_mono(audio)
        if waveform.size == 0:
            return {
                "speaking": False,
                "segments": [],
                "max_confidence": 0.0,
                "speech_ratio": 0.0,
                "sample_rate": sample_rate,
            }

        window = 512 if sample_rate == 16000 else 256
        state = np.zeros((2, 1, 128), dtype=np.float32)
        threshold = float(options.get("threshold", 0.5))
        off_threshold = max(0.05, threshold - 0.15)

        probs: list[float] = []
        speech_segments: list[dict[str, float]] = []
        active = False
        segment_start = 0

        offset = 0
        while offset < waveform.size:
            chunk = waveform[offset: offset + window]
            if chunk.size < window:
                chunk = np.pad(chunk, (0, window - chunk.size), mode="constant")

            output, state = runtime.run(
                None,
                {
                    "input": chunk.reshape(1, -1).astype(np.float32),
                    "state": state,
                    "sr": np.array(sample_rate, dtype=np.int64),
                },
            )
            prob = float(np.asarray(output).reshape(-1)[0])
            probs.append(prob)

            if not active and prob >= threshold:
                active = True
                segment_start = offset
            elif active and prob < off_threshold:
                active = False
                speech_segments.append({
                    "start": round(segment_start / sample_rate, 4),
                    "end": round(offset / sample_rate, 4),
                })

            offset += window

        if active:
            speech_segments.append({
                "start": round(segment_start / sample_rate, 4),
                "end": round(waveform.size / sample_rate, 4),
            })

        total_speech = sum(max(0.0, segment["end"] - segment["start"]) for segment in speech_segments)
        total_duration = max(1e-6, float(waveform.size) / float(sample_rate))

        return {
            "speaking": bool(speech_segments),
            "segments": speech_segments,
            "max_confidence": round(max(probs) if probs else 0.0, 4),
            "speech_ratio": round(min(1.0, total_speech / total_duration), 4),
            "sample_rate": sample_rate,
        }

    def apply_vad_precut(
        self,
        audio: bytes,
        vad_result: dict[str, Any],
        *,
        padding_ms: int = 120,
        merge_gap_ms: int = 180,
        min_segment_ms: int = 120,
    ) -> bytes:
        import numpy as np

        waveform, sample_rate = self._decode_audio_mono(audio)
        segments_in = vad_result.get("segments") if isinstance(vad_result, dict) else None
        if not isinstance(segments_in, list) or not segments_in:
            return audio

        padding = max(0, int(sample_rate * max(0, padding_ms) / 1000))
        merge_gap = max(0, int(sample_rate * max(0, merge_gap_ms) / 1000))
        min_len = max(1, int(sample_rate * max(0, min_segment_ms) / 1000))

        spans: list[tuple[int, int]] = []
        for raw in segments_in:
            if not isinstance(raw, dict):
                continue
            start_sec = float(raw.get("start", 0.0))
            end_sec = float(raw.get("end", 0.0))
            start = max(0, int(start_sec * sample_rate) - padding)
            end = min(waveform.size, int(end_sec * sample_rate) + padding)
            if end - start < min_len:
                continue
            spans.append((start, end))

        if not spans:
            return audio

        spans.sort(key=lambda item: item[0])
        merged: list[list[int]] = []
        for start, end in spans:
            if not merged:
                merged.append([start, end])
                continue
            prev = merged[-1]
            if start <= prev[1] + merge_gap:
                prev[1] = max(prev[1], end)
            else:
                merged.append([start, end])

        parts = [waveform[start:end] for start, end in merged if end > start]
        if not parts:
            return audio

        clipped = np.concatenate(parts).astype(np.float32)
        return self._wav(clipped, sample_rate, 1.0)

    def _transcribe_faster_whisper(self, model: ModelConfig, audio: bytes, options: dict[str, Any]) -> dict[str, Any]:
        try:
            from faster_whisper import WhisperModel
        except ImportError as exc:
            raise RuntimeError("faster-whisper ist fuer dieses CTranslate2-Modell nicht installiert") from exc
        requested = str(options.get("device", "auto"))
        device = "cuda" if requested == "cuda" else "cpu"
        if requested == "auto":
            try:
                import torch
                device = "cuda" if torch.cuda.is_available() else "cpu"
            except ImportError:
                device = "cpu"
        key = (model.id, "faster-whisper", device)
        with self._lock:
            runtime = self._pipelines.get(key)
            if runtime is None:
                runtime = WhisperModel(model.model_path, device=device, compute_type="float16" if device == "cuda" else "int8")
                self._pipelines[key] = runtime
        language = str(options.get("language") or "auto")
        segments, info = runtime.transcribe(
            io.BytesIO(audio), language=None if language == "auto" else language,
            task=str(options.get("task") or "transcribe"), vad_filter=True,
        )
        chunks = [{"text": segment.text, "timestamp": [segment.start, segment.end]} for segment in segments]
        return {"text": " ".join(str(item["text"]).strip() for item in chunks).strip(), "chunks": chunks,
                "language": getattr(info, "language", language)}

    def synthesize(self, model: ModelConfig, text: str, options: dict[str, Any]) -> tuple[bytes, int]:
        if self._is_kokoro_model(model):
            return self._synthesize_kokoro(model, text, options)
        if self._is_qwen3_tts_model(model):
            return self._synthesize_qwen3_tts(model, text, options)
        if self._is_kitten_tts_model(model):
            return self._synthesize_kitten_tts(model, text, options)

        pipe = self._pipeline(model, "text-to-speech", str(options.get("device", "auto")))
        forward_params: dict[str, Any] = {}
        speaker = str(options.get("speaker") or "").strip()
        language = str(options.get("language") or "").strip()
        if speaker:
            forward_params["speaker"] = speaker
        if language and language != "auto":
            forward_params["language"] = language
        try:
            result = pipe(text, forward_params=forward_params) if forward_params else pipe(text)
        except TypeError:
            result = pipe(text)
        audio = result.get("audio") if isinstance(result, dict) else result
        sample_rate = int(result.get("sampling_rate", 16000)) if isinstance(result, dict) else 16000
        return self._wav(audio, sample_rate, float(options.get("speed", 1.0))), sample_rate

    @staticmethod
    def _wav(audio: Any, sample_rate: int, speed: float) -> bytes:
        import numpy as np

        samples = np.asarray(audio, dtype=np.float32).squeeze()
        if samples.ndim != 1:
            samples = samples.reshape(-1)
        speed = max(0.5, min(speed, 2.0))
        if abs(speed - 1.0) > 0.01 and samples.size > 1:
            target = max(1, int(samples.size / speed))
            samples = np.interp(np.linspace(0, samples.size - 1, target), np.arange(samples.size), samples)
        peak = float(np.max(np.abs(samples))) if samples.size else 1.0
        pcm = (samples / max(peak, 1.0) * 32767).astype("<i2").tobytes()
        output = io.BytesIO()
        with wave.open(output, "wb") as wav:
            wav.setnchannels(1)
            wav.setsampwidth(2)
            wav.setframerate(sample_rate)
            wav.writeframes(pcm)
        return output.getvalue()


speech_service = SpeechService()
