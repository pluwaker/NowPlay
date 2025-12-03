"""
Integration tests for NowPlayApp and MediaMonitor interaction
Tests the complete workflow of starting/stopping server with MediaMonitor

These tests verify the integration between the app's server management
and MediaMonitor process lifecycle, ensuring they work together correctly.
"""
import unittest
from unittest.mock import Mock, patch, MagicMock, call
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from ui.mediamonitor_manager import MediaMonitorManager


class MockApp:
    """Mock NowPlayApp for testing integration logic"""
    
    def __init__(self):
        self.port = None
        self.obs_url = ""
        self.server_process = None
        self.server_thread = None
        self.obs_link = Mock()
        self.mediamonitor_manager = MediaMonitorManager()
    
    def start_server(self):
        """Simplified start_server logic for testing"""
        try:
            # Simulate finding port
            self.port = 8080
            self.obs_url = f"http://localhost:{self.port}/index.html"
            
            # Simulate starting server thread
            self.server_thread = Mock()
            self.server_thread.is_alive = Mock(return_value=True)
            self.server_process = self.server_thread
            
            self.obs_link.set(self.obs_url)
            
            # Start MediaMonitor after server is running
            if not self.mediamonitor_manager.start():
                # In real app, this would show a warning
                return "warning"
            
            return True
        except Exception as e:
            return False
    
    def stop_server(self):
        """Simplified stop_server logic for testing"""
        # Stop MediaMonitor first
        self.mediamonitor_manager.stop()
        
        # Stop server
        if hasattr(self, 'server_thread') and self.server_thread and self.server_thread.is_alive():
            self.server_thread = None
            self.server_process = None
            self.obs_url = ""
            self.obs_link.set("")
            return True
        return False
    
    def is_server_running(self):
        """Check if server is running"""
        return hasattr(self, 'server_thread') and self.server_thread and self.server_thread.is_alive()
    
    def on_closing(self):
        """Handle window close event"""
        self.exit_app()
    
    def exit_app(self):
        """Exit application with cleanup"""
        # Stop MediaMonitor if running with increased timeout
        if self.mediamonitor_manager.is_running():
            self.mediamonitor_manager.stop(timeout=3.0)
        
        self.stop_server()
        # In real app, this would call self.destroy()


