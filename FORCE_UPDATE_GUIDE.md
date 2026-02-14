# Force Update Guide

This guide explains how to force users to update their Internet 2000 application.

## 🎯 Available Force Update Methods

### Method 1: Minimum Version Enforcement (STRONGEST)

**Use Case**: Block all access until users update to a specific version.

**How it works**: 
- Set `__minimum_required_version__` in `version.py`
- Users below this version will see a blocking page
- Only the update page remains accessible

**Steps**:

1. **Edit `version.py`** and set the minimum required version:
   ```python
   __minimum_required_version__ = "1.0.1"  # Users below 1.0.1 cannot use the app
   ```

2. **Enable the middleware** in `settings.py`:
   ```python
   MIDDLEWARE = [
       # ... other middleware ...
       'manager.middleware.VersionEnforcementMiddleware',  # Add this line
   ]
   ```

3. **Create and publish your new release** (e.g., v1.0.1)

4. **Deploy the version.py change** to existing installations

**Result**: Users with version < 1.0.1 will see a blocking page forcing them to update.

---

### Method 2: Critical Update Flag (RECOMMENDED)

**Use Case**: Mark a release as critical to show urgent warnings.

**How it works**:
- Add `[CRITICAL]` or `[URGENT]` to your GitHub release notes
- The update UI will highlight it with red warnings
- Users can still use the app but see prominent update notifications

**Steps**:

1. **Create your release** on GitHub as normal

2. **Add `[CRITICAL]` to the release notes**:
   ```markdown
   [CRITICAL] Security Update
   
   ## What's New
   - Fixed critical security vulnerability
   - Updated authentication system
   
   ## Important
   Please update immediately to ensure system security.
   ```

3. **Publish the release**

**Result**: The update checker will display the update with critical styling and warnings.

---

### Method 3: Release Notes Emphasis

**Use Case**: Communicate urgency without blocking access.

**How it works**:
- Use clear, urgent language in release notes
- Highlight breaking changes or important fixes

**Steps**:

1. **Write compelling release notes**:
   ```markdown
   ## ⚠️ IMPORTANT UPDATE REQUIRED
   
   This update fixes critical issues that may affect your business:
   - Fixed checkout calculation bug affecting payments
   - Resolved database corruption issue
   - Security patches
   
   **Action Required**: Update within 24 hours
   ```

2. **Publish the release**

**Result**: Users see the urgent message when checking for updates.

---

## 📋 Complete Force Update Workflow

### Scenario: You need to force everyone to update NOW

1. **Prepare the fix** in your code
   ```bash
   git add .
   git commit -m "Critical fix: Payment calculation bug"
   ```

2. **Build the new version**
   ```bash
   build_release.bat
   # Enter version: 1.0.2
   ```

3. **Create GitHub release** with critical flag
   - Tag: `v1.0.2`
   - Title: `Internet 2000 v1.0.2 - CRITICAL UPDATE`
   - Description:
     ```markdown
     [CRITICAL] Payment Calculation Fix
     
     ## Critical Issues Fixed
     - Fixed payment calculation bug that could result in incorrect charges
     - Resolved database sync issue
     
     ## Action Required
     All users must update immediately. This update fixes a critical bug
     affecting payment processing.
     ```
   - Upload: `releases/Internet2000_v1.0.2.zip`

4. **Enable version enforcement** (optional, for maximum force)
   
   Edit `version.py`:
   ```python
   __minimum_required_version__ = "1.0.2"
   ```
   
   Add to `settings.py`:
   ```python
   MIDDLEWARE = [
       # ... existing middleware ...
       'manager.middleware.VersionEnforcementMiddleware',
   ]
   ```

5. **Deploy version.py to existing installations**
   - If you have remote access, update the file directly
   - Or create a small patch script that only updates version.py

6. **Monitor updates**
   - Users will see the update notification
   - With enforcement enabled, they cannot use the app until updated

---

## 🔧 Technical Details

### Version Enforcement Middleware

The `VersionEnforcementMiddleware` checks every request:

```python
# Blocks access if current version < minimum required version
# Allows these paths even when blocked:
- /system-update/
- /update/
- /static/
- /media/
- /login/
- /admin/
```

### Critical Update Detection

