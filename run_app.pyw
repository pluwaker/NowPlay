"""
Launch script for NowPlay application without console window
Use this file to run the application without showing a console window
"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Import and run the application
from ui.app import NowPlayApp

if __name__ == "__main__":
    app = NowPlayApp()
    app.mainloop()
