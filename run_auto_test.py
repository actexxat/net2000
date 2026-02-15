import os
import sys
from pathlib import Path

# Add the distribution internal path to sys.path to use its logic
dist_path = Path(r"d:\net2000\dist\Internet2000_Alpha_One\_internal")
sys.path.insert(0, str(dist_path))

from updater import UpdateChecker

def run_automated_test():
    print("="*50)
    print("AUTOMATED UPDATE TEST START")
    print("="*50)
    
    checker = UpdateChecker()
    print(f"1. Checking for updates on GitHub (Current: {checker.current_version})...")
    result = checker.check_for_updates()
    
    if not result['available']:
        print(f"❌ FAILED: No update available. Found: {result['latest_version']}")
        return
    
    print(f"✅ SUCCESS: New version {result['latest_version']} found.")
    print(f"2. Downloading update from {result['download_url']}...")
    
    def progress(p):
        print(f"   Download Progress: {p}%")
        
    zip_path = checker.download_update(result['download_url'], progress)
    if not zip_path:
        print("❌ FAILED: Download failed.")
        return
        
    print(f"✅ SUCCESS: Update downloaded to {zip_path}")
    print("3. Preparing installation (Extracting and creating script)...")
    
    # We need to manually set app_dir because we're running from this script
    app_dir = Path(r"d:\net2000\dist\Internet2000_Alpha_One")
    update_script = checker.install_update(zip_path)
    
    if not update_script:
        print("❌ FAILED: Preparation failed.")
        return
        
    print(f"✅ SUCCESS: Update script ready at {update_script}")
    print("4. VERIFICATION: Checking if replacement files are ready...")
    
    temp_dir = app_dir / "_update_temp" / "new_version"
    if temp_dir.exists():
        print(f"✅ SUCCESS: Extracted files found in {temp_dir}")
    else:
        print("❌ FAILED: Extracted files not found.")
        return

    print("="*50)
    print("TEST COMPLETED SUCCESSFULLY!")
    print("The system is ready to replace: dist\\Internet2000_Alpha_One")
    print("="*50)
    
if __name__ == "__main__":
    run_automated_test()
