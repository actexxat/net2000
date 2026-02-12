
import os
import django
import re
import sys

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from manager.models import Item

def get_po_entries(path):
    if not os.path.exists(path):
        return {}
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    entries = re.split(r'\n\n+', content)
    translated_map = {}
    for entry in entries:
        msgid_match = re.search(r'^msgid "(.*)"', entry, re.M)
        msgstr_match = re.search(r'^msgstr "(.*)"', entry, re.M)
        if msgid_match and msgstr_match:
            mid = msgid_match.group(1)
            mstr = msgstr_match.group(1)
            translated_map[mid] = mstr
    return translated_map

po_path = r'd:\net2000\locale\ar\LC_MESSAGES\django.po'
po_data = get_po_entries(po_path)

items = Item.objects.all()
missing = []

for item in items:
    name = item.name or ""
    clean_name = name.replace(" (Single)", "").replace(" (Double)", "")
    if clean_name not in po_data or not po_data[clean_name]:
        missing.append(clean_name)

cats = set(item.category for item in items if item.category)
for cat in cats:
    if cat not in po_data or not po_data[cat]:
        missing.append(cat)

missing = sorted(list(set(missing)))
for m in missing:
    print(f"MISSING: {m}")
