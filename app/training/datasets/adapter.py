import re
from pathlib import Path

from app.training.datasets.errors import DatasetValidationError
from app.training.datasets.universal import canonical_to_pairs, parse_dataset_to_canonical, write_canonical_jsonl


SECRET_PATTERNS = [
    re.compile(r"(?i)api[_-]?key\s*[:=]\s*['\"]?[a-z0-9_\-]{12,}"),
    re.compile(r"(?i)bearer\s+[a-z0-9\-_=\.]{12,}"),
    re.compile(r"-----BEGIN (RSA|EC|OPENSSH|DSA) PRIVATE KEY-----"),
    re.compile(r"(?i)password\s*[:=]\s*[^\s]{6,}"),
    re.compile(r"(?i)postgres(ql)?://[^\s]+:[^\s]+@"),
]

class DatasetAdapter:
    def load_samples(self, *, source_path: str, max_text_length: int = 12000) -> list[dict[str, str]]:
        path = Path(source_path)
        if not path.exists() or not path.is_file():
            raise DatasetValidationError("dataset_file_not_found")
        if path.suffix.lower() not in {".jsonl", ".json", ".csv", ".md", ".markdown", ".txt", ".yaml", ".yml", ".xml", ".html", ".htm", ".pdf", ".docx"}:
            raise DatasetValidationError("unsupported_dataset_format")

        canonical_records = parse_dataset_to_canonical(path)
        rows = canonical_to_pairs(canonical_records)

        # Persist normalized canonical dataset next to the original source for reproducibility.
        canonical_path = path.with_suffix(path.suffix + ".canonical.jsonl")
        write_canonical_jsonl(canonical_records, canonical_path)

        seen: set[str] = set()
        deduped_rows: list[dict[str, str]] = []
        for idx, text_pair in enumerate(rows, start=1):
            self._scan_for_secrets(text_pair["prompt"], idx)
            self._scan_for_secrets(text_pair["completion"], idx)

            if len(text_pair["prompt"]) > max_text_length or len(text_pair["completion"]) > max_text_length:
                raise DatasetValidationError(f"text_too_long:{idx}")

            dedup_key = f"{text_pair['prompt']}::{text_pair['completion']}"
            if dedup_key in seen:
                continue
            seen.add(dedup_key)
            deduped_rows.append(text_pair)

        if not deduped_rows:
            raise DatasetValidationError("dataset_empty")

        return deduped_rows

    def _scan_for_secrets(self, value: str, line_number: int) -> None:
        for pattern in SECRET_PATTERNS:
            if pattern.search(value):
                raise DatasetValidationError(f"secret_detected:{line_number}")
