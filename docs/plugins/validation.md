# Plugin Validation Guidelines

## Goals

- Provide consistent validation behavior.
- Keep validation machine-readable.
- Separate hard errors from review warnings.

## Validation Model

Recommended structure:

```json
{
  "status": "ready|needs_review",
  "errors": [],
  "warnings": [],
  "missing_information": []
}
```

## Rules

- Errors block ready-to-send behavior.
- Warnings signal review issues but may not block.
- `missing_information` lists actionable missing fields.
- Validation should be deterministic for identical input.

## Communication Plugins

For communication-oriented plugins (letter/email/etc.):

- Validate recipient channel requirements.
- Validate address or email format by channel.
- Validate required attachments and references.
- Detect placeholders that should block final send state.

## Status Resolution

If plugin supports status fields:

- Validation errors take precedence.
- Explicit status values may be accepted only from allowed enum.
- `ready_for_sending=true` should only become `ready` if no blocking errors exist.
