# Communication Plugin Conventions

Canonical reference:

- `docs/plugins/communication-contract.md`
- `app/plugins/contracts/communication.schema.json`

## Scope

Applies to plugins that generate or process communication artifacts:

- letters
- emails
- customer-facing notices

## Output Shape

Recommended top-level keys:

- letter
- email
- content
- document
- validation
- delivery
- metadata

## Channel Behavior

Support explicit channel selection when applicable:

- letter
- email
- both

Invalid channel values should fall back to a safe default.

## Delivery Metadata

Include structured delivery fields when possible:

- channel
- recipient
- subject
- reply_to
- requested_send_at

## Traceability

Include metadata for lifecycle and auditability:

- document_id
- created_at
- created_by
- approved_at
- approved_by
- sent_at
- status
- conversation_id

## Safety

- Validate contact data format.
- Avoid sending-ready status with placeholder business data.
- Distinguish between draft, review, ready, and post-send statuses.
