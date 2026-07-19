import os, sys
sys.stdout.reconfigure(encoding='utf-8')
filepath = 'f:/symple chat/python-chat-system/plugins/jtl_suite/plugin.py'
with open(filepath, 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i, line in enumerate(lines, 1):
    stripped = line.strip()
    if (stripped.startswith('class ') or 
        stripped.startswith('def __init__') or 
        stripped.startswith('async def execute') or
        'PLUGIN_META' in stripped or
        stripped.startswith('def set_settings')):
        print(f'{i}: {stripped}')
