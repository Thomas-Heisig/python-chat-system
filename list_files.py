import os, sys
sys.stdout.reconfigure(encoding='utf-8')
base = 'f:/symple chat/python-chat-system'
for root, dirs, files in os.walk(base):
    # Skip .venv and __pycache__ directories
    dirs[:] = [d for d in dirs if d not in ('.venv', '__pycache__', 'dist', 'build', 'node_modules', '.git')]
    for f in files:
        if f.endswith('.py'):
            print(os.path.join(root, f))
