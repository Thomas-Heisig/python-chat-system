from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.tools.registry import PluginDefinition

try:
    from jsonschema import Draft202012Validator
except Exception:  # pragma: no cover - optional runtime dependency
    Draft202012Validator = None  # type: ignore[assignment]


class PluginPolicyError(RuntimeError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


@dataclass(frozen=True)
class ExecutionContext:
    user_id: int | None
    team_id: int | None
    request_id: str
    confirmation_id: str
    dry_run: bool
    confirmed: bool
    idempotency_key: str
    granted_permissions: set[str]
    allowed_plugins: set[str]
    enforce_permissions: bool


class PluginExecutionPolicy:
    """Centralized gatekeeper for plugin execution safety and policy checks."""

    _NON_MUTATING_SIDE_EFFECTS = {"", "none", "read_only", "query"}

    def validate(
        self,
        *,
        definition: PluginDefinition,
        function_meta: dict[str, Any],
        input_data: dict[str, Any],
        plugin_settings: dict[str, Any] | None,
        execution_context: dict[str, Any] | None,
    ) -> ExecutionContext:
        context = self._normalize_context(execution_context)
        settings = plugin_settings if isinstance(plugin_settings, dict) else {}

        self._ensure_plugin_enabled(definition, settings)
        self._ensure_plugin_scope_access(definition.plugin_id, settings, context)
        self._ensure_function_permissions(function_meta, context)
        self._ensure_confirmation(function_meta, context)
        self._ensure_dry_run_support(function_meta, context)
        self._ensure_idempotency(definition.plugin_id, function_meta, input_data, context)
        self._validate_input_schema(definition, function_meta, input_data)

        return context

    def _normalize_context(self, raw: dict[str, Any] | None) -> ExecutionContext:
        payload = raw if isinstance(raw, dict) else {}

        granted_permissions = {
            str(item).strip()
            for item in self._to_list(payload.get("granted_permissions"))
            if str(item).strip()
        }
        allowed_plugins = {
            str(item).strip()
            for item in self._to_list(payload.get("allowed_plugins"))
            if str(item).strip()
        }

        return ExecutionContext(
            user_id=self._to_optional_int(payload.get("user_id")),
            team_id=self._to_optional_int(payload.get("team_id")),
            request_id=str(payload.get("request_id") or "").strip(),
            confirmation_id=str(payload.get("confirmation_id") or "").strip(),
            dry_run=bool(payload.get("dry_run", False)),
            confirmed=bool(payload.get("confirmed", False)),
            idempotency_key=str(payload.get("idempotency_key") or "").strip(),
            granted_permissions=granted_permissions,
            allowed_plugins=allowed_plugins,
            enforce_permissions=bool(payload.get("enforce_permissions", False)),
        )

    def _ensure_plugin_enabled(self, definition: PluginDefinition, settings: dict[str, Any]) -> None:
        if str(definition.status).strip().lower() != "implemented":
            raise PluginPolicyError("plugin_not_active", f"Plugin is not active: {definition.plugin_id}")

        enabled_value = settings.get("enabled", settings.get("plugin_enabled", True))
        if isinstance(enabled_value, bool) and not enabled_value:
            raise PluginPolicyError("plugin_disabled", f"Plugin is disabled: {definition.plugin_id}")

    def _ensure_plugin_scope_access(
        self,
        plugin_id: str,
        settings: dict[str, Any],
        context: ExecutionContext,
    ) -> None:
        if context.allowed_plugins and plugin_id not in context.allowed_plugins:
            raise PluginPolicyError(
                "plugin_scope_denied",
                f"Plugin '{plugin_id}' is not in the allowed plugin scope.",
            )

        allowed_user_ids = {value for value in self._to_int_set(settings.get("allowed_user_ids")) if value is not None}
        if allowed_user_ids:
            if context.user_id is None or context.user_id not in allowed_user_ids:
                raise PluginPolicyError("plugin_user_denied", f"User is not allowed for plugin '{plugin_id}'.")

        allowed_team_ids = {value for value in self._to_int_set(settings.get("allowed_team_ids")) if value is not None}
        if allowed_team_ids:
            if context.team_id is None or context.team_id not in allowed_team_ids:
                raise PluginPolicyError("plugin_team_denied", f"Team is not allowed for plugin '{plugin_id}'.")

    def _ensure_function_permissions(self, function_meta: dict[str, Any], context: ExecutionContext) -> None:
        required_permissions = {
            str(item).strip()
            for item in self._to_list(function_meta.get("required_permissions"))
            if str(item).strip()
        }
        if not required_permissions:
            return

        if not context.enforce_permissions:
            return

        if not context.granted_permissions:
            raise PluginPolicyError(
                "plugin_permission_missing",
                f"Missing required permissions: {', '.join(sorted(required_permissions))}",
            )

        missing = required_permissions.difference(context.granted_permissions)
        if missing:
            raise PluginPolicyError(
                "plugin_permission_missing",
                f"Missing required permissions: {', '.join(sorted(missing))}",
            )

    def _ensure_confirmation(self, function_meta: dict[str, Any], context: ExecutionContext) -> None:
        requires_confirmation = bool(function_meta.get("requires_confirmation", False))
        if requires_confirmation and not context.confirmed and not context.dry_run:
            raise PluginPolicyError(
                "plugin_confirmation_required",
                "Function requires explicit confirmation before execution.",
            )

    def _ensure_dry_run_support(self, function_meta: dict[str, Any], context: ExecutionContext) -> None:
        if not context.dry_run:
            return

        supports_dry_run = bool(function_meta.get("supports_dry_run", False))
        if not supports_dry_run:
            raise PluginPolicyError(
                "plugin_dry_run_not_supported",
                "Function does not support dry_run execution.",
            )

    def _ensure_idempotency(
        self,
        plugin_id: str,
        function_meta: dict[str, Any],
        input_data: dict[str, Any],
        context: ExecutionContext,
    ) -> None:
        if context.dry_run:
            return

        function_name = str(function_meta.get("name") or "execute").strip() or "execute"
        read_only = bool(function_meta.get("read_only", False))
        side_effect = str(function_meta.get("side_effect") or "").strip().lower()
        known_mutating_side_effect = side_effect not in self._NON_MUTATING_SIDE_EFFECTS and side_effect != "unknown"
        requires_idempotency = known_mutating_side_effect

        if requires_idempotency and not context.idempotency_key:
            raise PluginPolicyError(
                "plugin_idempotency_key_required",
                "Mutating plugin functions require an idempotency_key.",
            )

        if not context.idempotency_key:
            return

        if len(context.idempotency_key) < 4:
            raise PluginPolicyError(
                "plugin_idempotency_key_invalid",
                "Idempotency key is too short.",
            )

    def _validate_input_schema(
        self,
        definition: PluginDefinition,
        function_meta: dict[str, Any],
        input_data: dict[str, Any],
    ) -> None:
        if Draft202012Validator is None:
            return

        schema = function_meta.get("input_schema")
        if not isinstance(schema, dict) or not schema:
            schema = definition.input_schema
        if not isinstance(schema, dict) or not schema:
            return

        validator = Draft202012Validator(schema)
        errors = sorted(validator.iter_errors(input_data), key=lambda item: list(item.path))
        if not errors:
            return

        messages: list[str] = []
        for error in errors[:5]:
            path = ".".join(str(part) for part in error.path)
            if path:
                messages.append(f"{path}: {error.message}")
            else:
                messages.append(str(error.message))
        raise PluginPolicyError("plugin_input_schema_invalid", "; ".join(messages))

    def _to_optional_int(self, value: Any) -> int | None:
        if value is None:
            return None
        try:
            return int(value)
        except (TypeError, ValueError):
            return None

    def _to_int_set(self, value: Any) -> set[int | None]:
        values: set[int | None] = set()
        for item in self._to_list(value):
            values.add(self._to_optional_int(item))
        return values

    def _to_list(self, value: Any) -> list[Any]:
        if isinstance(value, list):
            return value
        return []
