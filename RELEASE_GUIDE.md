# Quick Release Guide

## Step-by-Step: Creating a New Release

### 1. Prepare Your Code
```batch
# Commit all changes
git add .
git commit -m "Release v1.0.1: Description of changes"
git push origin main
```

### 2. Build the Release
```batch
# Run the build script
build_release.bat

# When prompted, enter version (e.g., 1.0.1)
# Wait for build to complete
```

### 3. Test the Release
```batch
# Navigate to releases folder
cd releases\Internet2000_v1.0.1

# Extract and test the ZIP file
# Verify all features work correctly
```

### 4. Create Git Tag
```batch
# Create and push tag
git tag v1.0.1
git push origin v1.0.1
```

### 5. Publish to GitHub

1. Go to: https://github.com/YOUR_USERNAME/net2000/releases/new
2. Choose tag: `v1.0.1`
3. Release title: `Internet 2000 v1.0.1`
4. Description:
   ```markdown
   ## What's New
   - Feature 1
   - Feature 2
   
   ## Bug Fixes
   - Fixed issue 1
   - Fixed issue 2
   
   ## Installation
   Download the ZIP file below and extract it to a folder.
   Run Internet2000_Server.exe to start the application.
   ```
5. Upload: `releases\Internet2000_v1.0.1.zip`
6. Click "Publish release"

### 6. Verify Auto-Update Works

1. Open an older version of the app
2. Go to admin panel → Updates
3. Verify new version is detected
4. Test download and installation

## Common Release Scenarios

### Patch Release (Bug Fix)
- Version: 1.0.0 → 1.0.1
- Changes: Bug fixes only
- Testing: Focus on fixed issues

### Minor Release (New Features)
- Version: 1.0.0 → 1.1.0
- Changes: New features, backwards compatible
- Testing: Full regression test

### Major Release (Breaking Changes)
- Version: 1.0.0 → 2.0.0
- Changes: Major changes, may break compatibility
- Testing: Complete system test
- Note: May require database migration

## Checklist

Before publishing:
- [ ] All tests pass
- [ ] Version number updated
- [ ] Release notes written
- [ ] ZIP file tested
- [ ] Git tag created
- [ ] Database migrations tested (if any)
- [ ] Backup instructions provided (if needed)

## Emergency Rollback

If a release has critical issues:

1. **Immediately create a new patch release** with the fix
2. **Update GitHub release** to mark as "pre-release"
3. **Notify users** via release notes
4. **Provide rollback instructions** in release description

## Version History Template

Keep track in CHANGELOG.md:

```markdown
# Changelog

## [1.0.1] - 2026-02-14
### Fixed
- Fixed checkout calculation bug
- Resolved translation issues

### Changed
- Improved performance of dashboard polling

## [1.0.0] - 2026-02-01
### Added
- Initial release
- Auto-update system
- Multi-language support
```

## Tips

- **Test on clean Windows installation** if possible
- **Keep releases small and frequent** rather than large and rare
- **Document breaking changes** clearly
- **Maintain backwards compatibility** when possible
- **Archive old releases** but keep them available
