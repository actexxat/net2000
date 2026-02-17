import os
import sys
import webbrowser
import threading

# Add the current directory to sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set the environment variable for Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

def open_browser():
    """Open the default browser after a short delay to ensure server is ready"""
    import time
    time.sleep(3)  # Wait 3 seconds for server to start
    print("[ACTION] Opening browser to http://127.0.0.1:8000...")
    webbrowser.open('http://127.0.0.1:8000')

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

    print("--------------------------------------------------")
    print("Cafe App is starting...")
    print("Access the app from other devices using this PC's IP address.")
    print("Example: http://192.168.1.XX:8000")
    print("Press Ctrl+C to stop the server.")
    print("--------------------------------------------------")
    
    # Open browser in a separate thread
    browser_thread = threading.Thread(target=open_browser, daemon=True)
    browser_thread.start()
    
    # Set the environment variable for Django settings BEFORE importing application
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
    
    from core.wsgi import application
    from waitress import serve
    
    # Serve the application using Waitress
    # host='0.0.0.0' makes it available on the local network
    serve(application, host='0.0.0.0', port=8000, threads=8)

