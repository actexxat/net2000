"""
Auto-updater module for Internet 2000.
Checks GitHub releases for updates and downloads/installs them.
"""

import os
import sys
import json
import zipfile
import shutil
import tempfile
import subprocess
from pathlib import Path
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError
import ssl

# Import version info
try:
    from version import __version__, __github_repo__, compare_versions
except ImportError:
    __version__ = "1.0.0"
    __github_repo__ = "YOUR_USERNAME/net2000"
    
    def compare_versions(v1, v2):
        """Fallback version comparison."""
        try:
            v1_parts = [int(x) for x in v1.split('.')]
            v2_parts = [int(x) for x in v2.split('.')]
            max_len = max(len(v1_parts), len(v2_parts))
            v1_parts += [0] * (max_len - len(v1_parts))
            v2_parts += [0] * (max_len - len(v2_parts))
            if v1_parts > v2_parts:
                return 1
            elif v1_parts < v2_parts:
                return -1
            return 0
        except:
            return 0


class UpdateChecker:
    """Handles checking for and downloading updates from GitHub releases."""
    
    def __init__(self, github_repo=None):
        self.github_repo = github_repo or __github_repo__
        self.current_version = __version__
        self.api_url = f"https://api.github.com/repos/{self.github_repo}/releases/latest"
        
    def check_for_updates(self, include_prerelease=False):
        """
        Check if a new version is available on GitHub.
        Returns: dict with 'available', 'version', 'download_url', 'release_notes', 'is_critical'
        """
        try:
            # Create SSL context that doesn't verify certificates (for compatibility)
            context = ssl._create_unverified_context()
            
            # Create request with User-Agent header (required by GitHub API)
            req = Request(self.api_url)
            req.add_header('User-Agent', 'Internet2000-AutoUpdater')
            
            # Fetch latest release info
            with urlopen(req, context=context, timeout=10) as response:
                data = json.loads(response.read().decode('utf-8'))
            
            latest_version = data.get('tag_name', '').lstrip('v')
            release_notes = data.get('body', 'No release notes available.')
            is_prerelease = data.get('prerelease', False)
            
            # Skip prereleases unless explicitly requested
            if is_prerelease and not include_prerelease:
                return {
                    'available': False,
                    'current_version': self.current_version,
                    'latest_version': self.current_version,
                    'download_url': None,
                    'release_notes': '',
                    'is_critical': False,
                    'error': None
                }
            
            # Find the .zip asset
            download_url = None
            for asset in data.get('assets', []):
                if asset['name'].endswith('.zip'):
                    download_url = asset['browser_download_url']
                    break
            
            # Compare versions
            is_newer = self._compare_versions(latest_version, self.current_version)
            
            # Check if this is a critical update (marked with [CRITICAL] in release notes)
            is_critical = '[CRITICAL]' in release_notes.upper() or '[URGENT]' in release_notes.upper()
            
            return {
                'available': is_newer,
                'current_version': self.current_version,
                'latest_version': latest_version,
                'download_url': download_url,
                'release_notes': release_notes,
                'is_critical': is_critical,
                'error': None
            }
            
        except HTTPError as e:
            if e.code == 404:
                return {'available': False, 'error': 'No releases found on GitHub'}
            return {'available': False, 'error': f'HTTP Error: {e.code}'}
        except URLError as e:
            return {'available': False, 'error': f'Network error: {str(e)}'}
        except Exception as e:
            return {'available': False, 'error': f'Error checking for updates: {str(e)}'}
    
    def _compare_versions(self, version1, version2):
        """
        Compare two version strings (e.g., "1.2.3" vs "1.2.0").
        Returns True if version1 is newer than version2.
        """
        return compare_versions(version1, version2) > 0
    
    def download_update(self, download_url, progress_callback=None):
        """
        Download the update zip file.
        Returns: path to downloaded file or None if failed
        """
        try:
            # Create SSL context
            context = ssl._create_unverified_context()
            
            # Create temp file
            temp_dir = tempfile.gettempdir()
            zip_path = os.path.join(temp_dir, 'internet2000_update.zip')
            
            # Download with progress
            req = Request(download_url)
            req.add_header('User-Agent', 'Internet2000-AutoUpdater')
            
            with urlopen(req, context=context, timeout=30) as response:
                total_size = int(response.headers.get('content-length', 0))
                downloaded = 0
                
                with open(zip_path, 'wb') as f:
                    while True:
                        chunk = response.read(8192)
                        if not chunk:
                            break
                        f.write(chunk)
                        downloaded += len(chunk)
                        
                        if progress_callback and total_size > 0:
                            progress = int((downloaded / total_size) * 100)
                            progress_callback(progress)
            
            return zip_path
            
        except Exception as e:
            print(f"Error downloading update: {e}")
            return None
    
    def install_update(self, zip_path):
        """
        Install the update by extracting the zip and replacing files.
        This creates a batch script to handle the replacement after app exit.
        Returns: True if update script created successfully
        """
        try:
            # Determine if we're running as frozen executable
            is_frozen = getattr(sys, 'frozen', False)
            
            if is_frozen:
                app_dir = Path(sys.executable).parent
            else:
                app_dir = Path(__file__).parent
            
            # Create update script directory
            update_dir = app_dir / '_update_temp'
            update_dir.mkdir(exist_ok=True)
            
            # Extract zip to temp location
            extract_dir = update_dir / 'new_version'
            if extract_dir.exists():
                shutil.rmtree(extract_dir)
            
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(extract_dir)
            
            # Create update batch script
            update_script = self._create_update_script(app_dir, extract_dir)
            
            return update_script
            
        except Exception as e:
            print(f"Error preparing update: {e}")
            return None
    
    def _create_update_script(self, app_dir, extract_dir):
        """Create a batch script that will replace files after the app closes."""
        script_path = app_dir / '_update_temp' / 'apply_update.bat'
        
        # Find the actual content directory (might be nested in zip)
        content_dir = extract_dir
        for item in extract_dir.iterdir():
            if item.is_dir():
                content_dir = item
                break
        
        script_content = f'''@echo off
echo ========================================
echo Internet 2000 Auto-Updater
echo ========================================
echo.
echo Waiting for application to close...
timeout /t 3 /nobreak >nul

echo Backing up current version...
if exist "{app_dir}\\_backup" rmdir /s /q "{app_dir}\\_backup"
mkdir "{app_dir}\\_backup"

echo Copying files to backup...
xcopy "{app_dir}\\*.*" "{app_dir}\\_backup\\" /E /I /Y /EXCLUDE:{app_dir}\\_update_temp\\exclude.txt >nul

echo Installing new version...
xcopy "{content_dir}\\*.*" "{app_dir}\\" /E /I /Y >nul

echo Cleaning up...
rmdir /s /q "{app_dir}\\_update_temp"

echo.
echo ========================================
echo Update completed successfully!
echo ========================================
echo.
echo Starting application...
timeout /t 2 /nobreak >nul

cd /d "{app_dir}"
start "" "Internet2000_Server.exe"

exit
'''
        
        # Create exclusion list (don't backup temp files)
        exclude_path = app_dir / '_update_temp' / 'exclude.txt'
        with open(exclude_path, 'w') as f:
            f.write('_update_temp\n')
            f.write('_backup\n')
            f.write('db.sqlite3\n')
            f.write('media\n')
        
        # Write the script
        with open(script_path, 'w') as f:
            f.write(script_content)
        
        return str(script_path)
    
    def apply_update_and_restart(self, update_script):
        """
        Execute the update script and exit the application.
        The script will replace files and restart the app.
        """
        try:
            # Launch the update script in a new process
            subprocess.Popen(['cmd', '/c', update_script], 
                           creationflags=subprocess.CREATE_NEW_CONSOLE)
            
            # Exit the current application
            sys.exit(0)
            
        except Exception as e:
            print(f"Error applying update: {e}")
            return False


def check_for_updates_simple():
    """
    Simple function to check for updates.
    Returns: dict with update info or None if error
    """
    checker = UpdateChecker()
    return checker.check_for_updates()
