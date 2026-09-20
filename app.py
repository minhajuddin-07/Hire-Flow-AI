import os
import sys
import runpy

# Ensure root directory is in sys.path
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

# Launch the unified 5-screen HireFlow application
app_path = os.path.join(ROOT_DIR, "app", "app.py")
runpy.run_path(app_path, run_name="__main__")
