import sys
import re
import os
from datetime import datetime

def update_version(new_version):
    # Today's date
    today = datetime.now().strftime('%Y-%m-%d')
    
    # 1. Update core/version.py
    core_version_file = os.path.join('core', 'version.py')
    if os.path.exists(core_version_file):
        with open(core_version_file, 'r', encoding='utf-8') as f:
            content = f.read()
        content = re.sub(r'__version__ = "[^"]+"', f'__version__ = "{new_version}"', content)
        content = re.sub(r'__minimum_required_version__ = "[^"]+"', f'__minimum_required_version__ = "{new_version}"', content)
        content = re.sub(r'__build_date__ = "[^"]+"', f'__build_date__ = "{today}"', content)
        with open(core_version_file, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Updated {core_version_file}")

    # 2. Update root version.py
    root_version_file = 'version.py'
    if os.path.exists(root_version_file):
        with open(root_version_file, 'r', encoding='utf-8') as f:
            content = f.read()
        content = re.sub(r'__version__ = "[^"]+"', f'__version__ = "{new_version}"', content)
        content = re.sub(r'__minimum_required_version__ = "[^"]+"', f'__minimum_required_version__ = "{new_version}"', content)
        content = re.sub(r'__build_date__ = "[^"]+"', f'__build_date__ = "{today}"', content)
        with open(root_version_file, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Updated {root_version_file}")

    # 3. Update version.rc
    rc_file = 'version.rc'
    if os.path.exists(rc_file):
        # RC file uses comma separated version for FILEVERSION and PRODUCTVERSION (e.g. 1,0,0,3)
        # and dot separated for strings.
        # Ensure version parts are integers to strip leading zeros
        v_parts = new_version.split('.')
        while len(v_parts) < 4:
            v_parts.append('0')
        v_parts = [str(int(p)) for p in v_parts]
        comma_version = ', '.join(v_parts)
        
        with open(rc_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        content = re.sub(r'FILEVERSION [\d, ]+', f'FILEVERSION {comma_version}', content)
        content = re.sub(r'PRODUCTVERSION [\d, ]+', f'PRODUCTVERSION {comma_version}', content)
        content = re.sub(r'VALUE "FileVersion", "[^"]+"', f'VALUE "FileVersion", "{new_version}"', content)
        content = re.sub(r'VALUE "ProductVersion", "[^"]+"', f'VALUE "ProductVersion", "{new_version}"', content)
        
        with open(rc_file, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Updated {rc_file}")

    # 4. Update .spec file
    spec_file = 'Internet2000_win10.spec'
    if os.path.exists(spec_file):
        # Spec file uses tuple for version: (1, 0, 0, 3)
        v_parts = new_version.split('.')
        while len(v_parts) < 4:
            v_parts.append('0')
        v_parts = [str(int(p)) for p in v_parts]
        tuple_version = f"({', '.join(v_parts)})"
        
        with open(spec_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        content = re.sub(r'"version": \([\d, ]+\)', f'"version": {tuple_version}', content)
        content = re.sub(r'"product_version": \([\d, ]+\)', f'"product_version": {tuple_version}', content)
        
        with open(spec_file, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Updated {spec_file}")
    
    print(f"\nVersion successfully updated to {new_version} ({today}) across all files.")
    return True

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python update_version.py <new_version>")
        sys.exit(1)
    
    success = update_version(sys.argv[1])
    sys.exit(0 if success else 1)
