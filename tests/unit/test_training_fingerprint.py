import json
from pathlib import Path

from app.db_models.training_dataset import TrainingDataset
from app.training.api.routes import _training_fingerprint


def _dataset(path: Path, *, dataset_id: int) -> TrainingDataset:
    return TrainingDataset(
        id=dataset_id, user_id=1, name=f"dataset-{dataset_id}", source_type="local_file",
        status="ready", version=1,
        metadata_json=json.dumps({"files": {"source": str(path), "training": str(path)}}),
    )


def test_fingerprint_deduplicates_same_content_across_dataset_records(tmp_path: Path) -> None:
    first = tmp_path / "first.jsonl"
    second = tmp_path / "second.jsonl"
    content = '{"prompt":"a","completion":"b"}\n'
    first.write_text(content, encoding="utf-8")
    second.write_text(content, encoding="utf-8")

    left = _training_fingerprint(dataset=_dataset(first, dataset_id=1), base_model_name="model", trainer_name="peft_lora", hyperparameters={})
    right = _training_fingerprint(dataset=_dataset(second, dataset_id=2), base_model_name="model", trainer_name="peft_lora", hyperparameters={})

    assert left == right


def test_fingerprint_changes_with_training_content(tmp_path: Path) -> None:
    source = tmp_path / "training.jsonl"
    source.write_text('{"prompt":"a","completion":"b"}\n', encoding="utf-8")
    before = _training_fingerprint(dataset=_dataset(source, dataset_id=1), base_model_name="model", trainer_name="peft_lora", hyperparameters={})
    source.write_text('{"prompt":"a","completion":"changed"}\n', encoding="utf-8")
    after = _training_fingerprint(dataset=_dataset(source, dataset_id=1), base_model_name="model", trainer_name="peft_lora", hyperparameters={})

    assert before != after
