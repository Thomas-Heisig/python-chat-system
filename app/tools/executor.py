from __future__ import annotations

import json
import re
from typing import Any
import inspect

from app.tools.communication_contract import CommunicationContractValidator
from app.tools.execution_policy import PluginExecutionPolicy, PluginPolicyError
from app.tools.registry import PluginDefinition, PluginRegistry

_PLUGIN_CALL_PATTERN = re.compile(r"<plugin_call>\s*(?P<name>[^<]+?)\s*</plugin_call>", re.IGNORECASE | re.DOTALL)
_PLUGIN_INPUT_PATTERN = re.compile(r"<plugin_input>\s*(?P<input>\{.*\})\s*</plugin_input>", re.IGNORECASE | re.DOTALL)


class PluginExecutionError(RuntimeError):
	def __init__(self, code: str, message: str) -> None:
		super().__init__(message)
		self.code = code
		self.message = message


class PluginExecutor:
	def __init__(self, *, registry: PluginRegistry | None = None) -> None:
		self._registry = registry or PluginRegistry()
		self._communication_contract_validator = CommunicationContractValidator()
		self._execution_policy = PluginExecutionPolicy()

	def list_plugins(self) -> list[PluginDefinition]:
		return self._registry.list_plugins()

	def list_capabilities(self) -> list[dict[str, Any]]:
		return self._registry.list_capability_index()

	def search_plugins(self, query: str, *, limit: int = 3) -> list[dict[str, Any]]:
		return self._registry.search_capabilities(query, limit=limit)

	def describe_plugin(self, plugin_id: str) -> dict[str, Any] | None:
		return self._registry.get_plugin_manifest(plugin_id)

	def describe_function(self, plugin_id: str, function_name: str) -> dict[str, Any] | None:
		return self._registry.describe_function(plugin_id, function_name)

	def resolve_execution_target(
		self,
		plugin_id: str,
		input_data: dict[str, Any],
		*,
		function_name: str | None = None,
	) -> tuple[PluginDefinition, dict[str, Any], dict[str, Any], str]:
		loaded = self._registry.get_plugin(plugin_id)
		if loaded is None:
			raise PluginExecutionError("plugin_not_found", f"Unknown plugin: {plugin_id}")

		payload = dict(input_data)
		if function_name is None:
			function_meta = self._resolve_policy_function_meta(loaded, payload)
			resolved_function_name = str(function_meta.get("name") or "execute").strip() or "execute"
			return loaded.definition, function_meta, payload, resolved_function_name

		normalized_function = str(function_name).strip()
		if not normalized_function:
			raise PluginExecutionError("plugin_function_invalid", "Function name is empty")

		normalized_lower = normalized_function.lower()
		if normalized_lower == "execute":
			function_meta = self._resolve_policy_function_meta(loaded, payload)
			resolved_function_name = str(function_meta.get("name") or "execute").strip() or "execute"
			return loaded.definition, function_meta, payload, resolved_function_name

		function_meta = self.describe_function(plugin_id, normalized_function)
		if function_meta is None:
			raise PluginExecutionError(
				"plugin_function_not_found",
				f"Unknown function '{normalized_function}' for plugin: {plugin_id}",
			)

		current_action = payload.get("action")
		if current_action is None:
			payload["action"] = normalized_function
		elif isinstance(current_action, str) and current_action.strip().lower() == normalized_lower:
			pass
		else:
			raise PluginExecutionError(
				"plugin_function_action_conflict",
				"Function name and payload action differ.",
			)

		return loaded.definition, function_meta, payload, normalized_function

	async def execute(
		self,
		plugin_id: str,
		input_data: dict[str, Any],
		plugin_settings: dict[str, Any] | None = None,
		execution_context: dict[str, Any] | None = None,
	) -> dict[str, Any]:
		definition, function_meta, payload, _resolved_function_name = self.resolve_execution_target(
			plugin_id,
			input_data,
		)
		try:
			self._execution_policy.validate(
				definition=definition,
				function_meta=function_meta,
				input_data=payload,
				plugin_settings=plugin_settings,
				execution_context=execution_context,
			)
		except PluginPolicyError as exc:
			raise PluginExecutionError(exc.code, exc.message) from exc

		loaded = self._registry.get_plugin(plugin_id)
		if loaded is None:
			raise PluginExecutionError("plugin_not_found", f"Unknown plugin: {plugin_id}")
		return await self._execute_loaded(loaded, payload, plugin_settings)

	def _resolve_policy_function_meta(self, loaded: Any, input_data: dict[str, Any]) -> dict[str, Any]:
		plugin_id = loaded.definition.plugin_id
		action_name = str(input_data.get("action") or "").strip()
		if action_name:
			candidate = self.describe_function(plugin_id, action_name)
			if isinstance(candidate, dict):
				return candidate

		properties = loaded.definition.input_schema.get("properties")
		if isinstance(properties, dict):
			action_schema = properties.get("action")
			if isinstance(action_schema, dict):
				enum_values = action_schema.get("enum")
				if isinstance(enum_values, list) and enum_values:
					default_action = str(enum_values[0]).strip()
					if default_action:
						candidate = self.describe_function(plugin_id, default_action)
						if isinstance(candidate, dict):
							return candidate

		candidate = self.describe_function(plugin_id, "execute")
		if isinstance(candidate, dict):
			return candidate

		if loaded.definition.functions:
			first = loaded.definition.functions[0]
			if isinstance(first, dict):
				return first

		return {
			"name": "execute",
			"read_only": True,
			"side_effect": "none",
			"requires_confirmation": False,
			"idempotent": True,
			"supports_dry_run": True,
			"required_permissions": [],
			"input_schema": loaded.definition.input_schema,
		}

	async def _execute_loaded(
		self,
		loaded: Any,
		input_data: dict[str, Any],
		plugin_settings: dict[str, Any] | None,
	) -> dict[str, Any]:

		instance = self._create_plugin_instance(loaded.plugin_class, plugin_settings)
		input_errors = self._communication_contract_validator.validate_input(loaded.definition.plugin_id, input_data)
		if input_errors:
			raise PluginExecutionError(
				"plugin_contract_invalid_input",
				"; ".join(input_errors),
			)

		execute = getattr(instance, "execute", None)
		if not callable(execute):
			raise PluginExecutionError("plugin_not_callable", f"Plugin has no callable execute: {loaded.definition.plugin_id}")

		result = await execute(input_data)
		if isinstance(result, dict):
			output_errors = self._communication_contract_validator.validate_output(loaded.definition.plugin_id, result)
			if output_errors:
				raise PluginExecutionError(
					"plugin_contract_invalid_output",
					"; ".join(output_errors),
				)
			return result
		return {"result": result}

	async def execute_function(
		self,
		plugin_id: str,
		function_name: str,
		input_data: dict[str, Any],
		plugin_settings: dict[str, Any] | None = None,
		execution_context: dict[str, Any] | None = None,
	) -> dict[str, Any]:
		definition, function_meta, payload, resolved_function_name = self.resolve_execution_target(
			plugin_id,
			input_data,
			function_name=function_name,
		)
		if resolved_function_name.lower() == "execute":
			return await self.execute(plugin_id, payload, plugin_settings, execution_context=execution_context)

		policy_context = dict(execution_context or {})
		policy_context.setdefault("function_name", resolved_function_name)
		try:
			self._execution_policy.validate(
				definition=definition,
				function_meta=function_meta,
				input_data=payload,
				plugin_settings=plugin_settings,
				execution_context=policy_context,
			)
		except PluginPolicyError as exc:
			raise PluginExecutionError(exc.code, exc.message) from exc

		loaded = self._registry.get_plugin(plugin_id)
		if loaded is None:
			raise PluginExecutionError("plugin_not_found", f"Unknown plugin: {plugin_id}")
		return await self._execute_loaded(loaded, payload, plugin_settings)

	async def execute_from_markup(self, assistant_output: str) -> dict[str, Any]:
		plugin_id, plugin_input = self.parse_markup(assistant_output)
		plugin_result = await self.execute(plugin_id, plugin_input)
		return {
			"plugin_id": plugin_id,
			"plugin_input": plugin_input,
			"plugin_response": plugin_result,
			"plugin_response_markup": f"<plugin_response>{json.dumps(plugin_result, ensure_ascii=False)}</plugin_response>",
		}

	def parse_markup(self, assistant_output: str) -> tuple[str, dict[str, Any]]:
		call_match = _PLUGIN_CALL_PATTERN.search(assistant_output)
		if call_match is None:
			raise PluginExecutionError("plugin_call_missing", "No <plugin_call>...</plugin_call> found")

		plugin_id = call_match.group("name").strip()
		if not plugin_id:
			raise PluginExecutionError("plugin_call_invalid", "Plugin id in <plugin_call> is empty")

		input_match = _PLUGIN_INPUT_PATTERN.search(assistant_output)
		if input_match is None:
			raise PluginExecutionError("plugin_input_missing", "No <plugin_input>{...}</plugin_input> found")

		input_raw = input_match.group("input").strip()
		try:
			parsed = json.loads(input_raw)
		except Exception as exc:
			raise PluginExecutionError("plugin_input_invalid_json", f"Invalid plugin_input JSON: {exc}") from exc

		if not isinstance(parsed, dict):
			raise PluginExecutionError("plugin_input_not_object", "plugin_input must be a JSON object")

		return plugin_id, parsed

	def _create_plugin_instance(
		self,
		plugin_class: type[Any],
		plugin_settings: dict[str, Any] | None,
	) -> Any:
		if plugin_settings is None:
			return plugin_class()

		if not isinstance(plugin_settings, dict):
			return plugin_class()

		try:
			signature = inspect.signature(plugin_class)
			if "settings" in signature.parameters:
				return plugin_class(settings=plugin_settings)
		except (TypeError, ValueError):
			pass

		instance = plugin_class()
		setter = getattr(instance, "set_settings", None)
		if callable(setter):
			setter(plugin_settings)
		return instance

