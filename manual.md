# Internet 2000 - Cafe Management System
## Staff Maintenance & Troubleshooting Guide (One-Week Travel Edition)

This guide is for the cafe staff to ensure the management system runs smoothly while the owner is away.

---

### 1. How to Start/Restart the System
If the system becomes slow, the dashboard stops updating, or the computer reboots:
- **Shortcut**: Double-click the `start.bat` file on the desktop (or in `D:\net2000`).
- **Wait**: A black window will appear. Once you see "Cafe App is starting...", the system is active.
- **Auto-Fix**: The script is designed to automatically close any old "frozen" instances and start a fresh one.

### 2. QR Menu for Customers
Customers scan the code to order. 
- **Important**: The computer running the server **MUST** stay on and connected to the same Wi-Fi as the customers' phones.
- **If customers cannot open the menu**:
    1. Check if the "Server PC" has disconnected from Wi-Fi.
    2. Restart the server using `start.bat`.
    3. Verify the PC's IP address hasn't changed (The `start.bat` window shows the current link, e.g., `http://192.168.1.XX:8000`).

### 3. Missing Notifications / "New Order" Sound
- The dashboard (Admin screen) polls for new orders every few seconds.
- If you notice a customer has ordered but it's not showing:
    - Refresh the browser page (`F5`).
    - Make sure the speakers are on if you rely on the notification sound.

### 4. Special Table 0 (The Permanent Table)
- **Table 0** is to be used for "Walk-in" or "Misc" orders (Printing, Copies, single orders).
- It is styled **Indigo/Purple** and always stays at the top.
- It **never** has a minimum charge, so use it for quick services.

### 5. Daily Backups
- Before closing the cafe every night, double-click the `backup_db.bat` file.
- This creates a copy of all sales data in the `backups` folder.

### 6. Emergency Contact
- **Owner**: [User to add phone number]
- **Issue**: If the "Black Screen" (Terminal) shows any text starting with `[ERROR]`, take a photo and send it to the owner.

---
**Technical Note for Owner**:
- Ensure the PC is set to **NOT** go to sleep (Settings > Power & Sleep > Sleep: Never).
- Ensure the Wi-Fi is set to "Connect Automatically".
- It is recommended to pin `start.bat` and `backup_db.bat` to the Taskbar or Desktop for easy access by staff.
