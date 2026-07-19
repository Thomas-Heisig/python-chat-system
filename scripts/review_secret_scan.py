from __future__ import annotations

import argparse
import datetime as dt
import json
import subprocess
from pathlib import Path

from check_example_secrets import (
    ROOT,
    ALLOWLIST_PATH,
    iter_targets,
    list_repo_files,
    load_allowlist,
    scan_file,
)

REPORTS_DIR = ROOT / "docs" / "security" / "reports"
COMMENTS_PATH = ROOT / "config" / "secret-scan-change-comments.json"


def _normalize_entry(value: object) -> str:
    return str(value).strip()


def _build_change_key(group: str, change_type: str, entry: str) -> str:
    return f"{group}|{change_type}|{entry}"


def _load_allowlist_raw() -> dict[str, list[str]]:
    if not ALLOWLIST_PATH.exists():
        return {}
    try:
        raw = json.loads(ALLOWLIST_PATH.read_text(encoding="utf-8"))
        if isinstance(raw, dict):
            out: dict[str, list[str]] = {}
            for key in ("allowed_value_regex", "allowed_line_regex", "allowed_path_regex"):
                value = raw.get(key, [])
                if isinstance(value, list):
                    out[key] = [str(item) for item in value]
            return out
    except Exception:
        pass
    return {}


def _find_previous_report(current_output_path: Path) -> Path | None:
    if not REPORTS_DIR.exists():
        return None
    candidates = sorted(REPORTS_DIR.glob("secret-scan-review-*.md"))
    filtered = [p for p in candidates if p.resolve() != current_output_path.resolve()]
    if not filtered:
        return None
    return filtered[-1]


def _parse_report_allowlist_entries(report_text: str) -> dict[str, set[str]]:
    entries: dict[str, set[str]] = {
        "allowed_value_regex": set(),
        "allowed_line_regex": set(),
        "allowed_path_regex": set(),
    }
    current_key = ""
    in_entries_section = False
    for line in report_text.splitlines():
        line_stripped = line.strip()
        if line_stripped == "## Allowlist Entries":
            in_entries_section = True
            current_key = ""
            continue
        if line_stripped.startswith("## ") and line_stripped != "## Allowlist Entries":
            in_entries_section = False
            current_key = ""
            continue
        if not in_entries_section:
            continue
        if line_stripped == "### allowed_value_regex":
            current_key = "allowed_value_regex"
            continue
        if line_stripped == "### allowed_line_regex":
            current_key = "allowed_line_regex"
            continue
        if line_stripped == "### allowed_path_regex":
            current_key = "allowed_path_regex"
            continue
        if line_stripped.startswith("### "):
            current_key = ""
            continue
        if current_key and line_stripped.startswith("- "):
            entry = line_stripped[2:].strip()
            if entry and entry != "(none)":
                entries[current_key].add(entry)
    return entries


def _extract_old_snapshot(previous_report: Path | None) -> dict[str, set[str]]:
    if previous_report is None or not previous_report.exists():
        return {
            "allowed_value_regex": set(),
            "allowed_line_regex": set(),
            "allowed_path_regex": set(),
        }
    text = previous_report.read_text(encoding="utf-8", errors="replace")
    return _parse_report_allowlist_entries(text)


def _build_trend(
    current: dict[str, list[str]],
    previous: dict[str, set[str]],
) -> dict[str, dict[str, list[str] | int]]:
    trend: dict[str, dict[str, list[str] | int]] = {}
    for key in ("allowed_value_regex", "allowed_line_regex", "allowed_path_regex"):
        current_set = set(current.get(key, []))
        prev_set = previous.get(key, set())
        new_items = sorted(current_set - prev_set)
        removed_items = sorted(prev_set - current_set)
        unchanged = sorted(current_set & prev_set)
        trend[key] = {
            "new": new_items,
            "removed": removed_items,
            "unchanged_count": len(unchanged),
        }
    return trend


def _collect_changes(trend: dict[str, dict[str, list[str] | int]]) -> list[tuple[str, str, str]]:
    changes: list[tuple[str, str, str]] = []
    for group in ("allowed_value_regex", "allowed_line_regex", "allowed_path_regex"):
        info = trend.get(group, {})
        for entry in info.get("new", []):
            changes.append((group, "new", _normalize_entry(entry)))
        for entry in info.get("removed", []):
            changes.append((group, "removed", _normalize_entry(entry)))
    return changes


