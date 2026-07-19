from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


SPLITS = ("training", "validation", "test")
SENSITIVE_TERMS = re.compile(r"norm|recht|preis|gesteinssort|handelsname|gewähr|haft", re.IGNORECASE)


def _content_key(record: dict[str, Any]) -> str:
    messages = record.get("messages", [])
    normalized = [
        {"role": str(item.get("role", "")).strip(), "content": " ".join(str(item.get("content", "")).split())}
        for item in messages if isinstance(item, dict)
    ]
    return hashlib.sha256(json.dumps(normalized, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()


def _latest_packages(root: Path) -> list[Path]:
    packages = [path for path in root.iterdir() if path.is_dir() and all((path / f"{split}.jsonl").is_file() for split in SPLITS)]
    selected = [path for path in packages if "fremdgewerke_schnittstellen" not in path.name]
    fremd = [path for path in packages if "fremdgewerke_schnittstellen" in path.name]
    if fremd:
        selected.append(max(fremd, key=lambda path: tuple(int(value) for value in re.findall(r"v(\d+)\.(\d+)\.(\d+)", path.name)[-1])))
    return sorted(selected)


def _normalize(record: dict[str, Any], *, package: str, split: str, index: int) -> dict[str, Any]:
    messages = record.get("messages")
    if not isinstance(messages, list) or len(messages) < 2:
        raise ValueError(f"invalid messages in {package}/{split} line {index + 1}")
    metadata = record.get("metadata") if isinstance(record.get("metadata"), dict) else {}
    domain_raw = str(metadata.get("domain") or package.rsplit("_v", 1)[0]).strip().lower()
    category = domain_raw
    topic = str(metadata.get("topic") or "allgemein").strip().lower()
    dialogue = str(metadata.get("dialog_type") or metadata.get("dialogue_type") or "").strip().lower()
    if not dialogue:
        dialogue = "multi_turn" if sum(1 for item in messages if isinstance(item, dict) and item.get("role") == "user") > 1 else "single_turn"
    dialogue = {"single": "single_turn", "multi": "multi_turn", "multiturn": "multi_turn"}.get(dialogue, dialogue)
    turn_count = len(messages)
    difficulty = {"easy": "einfach", "medium": "mittel", "hard": "schwierig"}.get(str(metadata.get("difficulty") or "mittel").lower(), str(metadata.get("difficulty") or "mittel"))
    answer_length = {"short": "kurz", "medium": "mittel", "detailed": "ausfuehrlich"}.get(str(metadata.get("answer_length") or "mittel").lower(), str(metadata.get("answer_length") or "mittel"))
    source_required = bool(metadata.get("source_required", False) or metadata.get("sources") or SENSITIVE_TERMS.search(f"{category} {topic}"))
    record_id = str(metadata.get("id") or f"{category}_{topic}_{index + 1:04d}").strip().lower()
    normalized_metadata = {
        "id": record_id,
        "language": str(metadata.get("language") or "de"),
        "domain": "naturstein",
        "category": category,
        "topic": topic,
        "subtopic": str(metadata.get("subtopic") or topic),
        "customer_type": str(metadata.get("customer_type") or metadata.get("audience") or "nicht_angegeben"),
        "difficulty": difficulty,
        "answer_length": answer_length,
        "dialog_type": dialogue,
        "turn_count": turn_count,
        "split": split,
        "version": "2.0.0",
        "status": str(metadata.get("status") or "validated"),
        "source_required": source_required,
        "source_package": package,
        "source_record_id": str(metadata.get("id") or ""),
    }
    if isinstance(metadata.get("sources"), list):
        normalized_metadata["sources"] = metadata["sources"]
    return {"messages": messages, "metadata": normalized_metadata}


def consolidate(source_root: Path, output_root: Path) -> dict[str, Any]:
    packages = _latest_packages(source_root)
    raw: dict[str, list[dict[str, Any]]] = {split: [] for split in SPLITS}
    invalid: list[str] = []
    for package in packages:
        for split in SPLITS:
            for index, line in enumerate((package / f"{split}.jsonl").read_text(encoding="utf-8-sig").splitlines()):
                if not line.strip():
                    continue
                try:
                    parsed = json.loads(line)
                    raw[split].append(_normalize(parsed, package=package.name, split=split, index=index))
                except Exception as exc:
                    invalid.append(f"{package.name}/{split}:{index + 1}: {exc}")

    # The held-out test split has first ownership, then validation, then training.
    # This only performs technical exact-content overlap removal; it never scores test content.
    owner_order = ("test", "validation", "training")
    owned: set[str] = set()
    clean: dict[str, list[dict[str, Any]]] = {split: [] for split in SPLITS}
    duplicates: list[dict[str, str]] = []
    for split in owner_order:
        local: set[str] = set()
        for record in raw[split]:
            key = _content_key(record)
            if key in owned or key in local:
                duplicates.append({"hash": key, "removed_from": split, "id": record["metadata"]["id"]})
                continue
            local.add(key)
            clean[split].append(record)
        owned.update(local)

    output_root.mkdir(parents=True, exist_ok=True)
    metadata_root = output_root / "metadata"
    metadata_root.mkdir(exist_ok=True)
    statistics: dict[str, Any] = {"total": 0, "splits": {}, "topics": {}, "categories": {}, "dialog_types": {}, "difficulty": {}, "answer_length": {}}
    for split in SPLITS:
        complete_dir = output_root / split
        topic_dir = complete_dir / "by_topic"
        topic_dir.mkdir(parents=True, exist_ok=True)
        records = clean[split]
        (complete_dir / f"{split}_complete.jsonl").write_text("".join(json.dumps(item, ensure_ascii=False) + "\n" for item in records), encoding="utf-8")
        by_topic: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for record in records:
            by_topic[record["metadata"]["category"]].append(record)
        for topic, items in by_topic.items():
            (topic_dir / f"{topic}.jsonl").write_text("".join(json.dumps(item, ensure_ascii=False) + "\n" for item in items), encoding="utf-8")
        statistics["splits"][split] = len(records)
        statistics["total"] += len(records)

    all_records = [item for split in SPLITS for item in clean[split]]
    for key, target in (("topic", "topics"), ("category", "categories"), ("dialog_type", "dialog_types"), ("difficulty", "difficulty"), ("answer_length", "answer_length")):
        statistics[target] = dict(Counter(item["metadata"][key] for item in all_records).most_common())
    lengths = [sum(len(str(message.get("content", ""))) for message in item["messages"] if message.get("role") == "assistant") for item in all_records]
    statistics["assistant_answer_characters"] = {"min": min(lengths, default=0), "max": max(lengths, default=0), "average": round(sum(lengths) / max(1, len(lengths)), 2)}
    statistics["source_required"] = sum(bool(item["metadata"]["source_required"]) for item in all_records)

    manifest = {
        "name": "projekt_kernschmiede", "version": "2.0.0", "format": "messages",
        "source_packages": [path.name for path in packages], "splits": statistics["splits"],
        "deduplication": "sha256(normalized messages), precedence test > validation > training",
        "test_policy": "technical validation only; excluded from training and model selection",
    }
    (metadata_root / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    (metadata_root / "topic_statistics.json").write_text(json.dumps(statistics, ensure_ascii=False, indent=2), encoding="utf-8")
    (metadata_root / "duplicate_report.json").write_text(json.dumps({"removed": len(duplicates), "items": duplicates, "invalid": invalid}, ensure_ascii=False, indent=2), encoding="utf-8")
    report = ["# Qualitätsbericht", "", f"- Quellpakete: {len(packages)}", f"- Datensätze nach Bereinigung: {statistics['total']}", f"- Entfernte Dubletten/Überschneidungen: {len(duplicates)}", f"- Ungültige Datensätze: {len(invalid)}", f"- Training: {statistics['splits']['training']}", f"- Validation: {statistics['splits']['validation']}", f"- Test: {statistics['splits']['test']}", "", "Der Test-Split wurde nur technisch validiert und nicht zur Optimierung oder Modellauswahl verwendet."]
    (metadata_root / "quality_check_report.md").write_text("\n".join(report) + "\n", encoding="utf-8")
    (metadata_root / "changelog.md").write_text("# Changelog\n\n## 2.0.0\n\n- 11 Themenpakete konsolidiert.\n- Metadaten normalisiert.\n- Inhaltsdubletten splitübergreifend entfernt.\n", encoding="utf-8")
    (output_root / "README.md").write_text("# Projekt Kernschmiede 2.0.0\n\nKonsolidiertes, dedupliziertes Trainingspaket. Der Test-Split ist ein unabhängiger Abschlusstest.\n", encoding="utf-8")
    return {"packages": len(packages), "duplicates": len(duplicates), "invalid": len(invalid), **statistics}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, default=Path("training-datasets"))
    parser.add_argument("--output", type=Path, default=Path("training-datasets/projekt_kernschmiede_v2.0.0"))
    args = parser.parse_args()
    print(json.dumps(consolidate(args.source.resolve(), args.output.resolve()), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
