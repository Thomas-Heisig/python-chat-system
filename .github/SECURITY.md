# Security Policy

## Supported Versions

Security fixes are provided for the latest `main` branch state.

## Reporting a Vulnerability

Please do not open public issues for security vulnerabilities.

Use one of the following private channels:

1. GitHub Security Advisories (preferred):
   - Go to `Security` tab -> `Report a vulnerability`
2. If unavailable, open a private maintainer contact request.

Please include:

- Affected component and version/commit
- Reproduction steps
- Expected vs actual behavior
- Potential impact
- Suggested mitigation (if known)

## Response Expectations

- Initial triage target: within 3 business days
- Remediation plan target: within 10 business days for confirmed critical issues

## Secret Handling

- Secrets must never be stored in tracked files.
- Use `.env` (not committed), secret managers, or local secure stores.
