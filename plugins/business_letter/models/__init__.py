from .commercial import COMMERCIAL_DOCUMENT_TYPES, COMMUNICATION_DOCUMENT_TYPES, build_commercial_document, normalize_document_kind
from .communication import contains_placeholder, is_email_valid, normalize_attachments, normalize_letter_type, resolve_body_paragraphs
from .parties import build_company_settings, build_recipient, build_salutation
from ..constants import TEMPLATE_MODES

__all__ = [
    "COMMERCIAL_DOCUMENT_TYPES",
    "COMMUNICATION_DOCUMENT_TYPES",
    "TEMPLATE_MODES",
    "build_commercial_document",
    "normalize_document_kind",
    "contains_placeholder",
    "is_email_valid",
    "normalize_attachments",
    "normalize_letter_type",
    "resolve_body_paragraphs",
    "build_company_settings",
    "build_recipient",
    "build_salutation",
]
