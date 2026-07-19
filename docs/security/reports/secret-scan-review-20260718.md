# Secret Scan Review Report

- Generated at: 2026-07-18 11:48:37
- Status: PASS
- Scanned files: 33
- Findings: 0

## Allowlist Snapshot

- File: config/secret-scan-allowlist.json
- Last change date (git): unknown
- allowed_value_regex: 17
- allowed_line_regex: 5
- allowed_path_regex: 1
- Previous report: none
- Change comments file: config/secret-scan-change-comments.json
- Missing change comments: 23
- Comment enforcement active: no (baseline)

## Allowlist Trend

### allowed_value_regex

- new: 17
- removed: 0
- unchanged: 0
- new entries:
  - (?i)^change-me$
  - (?i)^change-this-key$
  - (?i)^changeme$
  - (?i)^dummy$
  - (?i)^example$
  - (?i)^example-value$
  - (?i)^insert-[a-z0-9-]+$
  - (?i)^none$
  - (?i)^null$
  - (?i)^placeholder$
  - (?i)^put-[a-z0-9-]+$
  - (?i)^replace-me$
  - (?i)^sample$
  - (?i)^tbd$
  - (?i)^todo$
  - (?i)^your-[a-z0-9-]+$
  - ^<[^>]+>$

### allowed_line_regex

- new: 5
- removed: 0
- unchanged: 0
- new entries:
  - (?i)127\.0\.0\.1
  - (?i)^\s*#
  - (?i)example\.com
  - (?i)gitleaks/gitleaks-action@
  - (?i)localhost

### allowed_path_regex

- new: 1
- removed: 0
- unchanged: 0
- new entries:
  - ^data/backups/

## Allowlist Entries

### allowed_value_regex-

- (?i)^change-this-key$
- (?i)^changeme$
- (?i)^change-me$
- (?i)^replace-me$
- (?i)^example$
- (?i)^example-value$
- (?i)^sample$
- (?i)^placeholder$
- (?i)^dummy$
- (?i)^none$
- (?i)^null$
- (?i)^todo$
- (?i)^tbd$
- (?i)^your-[a-z0-9-]+$
- (?i)^insert-[a-z0-9-]+$
- (?i)^put-[a-z0-9-]+$
- ^<[^>]+>$

### allowed_line_regex-

- (?i)^\s*#
- (?i)gitleaks/gitleaks-action@
- (?i)example\.com
- (?i)localhost
- (?i)127\.0\.0\.1

### allowed_path_regex-

- ^data/backups/

## Allowlist Change Comments

### Missing mandatory comments

- Add entries to config/secret-scan-change-comments.json under comments
- allowed_value_regex|new|(?i)^change-me$
- allowed_value_regex|new|(?i)^change-this-key$
- allowed_value_regex|new|(?i)^changeme$
- allowed_value_regex|new|(?i)^dummy$
- allowed_value_regex|new|(?i)^example$
- allowed_value_regex|new|(?i)^example-value$
- allowed_value_regex|new|(?i)^insert-[a-z0-9-]+$
- allowed_value_regex|new|(?i)^none$
- allowed_value_regex|new|(?i)^null$
- allowed_value_regex|new|(?i)^placeholder$
- allowed_value_regex|new|(?i)^put-[a-z0-9-]+$
- allowed_value_regex|new|(?i)^replace-me$
- allowed_value_regex|new|(?i)^sample$
- allowed_value_regex|new|(?i)^tbd$
- allowed_value_regex|new|(?i)^todo$
- allowed_value_regex|new|(?i)^your-[a-z0-9-]+$
- allowed_value_regex|new|^<[^>]+>$
- allowed_line_regex|new|(?i)127\.0\.0\.1
- allowed_line_regex|new|(?i)^\s*#
- allowed_line_regex|new|(?i)example\.com
- allowed_line_regex|new|(?i)gitleaks/gitleaks-action@
- allowed_line_regex|new|(?i)localhost
- allowed_path_regex|new|^data/backups/

## Findings

- No findings detected.

## Review Checklist

- Validate each allowlist regex is still needed.
- Remove stale allowlist entries that no longer match active examples.
- Confirm no real secrets are covered by broad allowlist patterns.
- Re-run scripts/check_example_secrets.py after allowlist edits.
