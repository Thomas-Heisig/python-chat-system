# Dynamic Plugin Settings

## Goal

All plugins define configurable settings exclusively via `PLUGIN_META.settingsFields`.

The frontend must not contain plugin-specific settings forms.

## Flow

```text
Plugin
  | settingsFields
  v
Backend
  | /api/plugins
  v
Frontend
  | generic renderer
  v
User
  v
Plugin settings persistence
```

## Supported Field Types

- string
- text
- boolean
- number
- password
- select
- multiselect
- color
- url
- email
- integer
- float

## Supported Attributes

- key: unique key
- label: display name
- description: help text
- default: default value
- required: required flag
- group: logical grouping
- placeholder: input placeholder
- options: options for select and multiselect
- validation: validation rules

## Rendering

The frontend creates the settings UI only from metadata.

No plugin-specific settings components.

## Persistence

Settings are stored by `plugin_id`.

Example:

```json
{
  "business_letter": {
    "company_name": "...",
    "company_phone": "...",
    "default_tone": "friendly"
  },
  "email": {
    "smtp_host": "...",
    "smtp_port": 587
  }
}
```

## Benefits

- New plugins need no frontend settings implementation.
- Unified UI and UX.
- Automatic validation support.
- Better maintainability.
- Stable API contract.
