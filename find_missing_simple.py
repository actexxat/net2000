
import re

po_path = r'd:\net2000\locale\ar\LC_MESSAGES\django.po'

def find_missing():
    with open(po_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Simple regex to find msgid with empty msgstr
    matches = re.findall(r'msgid "(.*?)"\nmsgstr ""', content)
    
    print(f"Found {len(matches)} untranslated strings:")
    for m in sorted(list(set(matches))):
        print(f"- {m}")

if __name__ == "__main__":
    find_missing()
