
import re
content = open(r'locale\ar\LC_MESSAGES\django.po', encoding='utf-8').read()
for m in re.finditer(r'^msgid "(Pay|Add).*"\nmsgstr "(.*)"', content, re.M):
    print(f"ID: {m.group(0).splitlines()[0]} | STR: {m.group(2)}")
