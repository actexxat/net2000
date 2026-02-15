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
    db_initial = os.path.join(base_dir, 'db_initial.sqlite3')
    
    # Initialize if db doesn't exist OR is 0 bytes
    if (not os.path.exists(db_path) or os.path.getsize(db_path) == 0) and os.path.exists(db_initial):
        print(f"[INIT] Initializing database from {db_initial}...")
        import shutil
        try:
            shutil.copy2(db_initial, db_path)
            print("[INIT] Database initialized successfully.")
        except Exception as e:
            print(f"[ERROR] Failed to initialize database: {e}")

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

