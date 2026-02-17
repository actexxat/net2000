import os
from pathlib import Path
import sys

BASE_DIR = Path(__file__).resolve().parent
print(f"BASE_DIR: {BASE_DIR}")
print(f"Templates exist: {os.path.exists(os.path.join(BASE_DIR, 'templates'))}")
print(f"Admin base exists: {os.path.exists(os.path.join(BASE_DIR, 'templates', 'admin', 'base.html'))}")
