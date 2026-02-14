# Auto-Update System Documentation

## Overview

The Internet 2000 application now includes a comprehensive auto-update system that allows users to update their application directly from GitHub releases without manual file replacement.

## Architecture

### Components

1. **version.py** - Stores current version information
2. **updater.py** - Core update logic (checking, downloading, installing)
3. **manager/update_views.py** - Django views for update UI
4. **manager/templates/manager/update_checker.html** - Update UI template
5. **build_release.bat** - Script to build and package releases

### How It Works

```
┌─────────────┐      ┌──────────────┐      ┌─────────────┐
│   Client    │─────▶│ GitHub API   │─────▶│  Download   │
│ Application │      │ (Check Ver.) │      │   Update    │
└─────────────┘      └──────────────┘      └─────────────┘
       │                                            │
       │                                            ▼
       │                                    ┌─────────────┐
       │                                    │   Extract   │
       │                                    │   & Backup  │
       │                                    └─────────────┘
       │                                            │
       │                                            ▼
       │                                    ┌─────────────┐
       └────────────────────────────────────│   Restart   │
                                            │ Application │
                                            └─────────────┘
```

## For Developers

### Building a Release

1. **Update your code** and commit changes to git

2. **Run the build script**:
   ```batch
   build_release.bat
   ```

3. **Enter the version number** when prompted (e.g., `1.0.1`)

4. The script will:
   - Update `version.py` with the new version
   - Build the executable with PyInstaller
   - Create a release package in `releases/Internet2000_vX.X.X.zip`

5. **Test the release package** before publishing

### Publishing to GitHub

1. **Create a git tag**:
   ```batch
   git tag v1.0.1
   git push origin v1.0.1
   ```

2. **Go to GitHub Releases**:
   - Navigate to: `https://github.com/YOUR_USERNAME/net2000/releases/new`
   - Select the tag you just created
   - Title: `Internet 2000 v1.0.1`
   - Description: Add release notes (what's new, bug fixes, etc.)

3. **Upload the release package**:
   - Drag and drop `releases/Internet2000_v1.0.1.zip`
   - Click "Publish release"

### Version Numbering

Follow semantic versioning (MAJOR.MINOR.PATCH):

- **MAJOR**: Breaking changes (e.g., 2.0.0)
- **MINOR**: New features, backwards compatible (e.g., 1.1.0)
- **PATCH**: Bug fixes (e.g., 1.0.1)

## For End Users

### Checking for Updates

1. **Access the admin panel** (superuser only)
2. **Navigate to the Updates section**
3. The system will automatically check for new versions

### Installing Updates

1. **Click "Download Update"** when a new version is available
2. **Wait for the download** to complete (progress bar shows status)
3. **Click "Install Update & Restart"**
4. The application will:
   - Create a backup of current files
   - Install the new version
   - Restart automatically

### Rollback (If Needed)

If an update causes issues:

1. **Close the application**
2. **Navigate to the installation folder**
3. **Delete all files** except `_backup` folder and `db.sqlite3`
4. **Copy all files** from `_backup` folder to the main folder
5. **Restart the application**

## Configuration

### Setting Your GitHub Repository

Edit `version.py` and update the repository:

```python
__github_repo__ = "YOUR_USERNAME/net2000"
```

Replace `YOUR_USERNAME` with your actual GitHub username.

### Customizing Update Behavior

In `updater.py`, you can customize:

- **Update check frequency**: Modify the API call logic
- **Download timeout**: Change the `timeout` parameter in `urlopen()`
- **Backup location**: Modify `_create_update_script()` method

## Security Considerations

1. **SSL Verification**: Currently disabled for Windows 7 compatibility
   - For production, consider enabling SSL verification
   - Update `ssl._create_unverified_context()` to use proper certificates

2. **Update Validation**: Consider adding:
   - Checksum verification (SHA256)
   - Digital signatures
   - Size validation

3. **Backup Strategy**:
   - Current: Single backup in `_backup` folder
   - Consider: Multiple versioned backups

## Troubleshooting

### Update Check Fails

**Symptom**: "Error checking for updates" message

**Solutions**:
- Check internet connection
- Verify GitHub repository is public
- Ensure `__github_repo__` is correctly set in `version.py`

### Download Fails

**Symptom**: Download progress stuck or error

**Solutions**:
- Check available disk space
- Verify firewall isn't blocking the download
- Try again later (GitHub API rate limits)

### Update Won't Install

**Symptom**: "Install Update" button doesn't work

**Solutions**:
- Ensure application has write permissions
- Close any antivirus that might block file operations
- Run as administrator (Windows)

### Application Won't Start After Update

**Symptom**: Application crashes or doesn't open

**Solutions**:
- Restore from backup (see Rollback section)
- Check Windows Event Viewer for error details
- Reinstall from original source

## API Reference

### UpdateChecker Class

```python
from updater import UpdateChecker

checker = UpdateChecker()

# Check for updates
info = checker.check_for_updates()
# Returns: {'available': bool, 'latest_version': str, 'download_url': str, ...}

# Download update
zip_path = checker.download_update(download_url, progress_callback)

# Install update
update_script = checker.install_update(zip_path)

# Apply and restart
checker.apply_update_and_restart(update_script)
```

### Django Views

- `update_check_view`: GET - Check for updates
- `update_download_view`: POST - Start download
- `update_progress_view`: GET - Get download progress
- `update_apply_view`: POST - Apply update and restart

## Best Practices

### For Developers

1. **Always test releases** before publishing
2. **Write clear release notes** for users
3. **Increment versions properly** (semantic versioning)
4. **Tag releases in git** for traceability
5. **Keep database migrations** backwards compatible

### For Deployment

1. **Backup database** before major updates
2. **Test on staging environment** first
3. **Schedule updates** during low-traffic periods
4. **Monitor logs** after updates
5. **Have rollback plan** ready

## Future Enhancements

Potential improvements:

1. **Automatic update checks** on application startup
2. **Background downloads** while app is running
3. **Delta updates** (only changed files)
4. **Update scheduling** (install at specific time)
5. **Multi-language support** for update UI
6. **Email notifications** for new releases
7. **Rollback from UI** without manual file operations

## License

This auto-update system is part of the Internet 2000 application.
