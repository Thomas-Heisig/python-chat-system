from __future__ import annotations

import json
from pathlib import Path
from typing import Any

try:
	from jsonschema import Draft202012Validator
	from jsonschema.exceptions import ValidationError
except Exception:  # pragma: no cover - optional dependency fallback
	Draft202012Validator = None  # type: ignore[assignment]
	ValidationError = Exception  # type: ignore[assignment]


class CommunicationContractValidator:
	"""Validates shared communication payload boundaries for selected plugins."""

	SUPPORTED_PLUGIN_IDS = frozenset({"business_letter", "email", "whatsapp", "translator"})

	def __init__(self, *, schema_path: Path | None = None) -> None:
		resolved = schema_path or Path(__file__).resolve().parents[1] / "plugins" / "contracts" / "communication.schema.json"
		self._schema = self._load_schema(resolved)
		self._validator = self._build_validator(self._schema)
		self._status_values = self._extract_enum(self._schema, ["properties", "status"])
		self._reason_values = self._extract_enum(self._schema, ["properties", "reason"])
		self._channel_values = self._extract_enum(self._schema, ["properties", "delivery", "properties", "communication_channel"])

	@classmethod
	def supports_plugin(cls, plugin_id: str) -> bool:
		return plugin_id in cls.SUPPORTED_PLUGIN_IDS

	def validate_input(self, plugin_id: str, payload: dict[str, Any]) -> list[str]:
		if not self.supports_plugin(plugin_id):
			return []
		return self._validate_payload(payload)

	def validate_output(self, plugin_id: str, payload: dict[str, Any]) -> list[str]:
		if not self.supports_plugin(plugin_id):
			return []
		return self._validate_payload(payload)

	def _validate_payload(self, payload: dict[str, Any]) -> list[str]:
		errors: list[str] = []

		validator = self._validator
		if validator is not None:
			schema_errors = sorted(validator.iter_errors(payload), key=self._sort_validation_errors)
			for item in schema_errors:
				errors.append(self._format_schema_error(item))

		if errors:
			return errors

		self._validate_optional_object(payload, "delivery", errors)
		self._validate_optional_object(payload, "content", errors)
		self._validate_optional_object(payload, "metadata", errors)
		self._validate_optional_bool(payload, "validate_only", errors)
		self._validate_optional_enum(payload, "status", self._status_values, errors)
		self._validate_optional_enum(payload, "reason", self._reason_values, errors)

		delivery = payload.get("delivery")
		if isinstance(delivery, dict):
			self._validate_optional_enum(delivery, "communication_channel", self._channel_values, errors, scope="delivery")

		metadata = payload.get("metadata")
		if isinstance(metadata, dict):
			self._validate_optional_bool(metadata, "validate_only", errors, scope="metadata")

		validation = payload.get("validation")
		if validation is not None:
			self._validate_validation_object(validation, errors)

		return errors

	def _build_validator(self, schema: dict[str, Any]) -> Any:
		if not schema or Draft202012Validator is None:
			return None
		try:
			return Draft202012Validator(schema)
		except Exception:
			return None

	def _sort_validation_errors(self, error: ValidationError) -> tuple[str, str]:
		path = ".".join(str(item) for item in error.absolute_path)
		return (path, error.message)

	def _format_schema_error(self, error: ValidationError) -> str:
		path = ".".join(str(item) for item in error.absolute_path)
		if not path:
			path = "root"
		return f"{path}: {error.message}"

	def _validate_validation_object(self, validation: Any, errors: list[str]) -> None:
		if not isinstance(validation, dict):
			errors.append("validation must be an object.")
			return

		required = {"status", "errors", "warnings", "missing_information"}
		missing = sorted(key for key in required if key not in validation)
		if missing:
			errors.append(f"validation missing required fields: {', '.join(missing)}")

		unknown = sorted(key for key in validation if key not in required)
		if unknown:
			errors.append(f"validation has unsupported fields: {', '.join(unknown)}")

		self._validate_optional_enum(validation, "status", self._status_values, errors, scope="validation")
		self._validate_string_list(validation, "errors", errors, scope="validation")
		self._validate_string_list(validation, "warnings", errors, scope="validation")
		self._validate_string_list(validation, "missing_information", errors, scope="validation")

	def _validate_optional_object(
		self,
		payload: dict[str, Any],
		key: str,
		errors: list[str],
		*,
		scope: str = "root",
	) -> None:
		value = payload.get(key)
		if value is None:
			return
		if not isinstance(value, dict):
			errors.append(f"{scope}.{key} must be an object.")

	def _validate_optional_bool(
		self,
		payload: dict[str, Any],
		key: str,
		errors: list[str],
		*,
		scope: str = "root",
	) -> None:
		value = payload.get(key)
		if value is None:
			return
		if not isinstance(value, bool):
			errors.append(f"{scope}.{key} must be a boolean.")

	def _validate_optional_enum(
		self,
		payload: dict[str, Any],
		key: str,
		allowed: set[str],
		errors: list[str],
		*,
		scope: str = "root",
	) -> None:
		value = payload.get(key)
		if value is None:
			return
		if not isinstance(value, str):
			errors.append(f"{scope}.{key} must be a string.")
			return
		if allowed and value not in allowed:
			errors.append(f"{scope}.{key} has invalid value '{value}'.")

	def _validate_string_list(
		self,
		payload: dict[str, Any],
		key: str,
		errors: list[str],
		*,
		scope: str,
	) -> None:
		value = payload.get(key)
		if value is None:
			return
		if not isinstance(value, list):
			errors.append(f"{scope}.{key} must be an array.")
			return
		for index, item in enumerate(value):
			if not isinstance(item, str):
				errors.append(f"{scope}.{key}[{index}] must be a string.")

	def _load_schema(self, schema_path: Path) -> dict[str, Any]:
		try:
			with schema_path.open("r", encoding="utf-8") as handle:
				raw = json.load(handle)
			if isinstance(raw, dict):
				return raw
		except Exception:
			pass
		return {}

	def _extract_enum(self, root: dict[str, Any], path: list[str]) -> set[str]:
		cursor: Any = root
		for key in path:
			if not isinstance(cursor, dict):
				return set()
			cursor = cursor.get(key)
		if isinstance(cursor, list):
			return {str(item) for item in cursor if isinstance(item, str)}
		return set()