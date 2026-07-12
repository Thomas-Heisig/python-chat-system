# Contributing

Thank you for contributing.

## Quick Start

1. Fork the repository and create a feature branch from `main`.
2. Install dependencies:
   - Backend: `pip install -r requirements-dev.txt`
   - Frontend: `cd frontend && npm ci`
3. Run checks locally:
   - Backend tests: `pytest`
   - Frontend build: `cd frontend && npm run build`
4. Open a Pull Request using the PR template.

## Branch and Commit Guidelines

- Use small, focused commits.
- Use descriptive commit messages.
- Keep PRs focused on one change set.

## Pull Request Checklist

- Add or update tests for behavioral changes.
- Update documentation for user-visible changes.
- Ensure no secrets, credentials, or private data are committed.
- Ensure CI is green.

## Development Notes

- Keep architectural boundaries intact (`API -> Services -> Repositories -> DB`).
- Avoid duplicate implementations when equivalent modules already exist.
- Prefer extension of existing components over introducing parallel structures.

## Security and Secrets

- Never commit real passwords, API keys, tokens, or private certificates.
- Use environment variables or local non-versioned secret stores.
- If you discover a vulnerability, see `SECURITY.md`.
