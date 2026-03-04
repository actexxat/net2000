import sqlite3
import sys
import os

def clean_db(db_path):
    if not os.path.exists(db_path):
        print(f"Database not found at {db_path}")
        return

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Clear sessions to avoid "Corrupted Session" warnings when running with a new SECRET_KEY
        cursor.execute("DELETE FROM django_session;")
        
        # Clear any system-update cached flags if they exist
        try:
            cursor.execute("DELETE FROM django_cache WHERE cache_key LIKE '%github_update_info%';")
        except sqlite3.OperationalError:
            pass # Cache table might not exist
            
        conn.commit()
        conn.close()
        print(f"Successfully cleaned database: {db_path}")
    except Exception as e:
        print(f"Error cleaning database: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        clean_db(sys.argv[1])
    else:
        print("Usage: python clean_db.py <path_to_db.sqlite3>")
