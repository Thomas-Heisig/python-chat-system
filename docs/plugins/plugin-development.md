# Plugin Development Guide

## 1. Purpose

This guide defines the required standards for implementing plugins consistently across backend and frontend.

## 2. Required Components

Every plugin should include:

- `PLUGIN_META`
- `input_schema`
- `output_schema`
- `execute(...)`

## 3. Metadata (`PLUGIN_META`)

Minimum recommended fields:

- `id`
- `name`
- `description`
- `category`
- `intentPattern`
- `apiKeyRequired`
- `status`
- `settingsFields`

`settingsFields` is the only supported source for dynamic plugin settings UI.

## 4. Settings Fields

Define settings declaratively using metadata.

Recommended field properties:

- key
- label
- type
- description
- default
- required
- group
- placeholder
- options
- validation

See `docs/plugins/settings.md`.

## 5. Input and Output Schemas

- Keep schemas explicit and strongly typed.
- Use enums for constrained values.
- Add aliases in runtime normalization when legacy values exist.
- Keep outputs stable and machine-readable.

## 6. Validation

Return structured validation whenever relevant.

Recommended keys:

- status
- errors
- warnings
- missing_information

See `docs/plugins/validation.md`.

## 7. Error Handling

- Return deterministic error payloads (`{ "error": "..." }`).
- Avoid leaking internal stack traces to API consumers.

## 8. Frontend Integration

- Frontend should rely on `/api/plugins` metadata.
- Do not require plugin-specific settings components.
- Rendering must be metadata-driven.

## 9. Tests

Each plugin should include tests for:

- schema compatibility
- normalization and aliasing
- validation outcomes
- expected success and failure paths

## 10. Documentation

- Plugin-specific usage remains in plugin README.
- Cross-plugin standards belong under `docs/plugins/`.

## 11. Backwards Compatibility

- Prefer additive changes.
- Keep legacy fallbacks where possible.
- Document behavior changes in changelog.
