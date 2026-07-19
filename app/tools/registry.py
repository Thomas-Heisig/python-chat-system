from __future__ import annotations

from dataclasses import dataclass
import importlib.util
import inspect
import re
from pathlib import Path
from threading import Lock
from typing import Any, Callable, cast


@dataclass(frozen=True)
class PluginDefinition:
	plugin_id: str
	name: str
	description: str
	category: str
	status: str
	api_key_required: bool
	intent_pattern: str
	summary: str
	capabilities: list[str]
	usage_rules: list[str]
	examples: list[dict[str, Any]]
	functions: list[dict[str, Any]]
	settings_fields: list[dict[str, Any]]
	plugin_frontend: dict[str, Any]
	input_schema: dict[str, Any]
	output_schema: dict[str, Any]


@dataclass(frozen=True)
class LoadedPlugin:
	definition: PluginDefinition
	plugin_class: type[Any]


class PluginRegistry:
	"""Discovers plugin modules from the top-level plugins folder and exposes runtime metadata."""

	def __init__(self, *, plugins_root: Path | None = None) -> None:
		self._plugins_root = plugins_root or Path(__file__).resolve().parents[2] / "plugins"
		self._lock = Lock()
		self._loaded = False
		self._plugins_by_id: dict[str, LoadedPlugin] = {}

	def _ensure_loaded(self) -> None:
		if self._loaded:
			return
		with self._lock:
			if self._loaded:
				return
			self._plugins_by_id = self._discover_plugins()
			self._loaded = True

	def reload(self) -> None:
		with self._lock:
			self._plugins_by_id = self._discover_plugins()
			self._loaded = True

	def list_plugins(self) -> list[PluginDefinition]:
		self._ensure_loaded()
		definitions = [item.definition for item in self._plugins_by_id.values()]
		return sorted(definitions, key=lambda item: item.plugin_id)

	def get_plugin(self, plugin_id: str) -> LoadedPlugin | None:
		self._ensure_loaded()
		return self._plugins_by_id.get(plugin_id)

	def list_capability_index(self) -> list[dict[str, Any]]:
		self._ensure_loaded()
		items: list[dict[str, Any]] = []
		for loaded in self._plugins_by_id.values():
			definition = loaded.definition
			if definition.capabilities:
				for capability in definition.capabilities:
					items.append(
						{
							"capability": capability,
							"plugin_id": definition.plugin_id,
							"summary": definition.summary,
						}
					)
			else:
				items.append(
					{
						"capability": f"plugin.{definition.plugin_id}",
						"plugin_id": definition.plugin_id,
						"summary": definition.summary,
					}
				)
		return sorted(items, key=lambda item: (str(item["capability"]), str(item["plugin_id"])))

	def search_capabilities(self, query: str, *, limit: int = 3) -> list[dict[str, Any]]:
		self._ensure_loaded()
		normalized_limit = max(1, min(3, int(limit)))
		query_tokens = self._tokenize(query)
		scored: list[dict[str, Any]] = []
		for loaded in self._plugins_by_id.values():
			definition = loaded.definition
			capability_tokens = self._tokenize(" ".join(definition.capabilities))
			function_tokens = self._tokenize(
				" ".join(
					f"{str(item.get('name', ''))} {str(item.get('description', ''))}"
					for item in definition.functions
				)
			)
			general_tokens = self._tokenize(
				" ".join(
					[
						definition.plugin_id,
						definition.name,
						definition.summary,
						definition.description,
						" ".join(definition.usage_rules),
					]
				)
			)
			plugin_name_tokens = self._tokenize(f"{definition.plugin_id} {definition.name}")
			if not query_tokens:
				score = 0.0
			else:
				capability_score = len(query_tokens.intersection(capability_tokens)) / max(1, len(query_tokens))
				function_score = len(query_tokens.intersection(function_tokens)) / max(1, len(query_tokens))
				general_score = len(query_tokens.intersection(general_tokens)) / max(1, len(query_tokens))
				score = (0.5 * capability_score) + (0.35 * function_score) + (0.15 * general_score)

				name_only_match = (
					len(query_tokens.intersection(plugin_name_tokens)) > 0
					and len(query_tokens.intersection(capability_tokens.union(function_tokens))) == 0
				)
				if name_only_match:
					score = min(score, 0.54)
			if score <= 0.0:
				continue
			decision = "no_auto_selection"
			auto_select = False
			if score >= 0.80:
				decision = "direct_manifest"
				auto_select = True
			elif score >= 0.55:
				decision = "model_review"
			reason = self._build_reason(query_tokens, definition)
			scored.append(
				{
					"plugin_id": definition.plugin_id,
					"score": round(score, 4),
					"decision": decision,
					"auto_select": auto_select,
					"reason": reason,
					"summary": definition.summary,
					"capabilities": list(definition.capabilities),
				}
			)

		scored.sort(key=lambda item: (float(item["score"]), str(item["plugin_id"])), reverse=True)
		return scored[:normalized_limit]

	def get_plugin_manifest(self, plugin_id: str) -> dict[str, Any] | None:
		loaded = self.get_plugin(plugin_id)
		if loaded is None:
			return None
		definition = loaded.definition
		return {
			"id": definition.plugin_id,
			"name": definition.name,
			"summary": definition.summary,
			"description": definition.description,
			"category": definition.category,
			"status": definition.status,
			"api_key_required": definition.api_key_required,
			"intent_pattern": definition.intent_pattern,
			"capabilities": list(definition.capabilities),
			"usage_rules": list(definition.usage_rules),
			"examples": list(definition.examples),
			"functions": list(definition.functions),
			"settings_fields": list(definition.settings_fields),
			"input_schema": dict(definition.input_schema),
			"output_schema": dict(definition.output_schema),
		}

	def describe_function(self, plugin_id: str, function_name: str) -> dict[str, Any] | None:
		manifest = self.get_plugin_manifest(plugin_id)
		if manifest is None:
			return None
		functions = manifest.get("functions")
		if not isinstance(functions, list):
			return None
		normalized = str(function_name).strip().lower()
		for item in functions:
			if not isinstance(item, dict):
				continue
			candidate = str(item.get("name", "")).strip().lower()
			if candidate == normalized:
				return cast(dict[str, Any], item)
		return None

	def _discover_plugins(self) -> dict[str, LoadedPlugin]:
		discovered: dict[str, LoadedPlugin] = {}
		if not self._plugins_root.exists() or not self._plugins_root.is_dir():
			return discovered

		for plugin_dir in sorted(path for path in self._plugins_root.iterdir() if path.is_dir()):
			plugin_file = plugin_dir / "plugin.py"
			if not plugin_file.exists():
				continue

			loaded = self._load_plugin_from_file(plugin_file)
			if loaded is None:
				continue

			plugin_id = loaded.definition.plugin_id.strip()
			if not plugin_id:
				continue
			discovered[plugin_id] = loaded

		return discovered

	def _load_plugin_from_file(self, plugin_file: Path) -> LoadedPlugin | None:
		module_name = f"runtime_plugins_{plugin_file.parent.name}"
		spec = importlib.util.spec_from_file_location(module_name, str(plugin_file))
		if spec is None or spec.loader is None:
			return None

		module = importlib.util.module_from_spec(spec)
		spec.loader.exec_module(module)

		metadata_raw = getattr(module, "PLUGIN_META", None)
		if not isinstance(metadata_raw, dict):
			return None
		metadata = cast(dict[str, Any], metadata_raw)

		plugin_class = self._extract_plugin_class(module)
		if plugin_class is None:
			return None

		input_schema_raw = getattr(plugin_class, "input_schema", {})
		output_schema_raw = getattr(plugin_class, "output_schema", {})
		input_schema = self._normalize_schema(input_schema_raw)
		output_schema = self._normalize_schema(output_schema_raw)
		summary = str(metadata.get("summary") or metadata.get("description") or "")
		capabilities = self._normalize_capabilities(metadata.get("capabilities"))
		if not capabilities:
			capabilities = self._infer_capabilities(
				plugin_id=str(metadata.get("id") or plugin_file.parent.name),
				input_schema=input_schema,
			)
		functions = self._normalize_functions(
			raw_functions=metadata.get("functions"),
			input_schema=input_schema,
			output_schema=output_schema,
			description=str(metadata.get("description") or ""),
		)
		definition = PluginDefinition(
			plugin_id=str(metadata.get("id") or plugin_file.parent.name),
			name=str(metadata.get("name") or plugin_file.parent.name),
			description=str(metadata.get("description") or ""),
			category=str(metadata.get("category") or ""),
			status=str(metadata.get("status") or "implemented"),
			api_key_required=bool(metadata.get("apiKeyRequired", False)),
			intent_pattern=str(metadata.get("intentPattern") or ""),
			summary=summary,
			capabilities=capabilities,
			usage_rules=self._normalize_string_list(metadata.get("usage_rules")),
			examples=self._normalize_examples(metadata.get("examples")),
			functions=functions,
			settings_fields=self._normalize_settings_fields(metadata.get("settingsFields")),
			plugin_frontend=self._normalize_schema(metadata.get("pluginFrontend")),
			input_schema=input_schema,
			output_schema=output_schema,
		)
		return LoadedPlugin(definition=definition, plugin_class=plugin_class)

	def _extract_plugin_class(self, module: Any) -> type[Any] | None:
		candidates: list[type[Any]] = []
		for attr_name in dir(module):
			attr = getattr(module, attr_name, None)
			if not inspect.isclass(attr):
				continue
			if not attr_name.endswith("Plugin"):
				continue
			execute_candidate = getattr(attr, "execute", None)
			if callable(execute_candidate):
				candidates.append(cast(type[Any], attr))

		if not candidates:
			return None
		candidates.sort(key=lambda item: item.__name__)
		return candidates[0]

	def _normalize_schema(self, value: Any) -> dict[str, Any]:
		if isinstance(value, dict):
			return cast(dict[str, Any], value)
		return {}

	def _normalize_settings_fields(self, value: Any) -> list[dict[str, Any]]:
		if not isinstance(value, list):
			return []

		fields: list[dict[str, Any]] = []
		for item in value:
			if isinstance(item, dict):
				fields.append(cast(dict[str, Any], item))
		return fields

	def _normalize_string_list(self, value: Any) -> list[str]:
		if not isinstance(value, list):
			return []
		items: list[str] = []
		for item in value:
			if isinstance(item, str):
				normalized = item.strip()
				if normalized:
					items.append(normalized)
		return items

	def _normalize_capabilities(self, value: Any) -> list[str]:
		if not isinstance(value, list):
			return []
		capabilities: list[str] = []
		for item in value:
			if isinstance(item, str):
				normalized = item.strip()
				if normalized:
					capabilities.append(normalized)
		return sorted(set(capabilities))

	def _normalize_examples(self, value: Any) -> list[dict[str, Any]]:
		if not isinstance(value, list):
			return []
		examples: list[dict[str, Any]] = []
		for item in value:
			if isinstance(item, dict):
				examples.append(cast(dict[str, Any], item))
		return examples

	def _normalize_functions(
		self,
		*,
		raw_functions: Any,
		input_schema: dict[str, Any],
		output_schema: dict[str, Any],
		description: str,
	) -> list[dict[str, Any]]:
		functions: list[dict[str, Any]] = []
		if isinstance(raw_functions, list):
			for item in raw_functions:
				if isinstance(item, dict):
					functions.append(self._normalize_function_entry(cast(dict[str, Any], item), input_schema, output_schema, description))

		if functions:
			return functions

		actions: list[str] = []
		properties = input_schema.get("properties")
		if isinstance(properties, dict):
			action_schema = properties.get("action")
			if isinstance(action_schema, dict):
				enum_values = action_schema.get("enum")
				if isinstance(enum_values, list):
					for value in enum_values:
						if isinstance(value, str) and value.strip():
							actions.append(value.strip())

		functions.append(
			self._normalize_function_entry(
				{
					"name": "execute",
					"description": description or "Execute plugin action.",
					"read_only": False,
					"side_effect": "unknown",
					"requires_confirmation": False,
					"idempotent": False,
					"supports_dry_run": bool(actions),
					"actions": sorted(set(actions)),
				},
				input_schema,
				output_schema,
				description,
			)
		)
		for action in sorted(set(actions)):
			functions.append(
				self._normalize_function_entry(
					{
						"name": action,
						"description": f"Execute plugin action '{action}'.",
						"read_only": False,
						"side_effect": "unknown",
						"requires_confirmation": False,
						"idempotent": False,
						"supports_dry_run": True,
					},
					input_schema,
					output_schema,
					description,
				)
			)
		return functions

	def _normalize_function_entry(
		self,
		item: dict[str, Any],
		input_schema: dict[str, Any],
		output_schema: dict[str, Any],
		description: str,
	) -> dict[str, Any]:
		function_name = str(item.get("name") or "execute").strip() or "execute"
		function_description = str(item.get("description") or description or "Execute plugin action.").strip()
		required_permissions = self._normalize_string_list(item.get("required_permissions"))
		normalized: dict[str, Any] = {
			"name": function_name,
			"description": function_description,
			"input_schema": cast(dict[str, Any], item.get("input_schema")) if isinstance(item.get("input_schema"), dict) else input_schema,
			"output_schema": cast(dict[str, Any], item.get("output_schema")) if isinstance(item.get("output_schema"), dict) else output_schema,
			"read_only": bool(item.get("read_only", False)),
			"side_effect": str(item.get("side_effect") or "unknown"),
			"requires_confirmation": bool(item.get("requires_confirmation", False)),
			"required_permissions": required_permissions,
			"idempotent": bool(item.get("idempotent", False)),
			"supports_dry_run": bool(item.get("supports_dry_run", False)),
		}
		actions = item.get("actions")
		if isinstance(actions, list):
			normalized["actions"] = [str(action).strip() for action in actions if str(action).strip()]
		return normalized

	def _infer_capabilities(self, *, plugin_id: str, input_schema: dict[str, Any]) -> list[str]:
		capabilities: set[str] = {f"plugin.{plugin_id}"}
		properties = input_schema.get("properties")
		if isinstance(properties, dict):
			action_schema = properties.get("action")
			if isinstance(action_schema, dict):
				enum_values = action_schema.get("enum")
				if isinstance(enum_values, list):
					for value in enum_values:
						if not isinstance(value, str):
							continue
						normalized = value.strip().lower()
						if normalized:
							capabilities.add(f"{plugin_id}.action.{normalized}")
		return sorted(capabilities)

	def _tokenize(self, text: str) -> set[str]:
		parts = re.split(r"[^a-z0-9_]+", text.lower())
		return {part for part in parts if len(part) >= 2}

	def _build_search_haystack(self, definition: PluginDefinition) -> str:
		fragments: list[str] = [
			definition.plugin_id,
			definition.name,
			definition.summary,
			definition.description,
			definition.category,
			" ".join(definition.capabilities),
			" ".join(definition.usage_rules),
		]
		for function in definition.functions:
			fragments.append(str(function.get("name", "")))
			fragments.append(str(function.get("description", "")))
		return " ".join(fragments)

	def _build_reason(self, query_tokens: set[str], definition: PluginDefinition) -> str:
		reason_tokens = query_tokens.intersection(self._tokenize(self._build_search_haystack(definition)))
		if reason_tokens:
			joined = ", ".join(sorted(reason_tokens)[:4])
			return f"Matched terms: {joined}"
		return f"Matched plugin metadata for {definition.plugin_id}"

