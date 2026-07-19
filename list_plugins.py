import os, sys
sys.stdout.reconfigure(encoding='utf-8')
base = 'f:/symple chat/python-chat-system/plugins'
for x in os.listdir(base):
    p = os.path.join(base, x)
    if os.path.isdir(p):
        print(x)
