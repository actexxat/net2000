# Force Update Quick Reference

## 🚀 Quick Start: Force an Update

### Option 1: Soft Force (Recommended)
**Mark release as critical - shows urgent warnings**

```markdown
# In your GitHub release notes:
[CRITICAL] Important Security Update

This update fixes critical issues. Please update immediately.
```

**Result**: Red warnings, urgent messaging, but app still works

---

### Option 2: Hard Force (Nuclear Option)
**Block app until users update**

```python
# 1. Edit version.py
__minimum_required_version__ = "1.0.2"

# 2. Edit settings.py - add to MIDDLEWARE:
'manager.middleware.VersionEnforcementMiddleware',
```

**Result**: App completely blocked until update

---

## 📋 Complete Workflow

```bash
# 1. Fix the critical bug
git commit -m "Critical fix"

# 2. Build new version
build_release.bat
# Enter: 1.0.2

# 3. Create GitHub Release
Tag: v1.0.2
Title: Internet 2000 v1.0.2 - CRITICAL
Notes: [CRITICAL] Security fix - update immediately
Upload: releases/Internet2000_v1.0.2.zip

# 4. (Optional) Enable hard block
# Edit version.py:
__minimum_required_version__ = "1.0.2"

# Edit settings.py, add to MIDDLEWARE:
'manager.middleware.VersionEnforcementMiddleware',
```

---

## 🎨 Critical Update Features

When you add `[CRITICAL]` or `[URGENT]` to release notes:

✅ Red alert banner appears  
✅ "CRITICAL UPDATE REQUIRED" heading  
✅ Red download button  
✅ Urgent messaging throughout UI  
✅ App still functional (unless hard block enabled)

---

## 🔧 Files to Edit

### For Soft Force (Critical Flag)
- ✏️ GitHub release notes only

### For Hard Force (Version Block)
- ✏️ `version.py` - set `__minimum_required_version__`
- ✏️ `settings.py` - add middleware

---

## 💡 When to Use Each Method

| Situation | Method | Why |
|-----------|--------|-----|
| Security vulnerability | Hard Force | Immediate action required |
| Payment bug | Hard Force | Financial impact |
| Data corruption | Hard Force | Data integrity critical |
| Important feature | Soft Force | Encourage but don't block |
| Bug fix | Soft Force | Update recommended |
| UI improvement | Normal | No urgency |

---

## ⚠️ Emergency Rollback

If forced update causes problems:

```python
# 1. Lower minimum version
__minimum_required_version__ = "1.0.1"  # Back to stable

# 2. Publish hotfix immediately
build_release.bat  # Version: 1.0.3

# 3. Mark bad release as pre-release on GitHub
```

---

## 📞 Support

- Full guide: `FORCE_UPDATE_GUIDE.md`
- Architecture: `UPDATE_ARCHITECTURE.md`
- Release process: `RELEASE_GUIDE.md`

---

**Remember**: Always test updates before forcing them!
