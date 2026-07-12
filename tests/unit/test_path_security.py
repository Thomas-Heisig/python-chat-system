import os
from pathlib import Path

from app.models.path_security import (
    normalize_base_directories,
    validate_model_path_against_allowed_bases,
)


def test_normalize_base_directories_keeps_only_allowed_and_deduplicates(tmp_path, monkeypatch):
    allowed_one = (tmp_path / "allowed-a").resolve(strict=False)
    allowed_two = (tmp_path / "allowed-b").resolve(strict=False)

    monkeypatch.setenv(
        "MODEL_ALLOWED_BASE_DIRS",
        os.pathsep.join([str(allowed_one), str(allowed_two)]),
    )

    result = normalize_base_directories(
        [
            str(allowed_one),
            str(allowed_one),
            str(allowed_two),
            str(tmp_path / "outside"),
            "..\\forbidden",
            "",
        ]
    )

    assert result == [str(allowed_one), str(allowed_two)]


def test_normalize_base_directories_accepts_windows_path_variants(tmp_path, monkeypatch):
    allowed = (tmp_path / "AllowedDir").resolve(strict=False)
    monkeypatch.setenv("MODEL_ALLOWED_BASE_DIRS", str(allowed))

    # Validate case-insensitive matching and slash normalization on Windows-like input.
    mixed_case = str(allowed).upper()
    forward_slash = str(allowed).replace("\\", "/")

    result = normalize_base_directories([mixed_case, forward_slash])

    assert result == [str(allowed)]


def test_validate_model_path_allows_parent_segments_when_resolved_path_stays_within_allowed_base(tmp_path):
    base = (tmp_path / "allowed").resolve(strict=False)
    target_dir = base / "models"
    target_dir.mkdir(parents=True, exist_ok=True)

    # Parent segments are accepted when the resolved target remains in the allowed base.
    traversal_path = str(target_dir / ".." / "models")

    valid, reason = validate_model_path_against_allowed_bases(traversal_path, [str(base)])

    assert valid is True
    assert reason is None


def test_validate_model_path_requires_existing_target(tmp_path):
    base = (tmp_path / "allowed").resolve(strict=False)
    base.mkdir(parents=True, exist_ok=True)

    missing_path = str(base / "missing-model")
    valid, reason = validate_model_path_against_allowed_bases(missing_path, [str(base)])

    assert valid is False
    assert reason == "path_missing"


def test_normalize_base_directories_is_permissive_without_allow_list(tmp_path, monkeypatch):
    monkeypatch.delenv("MODEL_ALLOWED_BASE_DIRS", raising=False)
    candidate = (tmp_path / "custom-model-root").resolve(strict=False)

    result = normalize_base_directories([str(candidate)])

    assert result == [str(candidate)]
