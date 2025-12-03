# ui/mediamonitor_manager.py
import subprocess
import sys
from pathlib import Path
from typing import Optional
from datetime import datetime


class MediaMonitorManager:
    """Manages the MediaMonitor.exe process lifecycle"""
    
    def __init__(self):
        self.process: Optional[subprocess.Popen] = None
        self.executable_path: Optional[Path] = None
        self.start_time: Optional[datetime] = None
    
    def find_executable(self) -> Optional[Path]:
        """
        Finds MediaMonitor.exe in various locations (Release/Debug/Production)
        
        Returns:
            Path to MediaMonitor.exe if found, None otherwise
        """
        # Get project root (parent of ui directory)
        project_root = Path(__file__).parent.parent
        
        # Search locations in order of preference
        search_paths = [
            # Production build (compiled application)
            project_root / "MediaMonitor.exe",
            project_root / "MediaMonitor" / "MediaMonitor.exe",
            
            # Development builds (net6.0-windows)
            project_root / "MediaMonitor" / "bin" / "Release" / "net6.0-windows10.0.19041.0" / "MediaMonitor.exe",
            project_root / "MediaMonitor" / "bin" / "Debug" / "net6.0-windows10.0.19041.0" / "MediaMonitor.exe",
            
            # Development builds (net8.0 - fallback)
            project_root / "MediaMonitor" / "bin" / "Release" / "net8.0" / "MediaMonitor.exe",
            project_root / "MediaMonitor" / "bin" / "Debug" / "net8.0" / "MediaMonitor.exe",
        ]
        
        for path in search_paths:
            if path.exists() and path.is_file():
                self.executable_path = path
                print(f"✅ Found MediaMonitor at: {path}")
                return path
        
        print("❌ MediaMonitor.exe not found in any expected location")
        return None
    
    def start(self) -> bool:
        """
        Starts MediaMonitor process without terminal window
        
        Returns:
            True if process started successfully, False otherwise
        """
        # Check if already running
        if self.is_running():
            print("⚠️ MediaMonitor is already running")
            return True
        
        # Find executable if not already found
        if not self.executable_path:
            if not self.find_executable():
                return False
        
        try:
            # Windows-specific flags for hidden process
            if sys.platform == "win32":
                # CREATE_NO_WINDOW flag (0x08000000)
                CREATE_NO_WINDOW = 0x08000000
                
                # Start process without terminal window
                self.process = subprocess.Popen(
                    [str(self.executable_path)],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    stdin=subprocess.PIPE,
                    creationflags=CREATE_NO_WINDOW
                )
            else:
                # For non-Windows systems (fallback)
                self.process = subprocess.Popen(
                    [str(self.executable_path)],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    stdin=subprocess.PIPE
                )
            
            self.start_time = datetime.now()
            print(f"✅ MediaMonitor started (PID: {self.process.pid})")
            return True
            
        except FileNotFoundError:
            print(f"❌ Executable not found: {self.executable_path}")
            return False
        except PermissionError:
            print(f"❌ Permission denied to execute: {self.executable_path}")
            return False
        except Exception as e:
            print(f"❌ Failed to start MediaMonitor: {e}")
            return False
    
    def stop(self, timeout: float = 2.0) -> bool:
        """
        Stops MediaMonitor with graceful shutdown (SIGTERM) and fallback to SIGKILL
        
        Args:
            timeout: Time in seconds to wait for graceful shutdown before force kill
        
        Returns:
            True if process stopped successfully, False otherwise
        """
        if not self.is_running():
            print("⚠️ MediaMonitor is not running")
            return True
        
        try:
            # Send SIGTERM for graceful shutdown
            print(f"🛑 Stopping MediaMonitor (PID: {self.process.pid})...")
            self.process.terminate()
            
            # Wait for graceful shutdown
            try:
                self.process.wait(timeout=timeout)
                print("✅ MediaMonitor stopped gracefully")
                self.process = None
                self.start_time = None
                return True
            except subprocess.TimeoutExpired:
                # Force kill if timeout exceeded
                print(f"⚠️ Graceful shutdown timeout, forcing kill...")
                self.process.kill()
                self.process.wait(timeout=1.0)
                print("✅ MediaMonitor force killed")
                self.process = None
                self.start_time = None
                return True
                
        except Exception as e:
            print(f"❌ Error stopping MediaMonitor: {e}")
            # Try to force kill as last resort
            try:
                if self.process:
                    self.process.kill()
                    self.process = None
                    self.start_time = None
            except:
                pass
            return False
    
    def is_running(self) -> bool:
        """
        Checks if MediaMonitor process is running
        
        Returns:
            True if process is running, False otherwise
        """
        if self.process is None:
            return False
        
        # Check if process is still alive
        poll_result = self.process.poll()
        
        if poll_result is not None:
            # Process has terminated
            self.process = None
            self.start_time = None
            return False
        
        return True
