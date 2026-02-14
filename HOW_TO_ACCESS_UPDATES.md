# How to Access the Update Section

## 🚀 Quick Access

### Method 1: Via Menu (Easiest)

1. **Click the menu icon** (grid icon) in the top-right corner of the navbar
2. **Scroll down** to the "Control Center" section
3. **Click "System Updates"**
4. The update checker will open in a modal

### Method 2: Direct URL

Navigate directly to:
```
http://localhost:8000/update/check/
```

Or if running in production:
```
http://your-domain.com/update/check/
```

### Method 3: Django Admin Panel

1. Go to `/admin/`
2. You can add a custom admin page for updates (optional)

---

## 📍 Where to Find It

### In the Navigation Menu

The "System Updates" button is located in the **offcanvas menu**:

```
☰ Menu (top-right)
  ├── Dashboard
  ├── QR Management
  │
  ├── 📊 Administration (superuser only)
  │   ├── Live Monitor
  │   ├── Business Metrics
  │   └── Financial History
  │
  └── ⚙️ Control Center (superuser only)
      ├── Admin Panel
      ├── 🔄 System Updates  ← HERE
      └── Start Night/Morning Shift
```

---

## 🎯 What You'll See

When you open System Updates, you'll see:

1. **Current Version** - Your installed version
2. **Update Status** - Whether updates are available
3. **Release Notes** - What's new in the latest version
4. **Download Button** - To download the update
5. **Install Button** - To apply the update and restart

### If Critical Update Available:
- 🔴 Red alert banner
- ⚠️ "CRITICAL UPDATE REQUIRED" message
- 🔴 Red download button
- Urgent messaging

---

## 🔐 Access Requirements

**Who can access:**
- ✅ Superusers only (staff members with admin access)

**Authentication:**
- Must be logged in
- Must have `is_staff` or `is_superuser` permission

**If you see "Permission Denied":**
- Make sure you're logged in as a superuser
- Check your user permissions in Django admin

---

## 🛠️ Troubleshooting

### Can't see the "System Updates" button?

**Check:**
1. Are you logged in as a superuser?
2. Is the menu open? (Click the grid icon)
3. Scroll down to "Control Center" section

### Modal doesn't open?

**Try:**
1. Refresh the page
2. Check browser console for errors
3. Make sure JavaScript is enabled

### "Updater not available" error?

**Fix:**
1. Make sure `updater.py` exists in project root
2. Make sure `version.py` exists in project root
3. Check that update views are imported in `views.py`

---

## 📱 Mobile Access

On mobile devices:
1. Tap the **menu icon** (☰) in top-right
2. The offcanvas menu will slide in from the right
3. Scroll to find **"System Updates"**
4. Tap to open the update modal

---

## 🎨 Visual Guide

```
┌─────────────────────────────────────┐
│  INTERNET 2000        [☰] ← Click  │
├─────────────────────────────────────┤
│                                     │
│  [Offcanvas Menu Opens]             │
│                                     │
│  📊 Administration                  │
│    • Live Monitor                   │
│    • Business Metrics               │
│    • Financial History              │
│                                     │
│  ⚙️ Control Center                  │
│    • Admin Panel                    │
│    • 🔄 System Updates ← Click      │
│    • Start Night Shift              │
│                                     │
└─────────────────────────────────────┘
           ↓
┌─────────────────────────────────────┐
│  System Updates Modal               │
├─────────────────────────────────────┤
│  Current Version: 1.0.0             │
│  ✓ Update Available!                │
│  New Version: 1.0.1                 │
│                                     │
│  [Download Update]                  │
└─────────────────────────────────────┘
```

---

## 🔗 Related URLs

All update-related endpoints:

- `/update/check/` - Check for updates (JSON API)
- `/update/download/` - Download update (POST)
- `/update/progress/` - Check download progress (GET)
- `/update/apply/` - Apply update and restart (POST)

---

## 💡 Tips

1. **Bookmark it**: You can bookmark the update modal for quick access
2. **Keyboard shortcut**: No built-in shortcut, but you can add one
3. **Auto-check**: The system can be configured to auto-check on startup
4. **Notifications**: Critical updates will show red warnings

---

## 📞 Need Help?

- Check `FORCE_UPDATE_GUIDE.md` for force update methods
- Check `UPDATE_ARCHITECTURE.md` for system details
- Check `RELEASE_GUIDE.md` for creating releases

---

**Quick Summary**: Click the menu icon (☰) → Scroll to "Control Center" → Click "System Updates"
