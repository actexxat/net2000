
import os
import re

def search():
    for root, dirs, files in os.walk('.'):
        for file in files:
            if file.endswith(('.html', '.py', '.po')):
                path = os.path.join(root, file)
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        if 'Add item' in content or 'Add Item' in content:
                            print(f"Found in {path}")
                            # Print matching lines
                            for i, line in enumerate(content.splitlines()):
                                if 'Add item' in line or 'Add Item' in line:
                                    print(f"  Line {i+1}: {line.strip()}")
                except:
                    pass

search()
