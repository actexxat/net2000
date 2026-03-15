---
description: Verify application pages after changes
---

// turbo-all

After making any changes to the codebase, follow these steps to ensure all pages are still accessible:

1. Run the page verification script:
```powershell
python scripts/verify_pages.py
```

2. If any page fails (returns something other than [OK]), investigate the changes and fix the issue before proceeding.

3. If the script succeeds, you can be confident that the basic navigation and page rendering are working correctly.
