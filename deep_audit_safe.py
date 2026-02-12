
import os
import django
import re

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from manager.models import Item

# Force UTF-8 for this script's processing
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

items = Item.objects.all().order_by('category', 'name')

missing_items = []
for item in items:
    name = item.name or ""
    clean_name = name.replace(" (Single)", "").replace(" (Double)", "")
    translation = po_data.get(clean_name)
    if not translation:
        missing_items.append(clean_name)

missing_cats = []
cats = set(item.category for item in items if item.category)
for cat in cats:
    if not po_data.get(cat):
        missing_cats.append(cat)

# Output only English names so view_file can read it without encoding issues
print("---MISSING_ITEMS_START---")
for m in sorted(set(missing_items)):
    print(m)
print("---MISSING_ITEMS_END---")

print("---MISSING_CATS_START---")
for m in sorted(set(missing_cats)):
    print(m)
print("---MISSING_CATS_END---")
