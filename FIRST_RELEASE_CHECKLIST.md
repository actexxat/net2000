# First Release Checklist

Use this checklist when creating your first release with the auto-update system.

## Pre-Release Setup

### 1. Configure Version Information
- [ ] Open `version.py`
- [ ] Update `__github_repo__` with your GitHub username
  ```python
  __github_repo__ = "YOUR_USERNAME/net2000"  # Change this!
  ```
- [ ] Set initial version to `1.0.0`
- [ ] Save the file

### 2. Test the Update System
- [ ] Run `python test_updater.py`
- [ ] Verify version information displays correctly
- [ ] Check that version comparison tests pass
- [ ] Note: Update check will fail until you create a release (this is normal)

### 3. Prepare Your Code
- [ ] All features working correctly
- [ ] All bugs fixed
- [ ] Database migrations tested
- [ ] Translations compiled (`python manage.py compilemessages`)
- [ ] Static files collected (`python manage.py collectstatic`)

### 4. Commit Everything
```batch
git add .
git commit -m "Release v1.0.0: Initial release with auto-update system"
git push origin main
```

## Building the Release

### 5. Run Build Script
- [ ] Open command prompt in project directory
- [ ] Run `build_release.bat`
- [ ] Enter version: `1.0.0`
- [ ] Wait for build to complete
- [ ] Check for any errors

### 6. Test the Build
- [ ] Navigate to `releases\Internet2000_v1.0.0\`
- [ ] Extract the ZIP file to a test folder
- [ ] Run `Internet2000_Server.exe`
- [ ] Verify application starts correctly
- [ ] Test all major features:
  - [ ] Login works
  - [ ] Dashboard loads
  - [ ] Can create/manage tables
  - [ ] Can add orders
  - [ ] Checkout works
  - [ ] Admin panel accessible
  - [ ] Translations work (if applicable)
- [ ] Close the application

## Publishing to GitHub

### 7. Create Git Tag
```batch
git tag v1.0.0
git push origin v1.0.0
```

### 8. Create GitHub Release
- [ ] Go to `https://github.com/YOUR_USERNAME/net2000/releases/new`
- [ ] Select tag: `v1.0.0`
- [ ] Release title: `Internet 2000 v1.0.0`
- [ ] Description (example):
  ```markdown
  # Internet 2000 - Initial Release
  
  ## Features
  - Complete cafe management system
  - Table and order management
  - Multi-language support (English/Arabic)
  - Business analytics dashboard
  - Auto-update system
  
  ## Installation
  1. Download the ZIP file below
  2. Extract to a folder on your computer
  3. Run Internet2000_Server.exe
  4. The application will open in your browser
  
  ## System Requirements
  - Windows 7 or later
  - No additional software required
  
  ## First Time Setup
  1. Default login: admin / admin
  2. Change password immediately after first login
  3. Configure your menu items in the admin panel
  
  ## Support
  For issues or questions, please create an issue on GitHub.
  ```
- [ ] Upload file: `releases\Internet2000_v1.0.0.zip`
- [ ] Click "Publish release"

## Post-Release Verification

### 9. Verify Release on GitHub
- [ ] Go to your repository's releases page
- [ ] Verify v1.0.0 is listed
- [ ] Download the ZIP file from GitHub
- [ ] Verify it downloads correctly
- [ ] Extract and test (should work identically to local build)

### 10. Test Auto-Update System
Since this is your first release, you can't test auto-update yet.
You'll be able to test it when you create v1.0.1.

For now, verify the update checker:
- [ ] Open the application
- [ ] Login as admin
- [ ] Go to admin panel
- [ ] Navigate to update section (if you've added it to admin)
- [ ] Should show "You are running the latest version"

## Next Steps

### 11. Document the Release
- [ ] Update README.md with installation instructions
- [ ] Add CHANGELOG.md entry:
  ```markdown
  # Changelog
  
  ## [1.0.0] - 2026-02-14
  ### Added
  - Initial release
  - Complete cafe management system
  - Auto-update functionality
  ```
- [ ] Commit and push documentation updates

### 12. Plan Next Release
To test the auto-update system, create a v1.0.1:
- [ ] Make a small change (e.g., fix a typo)
- [ ] Run `build_release.bat` with version `1.0.1`
- [ ] Create git tag `v1.0.1`
- [ ] Publish to GitHub
- [ ] Open v1.0.0 and test the update process

## Troubleshooting

### Build Fails
**Problem**: PyInstaller errors during build

**Solutions**:
- Check Python version (use 3.8 for Windows 7)
- Verify all dependencies installed: `pip install -r requirements.txt`
- Check for syntax errors in code
- Review build output for specific errors

### ZIP File Too Large
**Problem**: Release ZIP is very large

**Solutions**:
- Ensure `__pycache__` folders are excluded
- Check for unnecessary files in build
- Verify `.gitignore` is working
- Consider excluding development files

### GitHub Upload Fails
**Problem**: Can't upload ZIP to GitHub

**Solutions**:
- Check file size (GitHub has 2GB limit)
- Verify you're logged into correct account
- Check repository permissions
- Try different browser

### Update Check Shows Error
**Problem**: "Error checking for updates" in app

**Solutions**:
- Verify `__github_repo__` is correct in `version.py`
- Ensure repository is public
- Check internet connection
- Verify at least one release exists

## Success Criteria

You've successfully completed the first release when:
- ✅ Build completes without errors
- ✅ Application runs from ZIP file
- ✅ All features work correctly
- ✅ Git tag created and pushed
- ✅ GitHub release published
- ✅ ZIP file downloadable from GitHub
- ✅ Update checker shows "latest version"

## Notes

- Keep the `releases` folder locally for reference
- Don't commit ZIP files to git (they're in .gitignore)
- Save build logs if you encounter issues
- Document any build problems for future reference

---

**Congratulations on your first release! 🎉**

The auto-update system is now active and ready for future updates.
