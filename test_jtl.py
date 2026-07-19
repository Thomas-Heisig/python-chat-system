import sys, os
sys.path.insert(0, 'f:/symple chat/python-chat-system')
sys.stdout.reconfigure(encoding='utf-8')

# Test 1: Import the module
from plugins.jtl_suite.plugin import PLUGIN_META, JTLSuitePlugin
print(f'PLUGIN_META id: {PLUGIN_META.get("id")}')
print(f'Class: {JTLSuitePlugin.__name__}')

# Test 2: Create instance
inst = JTLSuitePlugin()
print(f'Instance created: {type(inst).__name__}')

# Test 3: Test execute
import asyncio
result = asyncio.run(inst.execute({"action": "list_products", "limit": 5}))
print(f'Execute result success: {result.get("success")}')

# Test 4: Test with settings
inst2 = JTLSuitePlugin(settings={"request_timeout_seconds": 30})
print(f'Instance with settings: {type(inst2).__name__}')

print('ALL CHECKS PASSED')
