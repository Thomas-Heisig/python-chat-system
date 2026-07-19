from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parents[1]
ALLOWLIST_PATH = ROOT / "config" / "secret-scan-allowlist.json"

TARGET_PATH_PREFIXES = (
    "docs/",
    "scripts/",
    "deployment/",
)
TARGET_FILE_NAMES = {
    ".env.example",
    ".env.template",
    ".env.sample",
    "README.md",
}
TARGET_SUFFIXES = (
    ".md",
    ".sh",
    ".ps1",
    ".yml",
    ".yaml",
    ".json",
    ".toml",
)

TOKEN_PATTERNS = [
    ("GitHub token", re.compile(r"\b(ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9]{20,}\b")),
    ("OpenAI-style key", re.compile(r"\bsk-[A-Za-z0-9]{20,}\b")),
    ("AWS access key", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("Google API key", re.compile(r"\bAIza[0-9A-Za-z_-]{35}\b")),
    ("Slack token", re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{10,}\b")),
    (
        "JWT token",
        re.compile(r"\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9._-]{10,}\.[A-Za-z0-9._-]{10,}\b"),
    ),
    (
        "Private key block",
        re.compile(r"-----BEGIN (RSA|OPENSSH|EC|DSA|PGP) PRIVATE KEY-----"),
    ),
]

ASSIGNMENT_RE = re.compile(r"^\s*([A-Za-z_][A-Za-z0-9_]*)\s*[:=]\s*(.*?)\s*$")
EXCLUDED_DIR_PREFIXES = (
    "frontend/node_modules/",
    "node_modules/",
    ".venv/",
    ".venv-chat/",
    "training-artifacts/",
    "training-datasets/",
)


def is_sensitive_key_name(key: str) -> bool:
    normalized = key.strip().lower()
    if normalized in {
        "secret",
        "secret_key",
        "api_key",
        "token",
        "access_token",
        "auth_token",
        "bearer_token",
        "password",
        "passwd",
        "private_key",
        "access_key",
        "client_secret",
    }:
        return True

    sensitive_fragments = (
        "_secret",
        "secret_",
        "_api_key",
        "_token",
        "token_",
        "_password",
        "password_",
        "_private_key",
        "_access_key",
        "_client_secret",
    )
    if any(fragment in normalized for fragment in sensitive_fragments):
        # Avoid known non-secret config fields containing token wording.
        if normalized in {"max_tokens", "max_new_tokens", "context_limit_tokens", "context_safety_margin_tokens"}:
            return False
        return True
    return False


class Allowlist:
    def __init__(self, raw: dict[str, list[str]]) -> None:
        self.allowed_value = [re.compile(p) for p in raw.get("allowed_value_regex", [])]
        self.allowed_line = [re.compile(p) for p in raw.get("allowed_line_regex", [])]
        self.allowed_path = [re.compile(p) for p in raw.get("allowed_path_regex", [])]

    def is_allowed_path(self, relative_path: str) -> bool:
        return any(rx.search(relative_path) for rx in self.allowed_path)

    def is_allowed_line(self, line: str) -> bool:
        return any(rx.search(line) for rx in self.allowed_line)

    def is_allowed_value(self, value: str) -> bool:
        normalized = value.strip().strip('"').strip("'")
        if not normalized:
            return True
        return any(rx.search(normalized) for rx in self.allowed_value)


def load_allowlist() -> Allowlist:
    if not ALLOWLIST_PATH.exists():
        return Allowlist({})
    raw = json.loads(ALLOWLIST_PATH.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        return Allowlist({})
    return Allowlist(raw)


def list_repo_files() -> list[Path]:
    results: list[Path] = []
    for path in ROOT.rglob("*"):
        if path.is_file():
            results.append(path)
    return results


def list_staged_files() -> list[Path]:
    cmd = ["git", "diff", "--cached", "--name-only", "--diff-filter=ACMR"]
    proc = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, check=False)
    if proc.returncode != 0:
        return []
    files: list[Path] = []
    for line in proc.stdout.splitlines():
        rel = line.strip()
        if rel:
            files.append(ROOT / rel)
    return files


def is_target(path: Path) -> bool:
    rel = path.relative_to(ROOT).as_posix()
    if rel.startswith(EXCLUDED_DIR_PREFIXES):
        return False
    if path.name in TARGET_FILE_NAMES:
        return rel == "README.md"
    if rel.startswith(TARGET_PATH_PREFIXES):
        return path.suffix.lower() in TARGET_SUFFIXES
    if path.name.startswith(".env"):
        return True
    return False


def iter_targets(candidates: Iterable[Path]) -> list[Path]:
    out: list[Path] = []
    for path in candidates:
        if not path.exists() or not path.is_file():
            continue
        if is_target(path):
            out.append(path)
    return out


def scan_file(path: Path, allowlist: Allowlist) -> list[str]:
    rel = path.relative_to(ROOT).as_posix()
    if allowlist.is_allowed_path(rel):
        return []

    findings: list[str] = []
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    except Exception as exc:  # pragma: no cover
        return [f"{rel}:0: unable to read file ({exc})"]

    for idx, line in enumerate(lines, start=1):
        if allowlist.is_allowed_line(line):
            continue

        for label, rx in TOKEN_PATTERNS:
            if rx.search(line) and not allowlist.is_allowed_value(line):
                findings.append(f"{rel}:{idx}: {label} pattern detected")

        m = ASSIGNMENT_RE.match(line)
        if not m:
            continue

        key = m.group(1).strip()
        value = m.group(2).strip()
        if not is_sensitive_key_name(key):
            continue
        if allowlist.is_allowed_value(value):
            continue

        # Very short values are often labels/placeholders and should not fail scan.
        value_body = value.strip().strip('"').strip("'")
        if len(value_body) < 8:
            continue

        findings.append(f"{rel}:{idx}: suspicious assignment for {key}")

    return findings


def main() -> int:
    parser = argparse.ArgumentParser(description="Scan example/docs/setup files for leaked secrets")
    parser.add_argument("--staged", action="store_true", help="Scan only staged files")
    args = parser.parse_args()

    allowlist = load_allowlist()
    candidates = list_staged_files() if args.staged else list_repo_files()
    targets = iter_targets(candidates)

    findings: list[str] = []
    for path in targets:
        findings.extend(scan_file(path, allowlist))

    if findings:
        print("[secret-check] Potential leaked secrets found:")
        for item in findings:
            print(f"  - {item}")
        print("[secret-check] Review values or extend config/secret-scan-allowlist.json for approved placeholders.")
        return 1

    print(f"[secret-check] OK: scanned {len(targets)} file(s), no leaked secrets detected.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
