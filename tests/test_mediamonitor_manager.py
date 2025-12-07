"""
Unit tests for MediaMonitorManager
Tests process lifecycle management, executable finding, and graceful shutdown
"""
import unittest
import subprocess
import sys
import time
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from ui.mediamonitor_manager import MediaMonitorManager


class TestMediaMonitorManager(unittest.TestCase):
    """Test suite for MediaMonitorManager class"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.manager = MediaMonitorManager()
    
    def tearDown(self):
        """Clean up after tests"""
        # Ensure process is stopped after each test
        if self.manager.process:
            try:
                self.manager.stop(timeout=1.0)
            except:
                pass
    
    def test_find_executable_success(self):
        """Test successful finding of MediaMonitor.exe"""
        # Create a mock path that exists
        with patch.object(Path, 'exists', return_value=True), \
             patch.object(Path, 'is_file', return_value=True):
            
            result = self.manager.find_executable()
            
            # Should return a Path object
            self.assertIsNotNone(result)
            self.assertIsInstance(result, Path)
            # Should set executable_path attribute
            self.assertEqual(self.manager.executable_path, result)
    
    def test_find_executable_not_found(self):
        """Test handling when MediaMonitor.exe is not found"""
        # Mock all paths to not exist
        with patch.object(Path, 'exists', return_value=False):
            
            result = self.manager.find_executable()
            
            # Should return None when not found
            self.assertIsNone(result)
            # executable_path should remain None
            self.assertIsNone(self.manager.executable_path)
    
    def test_start_process(self):
        """Test successful process start"""
        # Create a mock process
        mock_process = Mock(spec=subprocess.Popen)
        mock_process.pid = 12345
        mock_process.poll.return_value = None  # Process is running
        
        # Mock the executable path
        mock_path = Path("MediaMonitor.exe")
        self.manager.executable_path = mock_path
        
        with patch('subprocess.Popen', return_value=mock_process):
            result = self.manager.start()
            
            # Should return True on success
            self.assertTrue(result)
            # Should store the process
            self.assertEqual(self.manager.process, mock_process)
            # Should set start_time
            self.assertIsNotNone(self.manager.start_time)
    
    def test_start_process_already_running(self):
        """Test starting when process is already running"""
        # Set up a running process
        mock_process = Mock(spec=subprocess.Popen)
        mock_process.poll.return_value = None  # Process is running
        self.manager.process = mock_process
        
        result = self.manager.start()
        
        # Should return True (already running)
        self.assertTrue(result)
        # Should keep the same process
        self.assertEqual(self.manager.process, mock_process)
    
    def test_start_process_executable_not_found(self):
        """Test start when executable cannot be found"""
        # No executable path set
        self.manager.executable_path = None
        
        with patch.object(self.manager, 'find_executable', return_value=None):
            result = self.manager.start()
            
            # Should return False
            self.assertFalse(result)
            # Process should remain None
            self.assertIsNone(self.manager.process)
    
    def test_stop_process_graceful(self):
        """Test graceful shutdown with SIGTERM"""
        # Create a mock process that terminates gracefully
        mock_process = Mock(spec=subprocess.Popen)
        mock_process.pid = 12345
        mock_process.poll.return_value = None  # Initially running
        mock_process.wait.return_value = 0  # Exits cleanly
        
        self.manager.process = mock_process
        
        result = self.manager.stop(timeout=2.0)
        
        # Should return True on success
        self.assertTrue(result)
        # Should call terminate (SIGTERM)
        mock_process.terminate.assert_called_once()
        # Should wait for graceful shutdown
        mock_process.wait.assert_called_once_with(timeout=2.0)
        # Should clear process reference
        self.assertIsNone(self.manager.process)
        self.assertIsNone(self.manager.start_time)
    
    def test_stop_process_force(self):
        """Test force kill when graceful shutdown times out"""
        # Create a mock process that doesn't respond to SIGTERM
        mock_process = Mock(spec=subprocess.Popen)
        mock_process.pid = 12345
        mock_process.poll.return_value = None  # Initially running
        # First wait times out, second wait succeeds
        mock_process.wait.side_effect = [subprocess.TimeoutExpired('cmd', 2.0), 0]
        
        self.manager.process = mock_process
        
        result = self.manager.stop(timeout=2.0)
        
        # Should return True (force killed)
        self.assertTrue(result)
        # Should call terminate first
        mock_process.terminate.assert_called_once()
        # Should call kill after timeout
        mock_process.kill.assert_called_once()
        # Should clear process reference
        self.assertIsNone(self.manager.process)
        self.assertIsNone(self.manager.start_time)
    
    def test_stop_process_not_running(self):
        """Test stop when process is not running"""
        # No process running
        self.manager.process = None
        
        result = self.manager.stop()
        
        # Should return True (nothing to stop)
        self.assertTrue(result)
    
    def test_is_running_true(self):
        """Test is_running when process is active"""
        # Create a mock running process
        mock_process = Mock(spec=subprocess.Popen)
        mock_process.poll.return_value = None  # Process is running
        
        self.manager.process = mock_process
        
        result = self.manager.is_running()
        
        # Should return True
        self.assertTrue(result)
        # Should call poll to check status
        mock_process.poll.assert_called_once()
    
    def test_is_running_false_no_process(self):
        """Test is_running when no process exists"""
        # No process
        self.manager.process = None
        
        result = self.manager.is_running()
        
        # Should return False
        self.assertFalse(result)
    
    def test_is_running_false_process_terminated(self):
        """Test is_running when process has terminated"""
        # Create a mock terminated process
        mock_process = Mock(spec=subprocess.Popen)
        mock_process.poll.return_value = 0  # Process has exited
        
        self.manager.process = mock_process
        
        result = self.manager.is_running()
        
        # Should return False
        self.assertFalse(result)
        # Should clear process reference
        self.assertIsNone(self.manager.process)
        self.assertIsNone(self.manager.start_time)


if __name__ == '__main__':
    unittest.main()