def _load_change_comments() -> dict[str, dict[str, str]]:
    if not COMMENTS_PATH.exists():
        return {}
    try:
        raw = json.loads(COMMENTS_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {}
    if not isinstance(raw, dict):
        return {}
    comments = raw.get("comments", {})
    if not isinstance(comments, dict):
        return {}

    normalized: dict[str, dict[str, str]] = {}
    for key, value in comments.items():
        if not isinstance(key, str) or not isinstance(value, dict):
            continue
        reason = str(value.get("reason", "")).strip()
        reference = str(value.get("reference", "")).strip()
        if reason and reference:
            normalized[key.strip()] = {
                "reason": reason,
                "reference": reference,
            }
    return normalized


def _match_change_comments(
    changes: list[tuple[str, str, str]],
    comments: dict[str, dict[str, str]],
) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    matched: list[dict[str, str]] = []
    missing: list[dict[str, str]] = []
    for group, change_type, entry in changes:
        key = _build_change_key(group, change_type, entry)
        comment = comments.get(key)
        if comment:
            matched.append(
                {
                    "group": group,
                    "change": change_type,
                    "entry": entry,
                    "reason": comment["reason"],
                    "reference": comment["reference"],
                    "key": key,
                }
            )
        else:
            missing.append(
                {
                    "group": group,
                    "change": change_type,
                    "entry": entry,
                    "key": key,
                }
            )
    return matched, missing


def _git_last_change_date(path: Path) -> str:
    cmd = ["git", "log", "-1", "--format=%cs", "--", str(path)]
    proc = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, check=False)
    if proc.returncode != 0:
        return "unknown"
    value = proc.stdout.strip()
    return value or "unknown"


def _build_default_output_path() -> Path:
    date_str = dt.date.today().strftime("%Y%m%d")
    return ROOT / "docs" / "security" / "reports" / f"secret-scan-review-{date_str}.md"


