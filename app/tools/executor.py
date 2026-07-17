from __future__ import annotations

import json
import re
from typing import Any
import inspect

from app.tools.communication_contract import CommunicationContractValidator
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

	def list_plugins(self) -> list[PluginDefinition]:
		return self._registry.list_plugins()

	async def execute(
		self,
		plugin_id: str,
		input_data: dict[str, Any],
		plugin_settings: dict[str, Any] | None = None,
	) -> dict[str, Any]:
		loaded = self._registry.get_plugin(plugin_id)
		if loaded is None:
			raise PluginExecutionError("plugin_not_found", f"Unknown plugin: {plugin_id}")

		instance = self._create_plugin_instance(loaded.plugin_class, plugin_settings)
		input_errors = self._communication_contract_validator.validate_input(plugin_id, input_data)
		if input_errors:
			raise PluginExecutionError(
				"plugin_contract_invalid_input",
				"; ".join(input_errors),
			)

		execute = getattr(instance, "execute", None)
		if not callable(execute):
			raise PluginExecutionError("plugin_not_callable", f"Plugin has no callable execute: {plugin_id}")

		result = await execute(input_data)
		if isinstance(result, dict):
			output_errors = self._communication_contract_validator.validate_output(plugin_id, result)
			if output_errors:
				raise PluginExecutionError(
					"plugin_contract_invalid_output",
					"; ".join(output_errors),
				)
			return result
		return {"result": result}

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

