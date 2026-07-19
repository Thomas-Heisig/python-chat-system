from __future__ import annotations

import argparse
from pathlib import Path
import sys

from app.training.datasets.universal import canonical_to_pairs, parse_dataset_to_canonical
from app.training.evaluation.business_letter_schema import validate_business_letter_json_text


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Lint business-letter training datasets against strict JSON output requirements.",
    )
    parser.add_argument("--input", required=True, help="Path to dataset file (jsonl/json/csv/md/txt/...) ")
    parser.add_argument(
        "--max-errors",
        type=int,
        default=25,
        help="Maximum number of individual sample errors printed.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    dataset_path = Path(args.input)
    if not dataset_path.exists() or not dataset_path.is_file():
        print(f"ERROR: dataset not found: {dataset_path}")
        return 2

    try:
        canonical_records = parse_dataset_to_canonical(dataset_path)
        pairs = canonical_to_pairs(canonical_records)
    except Exception as exc:
        print(f"ERROR: dataset parsing failed: {exc}")
        return 2

    total = len(pairs)
    invalid_count = 0
    printed_errors = 0

    for idx, pair in enumerate(pairs, start=1):
        completion = str(pair.get("completion") or "")
        result = validate_business_letter_json_text(completion)
        if result.valid:
            continue

        invalid_count += 1
        if printed_errors < max(0, args.max_errors):
            print(f"[{idx}] INVALID: {', '.join(result.errors)}")
            printed_errors += 1

    valid_count = total - invalid_count
    print("---")
    print(f"Samples total : {total}")
    print(f"Samples valid : {valid_count}")
    print(f"Samples invalid: {invalid_count}")

    if invalid_count > 0:
        print("RESULT: FAILED (dataset contains invalid assistant targets)")
        return 1

    print("RESULT: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
