import sys, os
sys.stdout.reconfigure(encoding='utf-8')
fpath = 'f:/symple chat/python-chat-system/plugins/jtl_suite/plugin.py'

# Try to compile the source
with open(fpath, 'r', encoding='utf-8') as f:
    source = f.read()

try:
    compile(source, fpath, 'exec')
    print('COMPILE OK')
except SyntaxError as e:
    print(f'SYNTAX ERROR: {e}')

# Also check for datetime usage
if 'datetime.now' in source and 'from datetime' not in source:
    print('ISSUE: datetime.now() used without from datetime import')
    
# Check for all imports
for line in source.split('\n'):
    if line.strip().startswith('import ') or line.strip().startswith('from '):
        print(f'IMPORT: {line.strip()}')
        
# Check for class structure
import re
classes = re.findall(r'^class\s+\w+', source, re.MULTILINE)
print(f'Classes found: {classes}')
