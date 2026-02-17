import sys
import re
import os
from datetime import datetime

def update_version(new_version):
    version_file = os.path.join('core', 'version.py')
    if not os.path.exists(version_file):
        print(f"Error: {version_file} not found!")
        return False

    with open(version_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # Update version string
    content = re.sub(r'__version__ = "[^"]+"', f'__version__ = "{new_version}"', content)
    
    # Update build date
    today = datetime.now().strftime('%Y-%m-%d')
    content = re.sub(r'__build_date__ = "[^"]+"', f'__build_date__ = "{today}"', content)

    with open(version_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"Version updated to {new_version} ({today})")
    return True

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python update_version.py <new_version>")
        sys.exit(1)
    
    success = update_version(sys.argv[1])
    sys.exit(0 if success else 1)