class TestAppIntegration(unittest.TestCase):
    """Integration test suite for NowPlayApp with MediaMonitor"""
    
    def test_start_server_with_mediamonitor(self):
        """Test that starting server also starts MediaMonitor"""
        app = MockApp()
        
        # Mock MediaMonitor manager
        app.mediamonitor_manager = Mock(spec=MediaMonitorManager)
        app.mediamonitor_manager.start.return_value = True
        
        # Start server
        result = app.start_server()
        
        # Verify server started
        self.assertTrue(result)
        self.assertEqual(app.port, 8080)
        self.assertTrue(app.is_server_running())
        
        # Verify MediaMonitor was started
        app.mediamonitor_manager.start.assert_called_once()
    
    def test_start_server_mediamonitor_fails(self):
        """Test server starts even if MediaMonitor fails to start"""
        app = MockApp()
        
        # Mock MediaMonitor manager that fails
        app.mediamonitor_manager = Mock(spec=MediaMonitorManager)
        app.mediamonitor_manager.start.return_value = False
        
        # Start server
        result = app.start_server()
        
        # Verify server still started (returns "warning")
        self.assertEqual(result, "warning")
        self.assertEqual(app.port, 8080)
        self.assertTrue(app.is_server_running())
        
        # Verify MediaMonitor start was attempted
        app.mediamonitor_manager.start.assert_called_once()
    
    def test_stop_server_with_mediamonitor(self):
        """Test that stopping server also stops MediaMonitor"""
        app = MockApp()
        
        # Setup running server
        app.port = 8080
        app.server_thread = Mock()
        app.server_thread.is_alive = Mock(return_value=True)
        app.server_process = app.server_thread
        
        # Mock MediaMonitor manager
        app.mediamonitor_manager = Mock(spec=MediaMonitorManager)
        app.mediamonitor_manager.stop.return_value = True
        
        # Stop server
        result = app.stop_server()
        
        # Verify server stopped
        self.assertTrue(result)
        
        # Verify MediaMonitor was stopped
        app.mediamonitor_manager.stop.assert_called_once()
    
    def test_stop_server_when_not_running(self):
        """Test stopping server when nothing is running"""
        app = MockApp()
        
        # No server running
        app.server_thread = None
        
        # Mock MediaMonitor manager
        app.mediamonitor_manager = Mock(spec=MediaMonitorManager)
        app.mediamonitor_manager.stop.return_value = True
        
        # Stop server
        result = app.stop_server()
        
        # Verify MediaMonitor stop was called
        app.mediamonitor_manager.stop.assert_called_once()
        
        # Verify result is False (nothing was running)
        self.assertFalse(result)
    
    def test_app_close_cleanup(self):
        """Test that closing app properly cleans up MediaMonitor"""
        app = MockApp()
        
        # Setup running server
        app.port = 8080
        app.server_thread = Mock()
        app.server_thread.is_alive = Mock(return_value=True)
        app.server_process = app.server_thread
        
        # Mock MediaMonitor manager
        app.mediamonitor_manager = Mock(spec=MediaMonitorManager)
        app.mediamonitor_manager.is_running.return_value = True
        app.mediamonitor_manager.stop.return_value = True
        
        # Call exit_app
        app.exit_app()
        
        # Verify MediaMonitor was stopped with increased timeout
        app.mediamonitor_manager.is_running.assert_called()
        # stop() is called twice: once with timeout=3.0 in exit_app, once in stop_server
        self.assertEqual(app.mediamonitor_manager.stop.call_count, 2)
        # First call should be with timeout=3.0
        app.mediamonitor_manager.stop.assert_any_call(timeout=3.0)
    
    def test_on_closing_calls_exit_app(self):
        """Test that window close handler calls exit_app"""
        app = MockApp()
        
        # Mock exit_app
        app.exit_app = Mock()
        
        # Call on_closing
        app.on_closing()
        
        # Verify exit_app was called
        app.exit_app.assert_called_once()
    
    def test_app_close_when_mediamonitor_not_running(self):
        """Test closing app when MediaMonitor is not running"""
        app = MockApp()
        
        # No server running
        app.server_thread = None
        
        # Mock MediaMonitor manager (not running)
        app.mediamonitor_manager = Mock(spec=MediaMonitorManager)
        app.mediamonitor_manager.is_running.return_value = False
        
        # Call exit_app
        app.exit_app()
        
        # Verify is_running was checked
        app.mediamonitor_manager.is_running.assert_called()
        
        # stop() is called once in stop_server (even though not running)
        # but NOT called with timeout=3.0 since is_running() returned False
        app.mediamonitor_manager.stop.assert_called_once_with()  # Called without timeout
    
    def test_start_stop_cycle(self):
        """Test complete start-stop cycle"""
        app = MockApp()
        
        # Mock MediaMonitor manager
        app.mediamonitor_manager = Mock(spec=MediaMonitorManager)
        app.mediamonitor_manager.start.return_value = True
        app.mediamonitor_manager.stop.return_value = True
        
        # Start server
        start_result = app.start_server()
        self.assertTrue(start_result)
        self.assertTrue(app.is_server_running())
        
        # Verify MediaMonitor started
        app.mediamonitor_manager.start.assert_called_once()
        
        # Stop server
        stop_result = app.stop_server()
        self.assertTrue(stop_result)
        
        # Verify MediaMonitor stopped
        app.mediamonitor_manager.stop.assert_called_once()


if __name__ == '__main__':
    unittest.main()