The updater automatically detects critical updates by scanning release notes for:
- `[CRITICAL]`
- `[URGENT]`

When detected, the UI displays:
- Red warning badges
- Urgent messaging
- Prominent update buttons

### Version Comparison

Version comparison uses semantic versioning:
```
1.0.2 > 1.0.1  ✓ (newer patch)
1.1.0 > 1.0.9  ✓ (newer minor)
2.0.0 > 1.9.9  ✓ (newer major)
```

---

## 📱 User Experience

### With Version Enforcement Enabled

1. User opens app with old version
2. Sees blocking page: "Update Required"
3. Clicks "Go to Update Page"
4. Downloads and installs update
5. App restarts with new version
6. Full access restored

### With Critical Flag Only

1. User opens app normally
2. Admin sees red banner: "Critical Update Available"
3. Clicks to view update details
4. Sees urgent release notes
5. Downloads and installs at their convenience

---

## 🚨 Emergency Rollback

If a forced update causes issues:

1. **Immediately publish a new patch** (e.g., v1.0.3)

2. **Lower the minimum version requirement**
   ```python
   __minimum_required_version__ = "1.0.1"  # Allow older stable version
   ```

3. **Mark the problematic release as pre-release** on GitHub
   - This hides it from auto-update checks

4. **Communicate with users**
   - Update release notes with rollback instructions
   - Provide manual rollback steps if needed

---

## 💡 Best Practices

### When to Force Updates

✅ **DO force updates for**:
- Security vulnerabilities
- Data corruption bugs
- Payment/billing issues
- Breaking database changes

❌ **DON'T force updates for**:
- Minor UI improvements
- New features
- Performance optimizations
- Non-critical bug fixes

### Communication

1. **Be transparent**: Explain why the update is critical
2. **Provide timeline**: "Update within 24 hours"
3. **List changes**: Clear changelog of what's fixed
4. **Offer support**: Contact info for help

### Testing

Before forcing an update:
1. ✅ Test on clean Windows installation
2. ✅ Verify database migrations work
3. ✅ Test the update process itself
4. ✅ Have rollback plan ready
5. ✅ Backup user data

---

## 📊 Monitoring Updates

### Check Update Status

You can check which version users are running by:

1. **Adding version logging** to your analytics
2. **Checking server logs** for version headers
3. **Adding a version display** in the admin panel

### Future Enhancement Ideas

- Email notifications for critical updates
- Automatic background downloads
- Scheduled update windows
- Update statistics dashboard

---

## 🔐 Security Considerations

1. **HTTPS Only**: All GitHub communication uses HTTPS
2. **Verify Downloads**: Consider adding checksum verification
3. **Backup First**: Always create backups before updating
4. **Test Releases**: Use pre-releases for testing
5. **Gradual Rollout**: Consider staged rollouts for major updates

---

## Example: Real-World Scenario

**Situation**: You discovered a bug where checkout calculations are wrong.

**Action Plan**:

```bash
# 1. Fix the bug
git commit -m "Fix: Correct checkout calculation logic"

# 2. Build new version
build_release.bat  # Version: 1.0.3

# 3. Create GitHub release
Tag: v1.0.3
Title: Internet 2000 v1.0.3 - CRITICAL FIX
Notes:
  [CRITICAL] Checkout Calculation Fix
  
  This update fixes a critical bug in checkout calculations.
  All users must update immediately.
  
  Fixed:
  - Checkout calculation now correctly applies discounts
  - Minimum charge calculation fixed
  
  Update now to ensure accurate billing.

# 4. Enable enforcement
# Edit version.py:
__minimum_required_version__ = "1.0.3"

# 5. Deploy
# Users are now blocked until they update
```

**Result**: All users are forced to update, bug is eliminated.

---

## Quick Reference

| Method | Strength | User Impact | Use Case |
|--------|----------|-------------|----------|
| Minimum Version | 🔴 Blocks app | High | Critical bugs, security |
| Critical Flag | 🟡 Shows warning | Medium | Important updates |
| Release Notes | 🟢 Information only | Low | Regular updates |

---

## Support

If you need help with force updates:
1. Review this guide
2. Check `UPDATE_ARCHITECTURE.md` for system details
3. Test in development first
4. Have a rollback plan ready
