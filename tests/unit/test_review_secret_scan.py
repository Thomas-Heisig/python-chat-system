from __future__ import annotations

import importlib
import json
import sys
from pathlib import Path
from types import ModuleType, SimpleNamespace

import pytest


@pytest.fixture
def review_module(monkeypatch: pytest.MonkeyPatch) -> ModuleType:
    scripts = Path(__file__).resolve().parents[2] / "scripts"
    monkeypatch.syspath_prepend(str(scripts))
    return importlib.import_module("review_secret_scan")


@pytest.mark.parametrize("suffix", ["", "-"])
def test_report_parser_reads_current_and_legacy_headings(review_module: ModuleType, suffix: str) -> None:
    report = f"""## Allowlist Trend
### allowed_value_regex{suffix}
- ignored-trend
## Allowlist Entries
### allowed_value_regex{suffix}
- ^example$
### allowed_line_regex{suffix}
- example-line
### allowed_path_regex{suffix}
- docs/example
### unknown
- ignored-heading
## Findings
- ignored-finding
"""
    assert review_module._parse_report_allowlist_entries(report) == {
        "allowed_value_regex": {"^example$"},
        "allowed_line_regex": {"example-line"},
        "allowed_path_regex": {"docs/example"},
    }


@pytest.mark.parametrize(
    ("current_values", "change", "entry"),
    [
        (["^example$", "^added$"], "new", "^added$"),
        ([], "removed", "^example$"),
    ],
)
def test_strict_review_requires_comments_for_real_changes(
    review_module: ModuleType,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    current_values: list[str],
    change: str,
    entry: str,
) -> None:
    reports = tmp_path / "docs" / "security" / "reports"
    reports.mkdir(parents=True)
    (reports / "secret-scan-review-20260718.md").write_text(
        "## Allowlist Entries\n"
        "### allowed_value_regex-\n"
        "- ^example$\n"
        "### allowed_line_regex-\n"
        "- (none)\n"
        "### allowed_path_regex-\n"
        "- (none)\n",
        encoding="utf-8",
    )
    comments = tmp_path / "config" / "secret-scan-change-comments.json"
    monkeypatch.setattr(review_module, "ROOT", tmp_path)
    monkeypatch.setattr(review_module, "REPORTS_DIR", reports)
    monkeypatch.setattr(review_module, "COMMENTS_PATH", comments)
    monkeypatch.setattr(
        review_module,
        "load_allowlist",
        lambda: SimpleNamespace(allowed_value=[], allowed_line=[], allowed_path=[]),
    )
    monkeypatch.setattr(
        review_module,
        "_load_allowlist_raw",
        lambda: {"allowed_value_regex": current_values, "allowed_line_regex": [], "allowed_path_regex": []},
    )
    monkeypatch.setattr(review_module, "list_repo_files", list)
    monkeypatch.setattr(review_module, "iter_targets", list)
    monkeypatch.setattr(review_module, "_git_last_change_date", lambda path: "test")
    monkeypatch.setattr(sys, "argv", ["review_secret_scan.py", "--strict", "--output", "data/temp/review.md"])

    assert review_module.main() == 1
    report = tmp_path / "data" / "temp" / "review.md"
    assert "Comment enforcement active: yes" in report.read_text(encoding="utf-8")
    assert f"allowed_value_regex|{change}|{entry}" in report.read_text(encoding="utf-8")

    comments.parent.mkdir(parents=True)
    comments.write_text(
        json.dumps({"comments": {f"allowed_value_regex|{change}|{entry}": {"reason": "reviewed", "reference": "test"}}}),
        encoding="utf-8",
    )
    assert review_module.main() == 0
    assert "Missing change comments: 0" in report.read_text(encoding="utf-8")