def _write_report(
    output_path: Path,
    *,
    findings: list[str],
    scanned_files: int,
    allowed_value_count: int,
    allowed_line_count: int,
    allowed_path_count: int,
    allowlist_last_change: str,
    previous_report: Path | None,
    trend: dict[str, dict[str, list[str] | int]],
    allowlist_raw: dict[str, list[str]],
    matched_comments: list[dict[str, str]],
    missing_comments: list[dict[str, str]],
    comments_enforced: bool,
) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    now = dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    status = "PASS" if not findings else "FAIL"

    lines: list[str] = []
    lines.append("# Secret Scan Review Report")
    lines.append("")
    lines.append(f"- Generated at: {now}")
    lines.append(f"- Status: {status}")
    lines.append(f"- Scanned files: {scanned_files}")
    lines.append(f"- Findings: {len(findings)}")
    lines.append("")
    lines.append("## Allowlist Snapshot")
    lines.append("")
    lines.append(f"- File: config/secret-scan-allowlist.json")
    lines.append(f"- Last change date (git): {allowlist_last_change}")
    lines.append(f"- allowed_value_regex: {allowed_value_count}")
    lines.append(f"- allowed_line_regex: {allowed_line_count}")
    lines.append(f"- allowed_path_regex: {allowed_path_count}")
    lines.append(f"- Previous report: {previous_report.relative_to(ROOT).as_posix() if previous_report else 'none'}")
    lines.append(f"- Change comments file: {COMMENTS_PATH.relative_to(ROOT).as_posix()}")
    lines.append(f"- Missing change comments: {len(missing_comments)}")
    lines.append(f"- Comment enforcement active: {'yes' if comments_enforced else 'no (baseline)'}")
    lines.append("")
    lines.append("## Allowlist Trend")
    lines.append("")

    for key in ("allowed_value_regex", "allowed_line_regex", "allowed_path_regex"):
        info = trend.get(key, {})
        new_items = list(info.get("new", []))
        removed_items = list(info.get("removed", []))
        unchanged_count = int(info.get("unchanged_count", 0) or 0)

        lines.append(f"### {key}")
        lines.append(f"- new: {len(new_items)}")
        lines.append(f"- removed: {len(removed_items)}")
        lines.append(f"- unchanged: {unchanged_count}")
        if new_items:
            lines.append("- new entries:")
            for item in new_items:
                lines.append(f"  - {item}")
        if removed_items:
            lines.append("- removed entries:")
            for item in removed_items:
                lines.append(f"  - {item}")
        lines.append("")

    lines.append("## Allowlist Entries")
    lines.append("")
    for key in ("allowed_value_regex", "allowed_line_regex", "allowed_path_regex"):
        lines.append(f"### {key}")
        for item in allowlist_raw.get(key, []):
            lines.append(f"- {item}")
        if not allowlist_raw.get(key):
            lines.append("- (none)")
        lines.append("")

    lines.append("## Allowlist Change Comments")
    lines.append("")
    if matched_comments:
        lines.append("### Documented changes")
        for item in matched_comments:
            lines.append(
                f"- {item['group']} | {item['change']} | {item['entry']} | reason: {item['reason']} | reference: {item['reference']}"
            )
        lines.append("")
    if missing_comments:
        lines.append("### Missing mandatory comments")
        lines.append("- Add entries to config/secret-scan-change-comments.json under comments")
        for item in missing_comments:
            lines.append(f"- {item['key']}")
        lines.append("")
    if not matched_comments and not missing_comments:
        lines.append("- No allowlist changes compared to previous report.")
        lines.append("")

    lines.append("")
    lines.append("## Findings")
    lines.append("")

    if findings:
        for finding in findings:
            lines.append(f"- {finding}")
    else:
        lines.append("- No findings detected.")

    lines.append("")
    lines.append("## Review Checklist")
    lines.append("")
    lines.append("- Validate each allowlist regex is still needed.")
    lines.append("- Remove stale allowlist entries that no longer match active examples.")
    lines.append("- Confirm no real secrets are covered by broad allowlist patterns.")
    lines.append("- Re-run scripts/check_example_secrets.py after allowlist edits.")
    lines.append("")

    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Run periodic secret-scan review and generate a report")
    parser.add_argument(
        "--output",
        default=str(_build_default_output_path().relative_to(ROOT)),
        help="Output path for markdown report, relative to repository root",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit with code 1 when findings are present",
    )
    args = parser.parse_args()

    output_path = (ROOT / args.output).resolve()

    allowlist = load_allowlist()
    allowlist_raw = _load_allowlist_raw()
    candidates = list_repo_files()
    targets = iter_targets(candidates)

    findings: list[str] = []
    for path in targets:
        findings.extend(scan_file(path, allowlist))

    allowlist_last_change = _git_last_change_date(ALLOWLIST_PATH)
    previous_report = _find_previous_report(output_path)
    old_snapshot = _extract_old_snapshot(previous_report)
    trend = _build_trend(allowlist_raw, old_snapshot)
    changes = _collect_changes(trend)
    comments = _load_change_comments()
    matched_comments, missing_comments = _match_change_comments(changes, comments)
    comments_enforced = previous_report is not None

    _write_report(
        output_path,
        findings=findings,
        scanned_files=len(targets),
        allowed_value_count=len(allowlist.allowed_value),
        allowed_line_count=len(allowlist.allowed_line),
        allowed_path_count=len(allowlist.allowed_path),
        allowlist_last_change=allowlist_last_change,
        previous_report=previous_report,
        trend=trend,
        allowlist_raw=allowlist_raw,
        matched_comments=matched_comments,
        missing_comments=missing_comments,
        comments_enforced=comments_enforced,
    )

    print(f"[secret-review] report written: {output_path.relative_to(ROOT)}")
    print(f"[secret-review] scanned files: {len(targets)}")
    print(f"[secret-review] findings: {len(findings)}")
    print(f"[secret-review] allowlist changes: {len(changes)}")
    print(f"[secret-review] missing change comments: {len(missing_comments)}")

    strict_failed = False
    if findings:
        strict_failed = True
    if comments_enforced and missing_comments:
        strict_failed = True

    if strict_failed and args.strict:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
