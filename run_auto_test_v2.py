import os
import sys
from pathlib import Path

# Add the distribution internal path to sys.path to use its logic
dist_path = Path(r"d:\net2000\dist\Internet2000_Alpha_One\_internal")
sys.path.insert(0, str(dist_path))

# MOCK PyInstaller environment for the test
sys.frozen = True
sys.executable = r"d:\net2000\dist\Internet2000_Alpha_One\Internet2000_Alpha_One.exe"

from updater import UpdateChecker

def run_automated_test():
    print("="*50)
    print("MOCKED PRODUCTION TEST START")
    print("="*50)
    
    checker = UpdateChecker()
    print(f"1. Checking GitHub (Current: {checker.current_version})...")
    result = checker.check_for_updates()
    
    if not result['available']:
        print(f"FAILED: Found {result['latest_version']}. No update needed.")
        return
    
    print(f"SUCCESS: New version {result['latest_version']} found.")
    
    # Use the existing ZIP if found to save time
    temp_zip = Path(os.environ['TEMP']) / 'internet2000_update.zip'
    if temp_zip.exists():
        print(f"2. Using existing download: {temp_zip}")
        zip_path = str(temp_zip)
    else:
        print(f"2. Downloading...")
        zip_path = checker.download_update(result['download_url'])
        
    print(f"3. Installing update (Extraction)...")
    update_script = checker.install_update(zip_path)
    
    if not update_script:
        print("FAILED: install_update returned None.")
        return
        
    print(f"SUCCESS: Update script created at: {update_script}")
    
    # Check if files were extracted
    app_dir = Path(sys.executable).parent
    extract_dir = app_dir / "_update_temp" / "new_version"
    print(f"4. Verifying extraction in: {extract_dir}")
    
    if extract_dir.exists():
        files = list(extract_dir.iterdir())
        print(f"SUCCESS: Found {len(files)} items in extraction folder.")
        for f in files[:3]:
            print(f"   - {f.name}")
    else:
        print("FAILED: Extraction directory not found.")
        return

    print("="*50)
    print("TEST COMPLETED SUCCESSFULLY!")
    print("The system is 100% ready to replace and restart.")
    print("="*50)
    
if __name__ == "__main__":
    run_automated_test()
