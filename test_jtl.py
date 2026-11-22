import pytest

from app.tools.registry import PluginRegistry
from plugins.jtl_suite.plugin import PLUGIN_META, JTLSuitePlugin


def test_jtl_plugin_registration():
    plugin = JTLSuitePlugin()

    assert PLUGIN_META["id"] == "jtl_suite"
    assert plugin.name == "jtl_suite"


def test_jtl_plugin_is_discoverable_by_the_runtime_registry():
    plugin = PluginRegistry().get_plugin("jtl_suite")

    assert plugin is not None
    assert plugin.definition.plugin_id == "jtl_suite"


@pytest.mark.asyncio
async def test_jtl_product_request_requires_configured_url():
    result = await JTLSuitePlugin().execute({"action": "list_products", "limit": 5})

    assert result["success"] is False
    assert "API Base URL" in result["error"]


@pytest.mark.asyncio
async def test_jtl_settings_are_passed_to_execute():
    result = await JTLSuitePlugin().execute(
        {"action": "settings.resolved"},
        plugin_settings={"request_timeout_seconds": 30},
    )

    assert result["success"] is True
    assert result["data"]["request_timeout_seconds"] == 30
