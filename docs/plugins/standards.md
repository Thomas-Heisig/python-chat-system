# Plugin Standards

## Metadata Contract

Each plugin defines `PLUGIN_META` with at least:

- id
- name
- description
- category
- intentPattern
- apiKeyRequired
- status
- settingsFields

## Schema Contract

Each plugin should provide:

- input_schema
- output_schema

Schemas should be explicit and stable.

## Execution Contract

Plugin `execute(...)` should return either:

- structured success payload, or
- `{ "error": "..." }` on failure

Prefer deterministic, machine-readable outputs.

## Compatibility

- Prefer additive changes.
- Avoid renaming or removing fields without migration plan.
- Keep aliases for legacy values where practical.

## Documentation

Each plugin should document:

- supported inputs
- output shape
- validation behavior
- examples

System-wide plugin rules belong under `docs/plugins/`, not in a single plugin README.
