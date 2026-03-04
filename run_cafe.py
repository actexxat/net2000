import os
import sys
import webbrowser
import threading
import ctypes
import time

# Add the current directory to sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set the environment variable for Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

def open_browser():
    """Open the default browser after a delay to ensure server is ready"""
    import time
    # Frozen builds need slightly more time to unpack and start waitress
    delay = 6 if getattr(sys, 'frozen', False) else 3
    time.sleep(delay)
    print("[ACTION] Opening browser to http://127.0.0.1:8000...")
    if sys.platform == "win32":
        # Using native os.system('start') is far more reliable in frozen background apps
        os.system('start http://127.0.0.1:8000')
    else:
        webbrowser.open('http://127.0.0.1:8000')

def is_already_running():
    """Check if another instance of the server is already running."""
    import socket
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(1)
        s.connect(('127.0.0.1', 8000))
        s.close()
        return True
    except:
        return False

def hide_console_after_delay(delay=5):
    """Wait for some time then hide the console window."""
    time.sleep(delay)
    if sys.platform == "win32":
        hwnd = ctypes.windll.kernel32.GetConsoleWindow()
        if hwnd:
            ctypes.windll.user32.ShowWindow(hwnd, 0) # SW_HIDE
def relaunch_hidden():
    """Relaunch the app completely hidden, supporting both source and PyInstaller environments."""
    import subprocess
    
    # 1. If running as a packaged EXE (Production)
    if getattr(sys, 'frozen', False):
        # sys.executable is the .exe file (Internet2000.exe)
        # Add a custom flag so we know it's the child process, but don't suppress the browser
        args = [sys.executable, "--is-child"]
        subprocess.Popen(args, creationflags=subprocess.CREATE_NO_WINDOW)
        return True
        
    # 2. If running from Source (Development)
    elif sys.platform == "win32" and "pythonw.exe" not in sys.executable.lower():
        pythonw = sys.executable.replace("python.exe", "pythonw.exe")
        if os.path.exists(pythonw):
            args = [pythonw, __file__, "--is-child"]
            subprocess.Popen(args, creationflags=subprocess.CREATE_NO_WINDOW)
            return True
            
    return False

if __name__ == '__main__':
    # DATABASE INITIALIZATION (Must happen BEFORE importing application to avoid SQLite creating empty file)
    if getattr(sys, 'frozen', False):
        # When running as EXE, base_dir is the folder containing the EXE
        base_dir = os.path.dirname(sys.executable)
    else:
        # When running as script, base_dir is the script's folder
        base_dir = os.path.dirname(os.path.abspath(__file__))
        
    db_path = os.path.join(base_dir, 'db.sqlite3')
    # If db.sqlite3 does not exist, it means either the build process failed to include it,
    # or this is a fresh run where a database needs to be initialized.
    # In a typical PyInstaller build scenario, db.sqlite3 should already be present and migrated.
    # No explicit initialization from db_initial.sqlite3 is needed as the build script now
    # copies db.sqlite3 directly.

    is_frozen = getattr(sys, 'frozen', False)

    # --- Handle Background Startup ---
    # In production (frozen), we run in background by default unless it's explicitly explicitly the child.
    if "--background" in sys.argv or (is_frozen and "--is-child" not in sys.argv):
        if is_already_running():
            print("[STATUS] Server is already running. Skipping background start.")
            sys.exit(0)
            
        print("--------------------------------------------------")
        print("Cafe App is starting in background mode...")
        print("The terminal will close, and the app will run silently.")
        print("--------------------------------------------------")
        # The background process will handle opening the browser.            
        # Give user time to read the message
        time.sleep(3)
        
        # Relaunch as windowless process
        if relaunch_hidden():
            sys.exit(0)
        else:
            # Fallback to hiding current window if pythonw not found
            if sys.platform == "win32":
                hwnd = ctypes.windll.kernel32.GetConsoleWindow()
                if hwnd: ctypes.windll.user32.ShowWindow(hwnd, 0)
    
    # --- Normal Startup / Background Child Process ---
    # Set the environment variable for Django settings BEFORE importing application
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

    # Open browser (unless suppressed)
    if "--no-browser" not in sys.argv:
        browser_thread = threading.Thread(target=open_browser, daemon=True)
        browser_thread.start()
    
    from core.wsgi import application
    from waitress import serve
    
    # Serve the application using Waitress
    # host='0.0.0.0' makes it available on the local network
    print(f"[STATUS] Server running on http://0.0.0.0:8000")
    serve(application, host='0.0.0.0', port=8000, threads=8)

