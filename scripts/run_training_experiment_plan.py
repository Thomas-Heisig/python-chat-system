#!/usr/bin/env python3
"""Queue reproducible training experiments (A-F) against the local training API."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib import error, request


@dataclass(frozen=True)
class ExperimentStep:
    code: str
    name: str
    dataset_id: int | None
    base_model_id: str | None
    trainer_name: str | None
    hyperparameters: dict[str, Any] | None
    requires_training_job: bool


def _request_json(*, api_base: str, path: str, payload: dict[str, Any]) -> dict[str, Any]:
    url = f"{api_base.rstrip('/')}{path}"
    raw = json.dumps(payload).encode("utf-8")
    req = request.Request(url=url, data=raw, method="POST")
    req.add_header("Content-Type", "application/json")
    req.add_header("Accept", "application/json")
    try:
        with request.urlopen(req, timeout=180) as response:
            content = response.read().decode("utf-8")
    except error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"HTTP {exc.code} {path}: {body}") from exc
    except error.URLError as exc:
        raise RuntimeError(f"API unreachable at {url}: {exc}") from exc

    try:
        parsed = json.loads(content)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Invalid JSON response from {path}: {content[:2000]}") from exc
    if not isinstance(parsed, dict):
        raise RuntimeError(f"Unexpected response type from {path}: {type(parsed).__name__}")
    return parsed


def _default_controlled_hyperparameters() -> dict[str, Any]:
    return {
        "num_train_epochs": 4,
        "learning_rate": 0.0001,
        "per_device_train_batch_size": 1,
        "gradient_accumulation_steps": 4,
        "max_sequence_length": 768,
        "lora_r": 16,
        "lora_alpha": 32,
        "lora_dropout": 0.05,
        "target_modules": ["q_proj", "k_proj", "v_proj", "o_proj"],
        "load_in_4bit": True,
        "warmup_ratio": 0.05,
        "weight_decay": 0.01,
        "eval_steps": 10,
        "save_steps": 10,
        "logging_steps": 1,
        "load_best_model_at_end": True,
        "metric_for_best_model": "eval_loss",
        "greater_is_better": False,
        "seed": 42,
    }


def _legacy_hyperparameters() -> dict[str, Any]:
    return {
        "num_train_epochs": 1,
        "learning_rate": 0.0002,
        "per_device_train_batch_size": 1,
        "gradient_accumulation_steps": 8,
        "max_sequence_length": 512,
        "lora_r": 16,
        "lora_alpha": 32,
        "lora_dropout": 0.05,
        "target_modules": ["q_proj", "k_proj", "v_proj", "o_proj"],
        "load_in_4bit": True,
        "eval_steps": 25,
        "save_steps": 25,
        "logging_steps": 1,
        "seed": 42,
    }


def _build_steps(args: argparse.Namespace) -> list[ExperimentStep]:
    controlled = _default_controlled_hyperparameters()
    r32 = {**controlled, "lora_r": 32, "lora_alpha": 64}

    best_map = {
        "C": controlled,
        "D": r32,
        "E": controlled,
    }
    best_hparams = best_map[args.best_run]

    steps: list[ExperimentStep] = [
        ExperimentStep(
            code="A",
            name="Base-Modell Referenz (ohne Trainingsjob)",
            dataset_id=args.dataset_id,
            base_model_id=args.base_model,
            trainer_name=args.trainer_name,
            hyperparameters=None,
            requires_training_job=False,
        ),
        ExperimentStep(
            code="B",
            name="Legacy-Konfiguration reproduzieren",
            dataset_id=args.dataset_id,
            base_model_id=args.base_model,
            trainer_name=args.trainer_name,
            hyperparameters=_legacy_hyperparameters(),
            requires_training_job=True,
        ),
        ExperimentStep(
            code="C",
            name="Kontrolllauf (ca. 50-100 Updates)",
            dataset_id=args.dataset_id,
            base_model_id=args.base_model,
            trainer_name=args.trainer_name,
            hyperparameters=controlled,
            requires_training_job=True,
        ),
        ExperimentStep(
            code="D",
            name="Wie C, aber LoRA r=32",
            dataset_id=args.dataset_id,
            base_model_id=args.base_model,
            trainer_name=args.trainer_name,
            hyperparameters=r32,
            requires_training_job=True,
        ),
    ]

    steps.append(
        ExperimentStep(
            code="E",
            name="Bestes Setup mit groesserem Basismodell",
            dataset_id=args.dataset_id,
            base_model_id=args.base_model_e,
            trainer_name=args.trainer_name,
            hyperparameters=best_hparams,
            requires_training_job=bool(args.base_model_e),
        )
    )

    steps.append(
        ExperimentStep(
            code="F",
            name="Bestes Setup auf vergroessertem Datensatz",
            dataset_id=args.dataset_id_f,
            base_model_id=args.base_model_e or args.base_model,
            trainer_name=args.trainer_name,
            hyperparameters=best_hparams,
            requires_training_job=bool(args.dataset_id_f),
        )
    )

    return steps


def _run_preflight(*, api_base: str, user_id: int, step: ExperimentStep, run_label: str) -> dict[str, Any]:
    if step.dataset_id is None:
        raise RuntimeError(f"Step {step.code} has no dataset_id")
    payload = {
        "user_id": user_id,
        "dataset_id": step.dataset_id,
        "base_model_id": step.base_model_id,
        "trainer_name": step.trainer_name,
        "run_label": run_label,
        "hyperparameters": step.hyperparameters or {},
    }
    return _request_json(api_base=api_base, path="/api/training/preflight", payload=payload)


def _create_job(*, api_base: str, user_id: int, step: ExperimentStep, run_label: str) -> dict[str, Any]:
    if step.dataset_id is None:
        raise RuntimeError(f"Step {step.code} has no dataset_id")
    payload = {
        "user_id": user_id,
        "dataset_id": step.dataset_id,
        "base_model_id": step.base_model_id,
        "trainer_name": step.trainer_name,
        "run_label": run_label,
        "hyperparameters": step.hyperparameters or {},
    }
    return _request_json(api_base=api_base, path="/api/training/jobs", payload=payload)


def _write_report(*, report: dict[str, Any], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2), encoding="utf-8")


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Queue reproducible A-F training experiments")
    parser.add_argument("--api-base", default="http://127.0.0.1:8000", help="Training API base URL")
    parser.add_argument("--user-id", type=int, default=1, help="User id")
    parser.add_argument("--dataset-id", type=int, required=True, help="Dataset id for runs B/C/D")
    parser.add_argument("--base-model", required=True, help="Registered base model name or id")
    parser.add_argument("--trainer-name", default="peft_lora", help="Trainer id")
    parser.add_argument("--base-model-e", default="", help="Optional base model for run E")
    parser.add_argument("--dataset-id-f", type=int, default=0, help="Optional enlarged dataset id for run F")
    parser.add_argument("--best-run", choices=["C", "D", "E"], default="D", help="Best setup used for E/F")
    parser.add_argument("--run-tag", default="exp-af", help="Tag prefix for run_label")
    parser.add_argument("--dry-run", action="store_true", help="Do not submit jobs")
    parser.add_argument(
        "--output",
        default="artifacts/jobs/experiment-plan-af-last.json",
        help="Where to write the execution report",
    )
    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    args = parse_args(argv)

    now = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    run_tag = args.run_tag.strip() or "exp-af"
    steps = _build_steps(args)

    report: dict[str, Any] = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "api_base": args.api_base,
        "user_id": args.user_id,
        "run_tag": run_tag,
        "best_run": args.best_run,
        "steps": [],
    }

    for step in steps:
        run_label = f"{run_tag}-{step.code.lower()}-{now}"
        entry: dict[str, Any] = {
            "code": step.code,
            "name": step.name,
            "dataset_id": step.dataset_id,
            "base_model_id": step.base_model_id,
            "trainer_name": step.trainer_name,
            "run_label": run_label,
            "requires_training_job": step.requires_training_job,
        }

        if not step.requires_training_job:
            entry["status"] = "documented_only"
            entry["note"] = "No adapter training queued for this step."
            report["steps"].append(entry)
            continue

        if args.dry_run:
            entry["status"] = "dry_run"
            report["steps"].append(entry)
            continue

        try:
            preflight = _run_preflight(api_base=args.api_base, user_id=args.user_id, step=step, run_label=run_label)
            entry["preflight"] = preflight
            if not bool(preflight.get("ready", False)):
                entry["status"] = "preflight_failed"
                report["steps"].append(entry)
                continue

            created_job = _create_job(api_base=args.api_base, user_id=args.user_id, step=step, run_label=run_label)
            entry["status"] = "queued"
            entry["job_id"] = created_job.get("id")
            entry["job_status"] = created_job.get("status")
        except Exception as exc:  # pragma: no cover - script runtime protection
            entry["status"] = "error"
            entry["error"] = str(exc)
        report["steps"].append(entry)

    output_path = Path(args.output).expanduser().resolve()
    _write_report(report=report, output_path=output_path)

    print(f"Experiment plan report written to: {output_path}")
    for step in report["steps"]:
        code = step.get("code", "?")
        status = step.get("status", "unknown")
        job_id = step.get("job_id")
        suffix = f" (job_id={job_id})" if job_id is not None else ""
        print(f"- {code}: {status}{suffix}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
