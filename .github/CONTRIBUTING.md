# Contributing

Thank you for considering a contribution to Kernschmiede.

This project is under active development. Contributions should remain focused, testable, and consistent with the existing architecture.

Before starting a larger change, open an issue to discuss the intended behavior and implementation direction.

## Code of Conduct

All contributors must follow the [Code of Conduct](CODE_OF_CONDUCT.md).

Security vulnerabilities must not be reported through public issues or pull requests. Follow the process described in the [Security Policy](SECURITY.md).

## Ways to Contribute

Contributions may include:

- bug fixes
- tests
- documentation corrections
- frontend improvements
- backend and API improvements
- model backend integrations
- dataset validation improvements
- Training Workbench improvements
- performance improvements
- security hardening
- CI and development tooling
- well-defined feature proposals

Support requests and configuration questions should follow the [Support Guide](SUPPORT.md).

## Before You Start

Before implementing a change:

1. Search existing issues and pull requests.
2. Review the current [`README.md`](../README.md).
3. Check [`docs/ROADMAP.md`](../docs/ROADMAP.md).
4. Check [`docs/todo.md`](../docs/todo.md).
5. Review relevant architecture documentation.
6. Confirm that an equivalent implementation does not already exist.
7. Open an issue before beginning a large or breaking change.

An issue is especially recommended for:

- database schema changes
- new model backends
- new trainer implementations
- authentication or authorization changes
- public API changes
- new dependencies
- changes to dataset formats
- changes to training lifecycle states
- major frontend restructuring
- changes affecting security boundaries

## Development Environment

### Recommended versions

- Python 3.12
- Node.js 22.13 or a compatible newer Node 22 release
- npm
- Git

GPU-dependent development may additionally require:

- an NVIDIA GPU
- compatible NVIDIA drivers
- CUDA-compatible PyTorch
- llama-cpp-python with appropriate acceleration support
- bitsandbytes for supported 4-bit workflows

Not every contribution requires a GPU. CPU-compatible tests should be preferred where practical.

## Repository Setup

### 1. Fork and clone

```bash
git clone https://github.com/<your-user>/python-chat-system.git
cd python-chat-system
git remote add upstream https://github.com/Thomas-Heisig/python-chat-system.git
```

### 2. Create a branch from the current `main`

```bash
git fetch upstream
git switch main
git pull --ff-only upstream main
git switch -c <type>/<short-description>
```

Examples:

```text
feature/training-preflight
fix/stream-error-handling
security/dataset-url-validation
docs/update-installation
refactor/model-manager
ci/split-test-jobs
```

### 3. Create the Python environment

Linux/macOS:

```bash
python3.12 -m venv .venv-chat
source .venv-chat/bin/activate
python -m pip install --upgrade pip
pip install -r requirements-dev.txt
```

Windows PowerShell:

```powershell
py -3.12 -m venv .venv-chat
.\.venv-chat\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements-dev.txt
```

### 4. Install frontend dependencies

```bash
cd frontend
npm ci
cd ..
```

### 5. Create local configuration

Linux/macOS:

```bash
cp .env.example .env
```

Windows PowerShell:

```powershell
Copy-Item .env.example .env
```

Replace the example `SECRET_KEY` with a local value. Never commit `.env`.

## Running the Application

### Backend only

```bash
python start.py --reload
```

### Backend and frontend

Windows:

```powershell
.\scripts\start_fullstack.ps1
```

Linux/macOS:

```bash
./scripts/start_fullstack.sh
```

### Initialization only

```bash
python start.py --init-only
```

Initialization without a model scan:

```bash
python start.py --init-only --skip-model-scan
```

## Architecture Rules

Preserve the existing architectural boundaries:

```text
API routes
    ↓
Services
    ↓
Repositories
    ↓
Database
```

General rules:

- API routes should validate requests and translate service results into HTTP responses.
- Business logic should reside in services rather than route handlers.
- Database access should go through repositories where an appropriate repository exists.
- Pydantic schemas and persistence models should remain separate where their responsibilities differ.
- Shared logic should be extracted only when there is a real shared responsibility.
- Existing components should be extended instead of introducing parallel implementations.
- Avoid hidden global state.
- Avoid blocking operations inside async request paths.
- Use explicit dependency injection where the project already provides it.
- Keep model, chat, settings, and training domains separated.
- New abstractions should solve a current problem rather than only a hypothetical future one.

