# Plugin System Architecture

## Purpose

The plugin system provides a single contract for discovery, execution, validation, and settings rendering across all plugins.

## Core Principles

- Plugin metadata is the source of truth.
- Backend exposes plugin capabilities via API.
- Frontend renders plugin settings and forms generically.
- Plugin-specific UI logic should be avoided.

## High-Level Flow

```text
Plugin (PLUGIN_META, input_schema, output_schema)
  -> Backend registry
  -> /api/plugins
  -> Frontend generic renderer
  -> User configuration and execution
```

## Runtime Layers

```text
Chat/API Route
  -> Plugin orchestrator/executor
  -> Plugin implementation
  -> Structured result (content, validation, metadata)
```

## Stability Rules

- Keep plugin API contracts backwards compatible when possible.
- Additive schema changes are preferred over breaking changes.
- Validation output should be structured and machine-readable.
- Settings must be represented in metadata, not hardcoded UI.
