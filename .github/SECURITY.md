# Security Policy

## Supported Versions

This project is under active development and has not yet reached version `1.0.0`.

Security fixes are provided for:

| Version | Supported |
|---|---:|
| Latest `main` branch state | ✅ |
| Latest published release | ✅ |
| Older releases and commits | ❌ |
| Modified forks | ❌ |

Before reporting a vulnerability, verify where reasonably possible that it still affects the latest `main` branch state.

## Reporting a Vulnerability

Do not report suspected security vulnerabilities through public issues, pull requests, discussions, or commit comments.

Use GitHub's private vulnerability reporting:

[Report a vulnerability privately](https://github.com/Thomas-Heisig/python-chat-system/security/advisories/new)

If private vulnerability reporting is unavailable, contact the maintainer through a private contact method listed on the maintainer's GitHub profile:

[Thomas-Heisig on GitHub](https://github.com/Thomas-Heisig)

If no private contact method is available, open a public issue requesting private contact without including vulnerability details, credentials, personal data, or proof-of-concept code.

## Information to Include

Please include, where applicable:

- affected component, file, endpoint, or workflow
- affected version or commit SHA
- operating system and relevant runtime versions
- required configuration and preconditions
- reproduction steps
- expected and actual behavior
- potential security impact
- minimal proof of concept
- suggested mitigation, if known
- whether the issue has already been disclosed elsewhere

Do not include real credentials, personal data, private datasets, database contents, or information obtained from systems you do not own or have permission to test.

## Response Targets

The following are targets, not guaranteed service-level commitments:

- acknowledgement and initial triage: within 3 business days
- preliminary assessment of a confirmed critical issue: within 10 business days
- further status updates: when material progress is available

Resolution time depends on severity, reproducibility, affected components, dependency involvement, and available maintainer capacity.

Critical vulnerabilities that are remotely exploitable or expose credentials, private files, internal networks, model artifacts, or training data receive priority.

## Coordinated Disclosure

Please allow reasonable time for investigation, remediation, testing, and release before publishing technical details.

When practical, the reporter will be informed before coordinated disclosure. Public acknowledgement may be provided with the reporter's consent.

This project currently does not operate a bug bounty program and cannot guarantee compensation.

## Secret Handling

Secrets must never be committed to tracked files.

Use:

- an untracked `.env` file
- GitHub Actions secrets
- an operating-system credential store
- an appropriate secret manager

At minimum:

- replace the example `SECRET_KEY`
- never commit `.env`
- rotate any credential that may have been exposed
- avoid placing tokens or passwords in logs
- redact credentials before sharing diagnostics
- review repository history if a secret was committed

Deleting a secret from the latest file version is not sufficient if it remains in Git history. Exposed credentials must always be revoked or rotated.

## Security Scope

Relevant vulnerability classes include, but are not limited to:

- authentication or authorization bypass
- remote code execution
- server-side request forgery
- path traversal or unauthorized file access
- unsafe file or dataset processing
- credential or sensitive-data exposure
- injection vulnerabilities
- insecure deserialization
- privilege escalation
- security-relevant model or training artifact manipulation

Automated scanner results should include a reachable code path or reproducible project-specific impact whenever possible.

## Safe Testing

Security testing must only be performed against systems you own or are explicitly authorized to test.

Do not:

- access, modify, or delete another person's data
- disrupt public or third-party services
- retain unnecessary sensitive information
- publish secrets or personal data
- use destructive payloads when a non-destructive demonstration is sufficient

## Deployment Notice

The project is not currently presented as a fully hardened, directly internet-facing production service.

Public deployments should use, at minimum:

- HTTPS and a reverse proxy
- restricted CORS origins
- secure authentication and secrets
- firewall and filesystem restrictions
- request-size and rate limits
- production settings without automatic reload
- current dependencies and security updates
- trusted model and dataset sources

A successful CI or CodeQL run does not prove that the application is free of security vulnerabilities.