Architecture changes should be described in the pull request.

## Backend Guidelines

- Use type hints for new or modified Python code.
- Keep functions focused and reasonably small.
- Prefer explicit error handling.
- Do not expose internal exception messages through API responses.
- Avoid broad `except Exception` blocks unless errors are safely translated or logged.
- Do not perform blocking model, file, network, or training operations directly on the event loop.
- Validate all user-controlled file paths and network targets.
- Use parameterized SQLAlchemy operations.
- Keep HTTP-specific behavior out of repositories.
- Use timezone-aware timestamps.
- Add tests for new API and service behavior.

Avoid storing sensitive request data in logs.

## Frontend Guidelines

- Use TypeScript for new frontend code.
- Reuse existing components, hooks, API clients, and query patterns.
- Keep server state in the established TanStack Query layer.
- Avoid duplicating backend validation as the only validation mechanism.
- Keep visible error messages useful but free of internal implementation details.
- Consider loading, empty, error, disabled, and success states.
- Preserve keyboard accessibility and usable labels.
- Add tests for meaningful interaction and state changes.
- Run the production build before opening a pull request.

Do not commit generated `frontend/dist` output unless explicitly required.

## Model Backend Guidelines

Changes to model discovery, loading, activation, or generation should consider:

- model format
- backend compatibility
- CPU behavior
- GPU behavior
- RAM and VRAM requirements
- rollback behavior
- streaming behavior
- cancellation and concurrent requests
- local path validation
- error redaction
- resource cleanup after failure

Do not add or commit model weights to the repository.

Tests should use small fixtures, mocks, or reference implementations rather than requiring large models.

## Dataset and Training Guidelines

Dataset and training changes should preserve the distinction between:

- imported raw sources
- parsed records
- validated training examples
- reviewed datasets
- training-ready datasets
- simulated jobs
- real training jobs
- saved artifacts
- registered adapters or models

Contributions should consider:

- dataset schema validation
- duplicate detection
- token limits
- secret and personal-data detection
- safe HTML and document parsing
- SSRF protection for URL imports
- file path restrictions
- deterministic dataset splits
- reproducibility metadata
- training preflight checks
- cancellation and failure states
- artifact verification
- CPU, GPU and 4-bit requirements

Do not commit private, proprietary, personal, or license-incompatible datasets.

Training tests should not require expensive real training unless the contribution specifically requires an integration test and the test is clearly marked.

## Security Requirements

Never commit:

- passwords
- API keys
- access tokens
- session cookies
- private certificates or keys
- `.env` files
- database files containing real data
- private chat histories
- personal information
- proprietary models
- confidential datasets
- internal infrastructure details

Use:

- environment variables
- GitHub Actions secrets
- local untracked configuration
- operating-system credential stores
- dedicated secret managers

If a secret is committed accidentally:

1. revoke or rotate it immediately,
2. notify the maintainer privately,
3. remove it from the affected files,
4. assess whether repository history must be cleaned.

Deleting the current file content does not invalidate a secret already present in Git history.

## Dependencies

New dependencies require justification.

Before adding a dependency, consider:

- whether the standard library or an existing dependency is sufficient
- maintenance activity
- security history
- license compatibility
- installation size
- platform compatibility
- Python or Node version requirements
- GPU or CUDA coupling
- impact on startup and build time

When changing dependencies:

- update the relevant manifest,
- update the lockfile where applicable,
- run relevant tests,
- run `npm audit` for frontend changes,
- document compatibility changes.

Do not manually edit `frontend/package-lock.json` unless necessary. Prefer regenerating it through npm.

## Database Changes

Database changes must include:

- a description of the schema impact
- backward-compatibility considerations
- migration or transition instructions
- rollback considerations
- tests for affected repositories and services

Do not silently delete or reinterpret existing data.

Until a formal migration system is fully established, database changes require particular care and explicit documentation.

## Testing

Run checks relevant to the change.

### Backend tests

```bash
pytest
```

### Python linting

```bash
ruff check .
```

### Frontend tests

