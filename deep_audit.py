
import os
import django
import re
import sys

# Ensure UTF-8 output even on Windows
if sys.stdout.encoding != 'utf-8':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

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

items = Item.objects.all().order_by('category', 'name')

print(f"{'Item Name':<40} | {'Clean Name':<40} | {'Status'}")
print("-" * 120)

missing_count = 0
results = []
for item in items:
    name = item.name or ""
    # Logic from translate_text filter:
    clean_name = name.replace(" (Single)", "").replace(" (Double)", "")
    
    translation = po_data.get(clean_name)
    
    if not translation:
        status = "MISSING"
        missing_count += 1
    else:
        status = f"OK ({translation})"
    
    line = f"{name:<40} | {clean_name:<40} | {status}"
    print(line)

print("-" * 120)
print(f"Total missing translations: {missing_count}")

cats = set(item.category for item in items if item.category)
print("\nCategories Check:")
for cat in sorted(cats):
    trans = po_data.get(cat)
    status = f"OK ({trans})" if trans else "MISSING"
    print(f"{cat:<40} | {status}")
