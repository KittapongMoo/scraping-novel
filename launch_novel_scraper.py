#!/usr/bin/env python3
"""
Novel Scraper GUI Launcher
Double-click this file to start the Novel Scraper GUI application.
"""

import os
import sys
import subprocess
from pathlib import Path

def main():
    # Get the directory where this script is located
    script_dir = Path(__file__).parent.absolute()
    app_file = script_dir / "app_version_scrape_novel.py"
    
    # Change to the script directory
    os.chdir(script_dir)
    
    print("🚀 Starting Novel Scraper GUI...")
    print(f"📁 Working directory: {script_dir}")
    
    # Check if the main app file exists
    if not app_file.exists():
        print(f"❌ Error: {app_file} not found!")
        input("Press Enter to exit...")
        return
    
    # Check if virtual environment exists and activate it
    venv_path = script_dir / ".venv"
    if venv_path.exists():
        print("🔧 Virtual environment found, activating...")
        if sys.platform == "win32":
            python_exe = venv_path / "Scripts" / "python.exe"
        else:
            python_exe = venv_path / "bin" / "python"
    else:
        print("🔧 Using system Python...")
        python_exe = sys.executable
    
    try:
        # Run the GUI application
        print("✅ Launching Novel Scraper GUI...")
        subprocess.run([str(python_exe), str(app_file)], check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ Error running application: {e}")
        input("Press Enter to exit...")
    except KeyboardInterrupt:
        print("\n⏹️ Application stopped by user")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        input("Press Enter to exit...")

if __name__ == "__main__":
    main()