```bash
cd frontend
npm run test:run
```

### Frontend production build

```bash
cd frontend
npm run build
```

### Frontend dependency audit

```bash
cd frontend
npm audit
```

A documentation-only change does not require every runtime test, but the pull request should state which checks were not applicable.

Tests should:

- be deterministic
- avoid external network access unless explicitly testing an integration
- avoid dependence on large local models
- clean up temporary files and database records
- cover failure paths as well as successful paths
- avoid real secrets and personal data

## Test Expectations

| Change | Expected validation |
|---|---|
| Backend behavior | `pytest`, `ruff check .` |
| API route | route and service tests |
| Database behavior | repository/service tests |
| Frontend behavior | `npm run test:run`, `npm run build` |
| Dependency update | relevant tests, build and audit |
| Security fix | regression test for the affected path |
| Dataset parser | valid, malformed and hostile input tests |
| Training logic | preflight, state and failure-path tests |
| Documentation only | link and command review |
| CI workflow | workflow syntax and affected job review |

If a relevant test cannot be added, explain why in the pull request.

## Documentation

Update documentation when behavior, configuration, architecture, or planning changes.

Relevant files include:

- `README.md`
- `.env.example`
- `docs/changelog.md`
- `docs/ROADMAP.md`
- `docs/todo.md`
- `docs/training-workbench.md`
- API or architecture documentation

Guidance:

- Update `docs/changelog.md` for user-visible behavior.
- Update `docs/ROADMAP.md` when planned direction changes.
- Update `docs/todo.md` when follow-up work changes.
- Update `.env.example` when environment variables change.
- Do not document planned behavior as already implemented.
- Keep commands and file paths verifiable.

## Commit Guidelines

Use small, focused commits with descriptive messages.

Recommended format:

```text
<type>(<scope>): <short description>
```

Examples:

```text
feat(training): add dataset preflight validation
fix(chat): redact internal streaming errors
security(models): reject unsafe model paths
test(api): cover conversation-not-found response
docs(readme): clarify Python setup
ci(actions): update CodeQL workflow
deps(frontend): update React dependencies
```

Suggested types:

- `feat`
- `fix`
- `security`
- `refactor`
- `test`
- `docs`
- `ci`
- `deps`
- `chore`

Avoid:

- unrelated changes in the same commit
- vague messages such as `update`, `changes`, or `fix stuff`
- committed debug output
- formatting unrelated files without reason
- generated or local files not needed by the project

## Pull Requests

Pull requests should:

- address one coherent change
- use the pull request template
- link the related issue where applicable
- describe previous and new behavior
- explain significant implementation decisions
- identify breaking changes
- include validation results
- include migration or rollback notes where relevant
- contain no secrets or private data
- remain reviewable in size

Draft pull requests are appropriate for early feedback on larger work.

Do not mark a pull request as ready for review while known required checks are failing without explanation.

## Labels and Release Notes

Use labels that match the change where possible:

- `feature`
- `enhancement`
- `bug`
- `fix`
- `security`
- `performance`
- `refactor`
- `dependencies`
- `tests`
- `documentation`
- `maintenance`
- `chore`
- `ci`
- `backend`
- `frontend`
- `training`
- `breaking-change`
- `skip-changelog`

These labels are used by Release Drafter and repository automation.

Use `breaking-change` only when users must change configuration, API usage, data, scripts, or deployment behavior.

Use `skip-changelog` only for changes that should not appear in public release notes.

## Review Process

Reviewers may request changes for:

- incorrect behavior
- missing tests
- unsafe input handling
- architecture violations
- unhandled compatibility impact
- unnecessary dependencies
- unclear documentation
- excessive scope
- secrets or private data
- missing migration or rollback information

Approval does not guarantee immediate merge. A pull request may remain open while related design, compatibility, or security questions are resolved.

## After Review

Before merge:

- resolve actionable review comments
- update the branch if required
- rerun affected checks
- confirm documentation is current
- confirm no debugging artifacts remain
- verify the final diff
- confirm that the PR title and labels are accurate

## Reporting Security Issues

Do not open a public issue for a vulnerability.

Follow [SECURITY.md](SECURITY.md) and use GitHub private vulnerability reporting where available.
