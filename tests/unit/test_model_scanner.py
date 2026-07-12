from app.models.scanner import ModelScanner


def test_scan_empty_directory(tmp_path):
    scanner = ModelScanner()
    result = scanner.scan_directories([str(tmp_path)])
    assert result == []


def test_scan_detects_supra_custom_any_to_any_model(tmp_path):
    scanner = ModelScanner()
    model_dir = tmp_path / "Supra-A2A-Nano-Exp"
    model_dir.mkdir(parents=True, exist_ok=True)
    (model_dir / "model.safetensors").write_text("stub", encoding="utf-8")
    (model_dir / "vqvae.safetensors").write_text("stub", encoding="utf-8")
    (model_dir / "tokenizer.json").write_text("{}", encoding="utf-8")

    result = scanner.scan_directories([str(tmp_path)])
    assert len(result) == 1
    entry = result[0]
    assert entry["name"] == "Supra-A2A-Nano-Exp"
    assert entry["backend"] == "custom_pytorch"
    assert entry["model_format"] == "custom_safetensors"
    assert entry["task_type"] == "any_to_any"
    assert entry["metadata"]["requires_custom_code"] is True
    assert entry["metadata"]["custom_code_available"] is False
    assert entry["metadata"]["custom_code_trusted"] is False


def test_scan_classifies_ultravox_as_audio_text_generation(tmp_path):
    scanner = ModelScanner()
    model_dir = tmp_path / "Ultravox-Gemma-2-9B-it"
    model_dir.mkdir(parents=True, exist_ok=True)
    (model_dir / "config.json").write_text('{"model_type":"gemma"}', encoding="utf-8")
    (model_dir / "model.safetensors").write_text("stub", encoding="utf-8")
    (model_dir / "README.md").write_text(
        "---\n"
        "pipeline_tag: image-text-to-text\n"
        "tags:\n"
        "  - audio-text-to-text\n"
        "---\n",
        encoding="utf-8",
    )

    result = scanner.scan_directories([str(tmp_path)])
    assert len(result) == 1
    entry = result[0]
    assert entry["name"] == "Ultravox-Gemma-2-9B-it"
    assert entry["task_type"] == "audio_text_generation"
    assert entry["backend"] == "transformers"


def test_scan_classifies_smolvlm2_as_vision_text_generation(tmp_path):
    scanner = ModelScanner()
    model_dir = tmp_path / "SmolVLM2-2.2B-Instruct"
    model_dir.mkdir(parents=True, exist_ok=True)
    (model_dir / "config.json").write_text('{"model_type":"smolvlm"}', encoding="utf-8")
    (model_dir / "model.safetensors").write_text("stub", encoding="utf-8")
    (model_dir / "processor_config.json").write_text("{}", encoding="utf-8")
    (model_dir / "README.md").write_text(
        "---\n"
        "pipeline_tag: image-text-to-text\n"
        "---\n",
        encoding="utf-8",
    )

    result = scanner.scan_directories([str(tmp_path)])
    assert len(result) == 1
    entry = result[0]
    assert entry["name"] == "SmolVLM2-2.2B-Instruct"
    assert entry["task_type"] == "vision_text_generation"
    assert entry["backend"] == "transformers"
