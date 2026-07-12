## Summary

Describe what this pull request changes and why the change is needed.

<!--
Keep the summary concise. Explain the problem and the intended outcome,
not only the files that were modified.
-->

## Related Issue

<!--
Use "Closes #123", "Fixes #123", or "Related to #123".
Write "None" if no issue exists.
-->

Closes #

## Type of Change

Select all that apply:

- [ ] Breaking change
- [ ] Feature
- [ ] Bug fix
- [ ] Security fix
- [ ] Performance improvement
- [ ] Refactor
- [ ] Dependency update
- [ ] Test
- [ ] Documentation
- [ ] CI/CD
- [ ] Maintenance

## Affected Areas

Select all that apply:

- [ ] Backend/API
- [ ] Frontend/UI
- [ ] Database or persistence
- [ ] Authentication or authorization
- [ ] Settings
- [ ] Chat or streaming
- [ ] Model discovery or loading
- [ ] Training Workbench
- [ ] Dataset import or validation
- [ ] Evaluation or model registration
- [ ] Start or setup scripts
- [ ] GitHub workflows
- [ ] Documentation only

## Implementation

Describe the main implementation decisions.

<!--
Mention relevant design choices, alternatives considered, and important
limitations. Avoid repeating the complete diff.
-->

## Behavior Before

Describe the previous behavior or limitation.

## Behavior After

Describe the behavior after this change.

## Breaking Changes

- [ ] This pull request contains no breaking changes.
- [ ] This pull request contains breaking changes described below.

<!--
Describe affected APIs, settings, files, database structures, scripts,
model formats, or user workflows. State how users should migrate.
-->

## Security Review

- [ ] No credentials, secrets, tokens, or private data were added.
- [ ] Logs and error responses do not expose sensitive information.
- [ ] New file paths and user-controlled input are validated.
- [ ] Network requests and redirects are validated where applicable.
- [ ] Authentication and authorization were reviewed where applicable.
- [ ] Uploaded files, datasets, models, and archives are handled safely where applicable.
- [ ] Security implications are described below or are not applicable.

### Security Notes

<!--
Describe security-sensitive behavior, trust boundaries, input validation,
permissions, or remaining risks. Write "Not applicable" if appropriate.
Do not include real secrets, private data, or working exploits.
-->

## Database and Configuration

- [ ] No database or configuration changes.
- [ ] Database changes are backward compatible.
- [ ] A migration or explicit migration instructions are included.
- [ ] `.env.example` was updated if environment variables changed.
- [ ] New settings include safe defaults and validation.
- [ ] Configuration changes are documented below.

### Migration or Configuration Notes

<!--
Describe required environment variables, setting changes, data migrations,
restart requirements, or rollback steps. Write "Not applicable" if none.
-->

## Model, Dataset, and Training Impact

- [ ] No model, dataset, or training impact.
- [ ] Model loading or activation was tested.
- [ ] Dataset parsing or validation was tested.
- [ ] Training preflight behavior was tested.
- [ ] Training changes distinguish simulated and real runs.
- [ ] GPU, CPU, CUDA, RAM, and VRAM implications were considered.
- [ ] Compatibility limitations are documented below.

### AI/Training Notes

<!--
State the model format, trainer, dataset format, hardware assumptions,
or compatibility limitations. Do not attach private model or dataset data.
-->

## Validation

Mark checks as completed or explain why they are not applicable.

### Backend

- [ ] Backend tests pass: `pytest`
- [ ] Python linting passes: `ruff check .`
- [ ] Backend test not applicable to this change

### Frontend

- [ ] Frontend tests pass: `npm run test:run`
- [ ] Frontend build passes: `npm run build`
- [ ] Frontend validation not applicable to this change

### Dependencies

- [ ] Frontend dependency audit passes: `npm audit`
- [ ] Dependency review is not applicable to this change
- [ ] New or updated dependencies are justified below

### Manual Validation

Describe the manual checks performed:

```text
1.
2.
3.
```

Add links, screenshots, or command outputs when they help reviewers verify behavior.