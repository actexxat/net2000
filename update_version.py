
import re
import sys
import datetime

def update_version(version_file_path, new_version):
    """
    Updates the __version__ and __build_date__ in the specified file using regex,
    preserving all other content.
    """
    try:
        with open(version_file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Update version
        # Look for __version__ = "..." or '__version__ = '...''
        version_pattern = r'__version__\s*=\s*["\']([^"\']+)["\']'
        if re.search(version_pattern, content):
            content = re.sub(version_pattern, f'__version__ = "{new_version}"', content)
        else:
            print(f"Warning: Could not find __version__ variable in {version_file_path}")
            # Append if missing? No, better warn.

        # Update build date
        date_pattern = r'__build_date__\s*=\s*["\']([^"\']+)["\']'
        today = datetime.datetime.now().strftime('%Y-%m-%d')
        if re.search(date_pattern, content):
            content = re.sub(date_pattern, f'__build_date__ = "{today}"', content)
        
        with open(version_file_path, 'w', encoding='utf-8') as f:
            f.write(content)
            
        print(f"Successfully updated version to {new_version} and date to {today}")
        return True
    except Exception as e:
        print(f"Error updating version file: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python update_version.py <new_version>")
        sys.exit(1)
        
    new_version = sys.argv[1]
    success = update_version('version.py', new_version)
    if not success:
        sys.exit(1)
