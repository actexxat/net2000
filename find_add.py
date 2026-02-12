
import re
content = open(r'locale\ar\LC_MESSAGES\django.po', encoding='utf-8').read()
matches = re.finditer(r'^msgid "(.*Add.*)"\nmsgstr "(.*)"', content, re.M)
for m in matches:
    print(f"ID: {m.group(1)} | STR: {m.group(2)}")
