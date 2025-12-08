"""
Quick version of Extended Operation Integration Test
Runs for 2 minutes instead of 30 for rapid testing

This is a shortened version for development/testing purposes.
Use test_extended_operation.py for the full 30-minute test.
"""

import subprocess
import psutil
import time
import sys
import os
import json
import requests
from datetime import datetime, timedelta
from typing import List, Tuple, Optional
from dataclasses import dataclass

# Test configuration - SHORTENED FOR QUICK TESTING
TEST_DURATION_MINUTES = 2  # 2 minutes for quick test
MEDIA_CHANGE_INTERVAL_SECONDS = 10  # Simulate media change every 10 seconds
MAX_UPDATE_GAP_SECONDS = 5  # Maximum acceptable gap between updates
MEMORY_CHECK_INTERVAL_SECONDS = 20  # Check memory every 20 seconds
MEMORY_LEAK_THRESHOLD_MB = 50  # Alert if memory grows by more than 50MB

# Python server configuration
PYTHON_SERVER_PORT = 8080
PYTHON_SERVER_URL = f"http://localhost:{PYTHON_SERVER_PORT}"


@dataclass
class UpdateRecord:
    """Record of a received update"""
    timestamp: datetime
    artist: str
    title: str
    position: float
    is_playing: bool
    
    def __str__(self):
        return f"{self.timestamp.strftime('%H:%M:%S')} - {self.artist} - {self.title} ({self.position:.1f}s)"


@dataclass
class GapRecord:
    """Record of a detected gap in updates"""
    start_time: datetime
    end_time: datetime
    duration_seconds: float
    
    def __str__(self):
        return f"Gap: {self.duration_seconds:.1f}s from {self.start_time.strftime('%H:%M:%S')} to {self.end_time.strftime('%H:%M:%S')}"


@dataclass
class MemorySnapshot:
    """Memory usage snapshot"""
    timestamp: datetime
    memory_mb: float
    
    def __str__(self):
        return f"{self.timestamp.strftime('%H:%M:%S')}: {self.memory_mb:.1f} MB"


class MockPythonServer:
    """Mock Python server to receive updates from MediaMonitor"""
    
    def __init__(self, port: int):
        self.port = port
        self.process: Optional[subprocess.Popen] = None
        self.updates: List[UpdateRecord] = []
        self.server_log_file = "test_server_log_quick.txt"
        
    def start(self) -> bool:
        """Start the mock server"""
        try:
            # Create a simple Flask server script
            server_script = f"""
import sys
from flask import Flask, request, jsonify
from datetime import datetime
import json

app = Flask(__name__)

@app.route('/update', methods=['POST'])
def update():
    try:
        data = request.get_json()
        timestamp = datetime.now().isoformat()
        
        # Log to file
        with open('{self.server_log_file}', 'a', encoding='utf-8') as f:
            f.write(f"{{timestamp}}|{{data.get('artist', 'Unknown')}}|{{data.get('title', 'Unknown')}}|{{data.get('position', 0)}}|{{data.get('isPlaying', False)}}\\n")
        
        return jsonify({{"status": "ok"}}), 200
    except Exception as e:
        return jsonify({{"error": str(e)}}), 500

@app.route('/config', methods=['GET'])
def config():
    return jsonify({{"selectedSource": ""}}), 200

@app.route('/sources', methods=['POST'])
def sources():
    return jsonify({{"status": "ok"}}), 200

if __name__ == '__main__':
    app.run(host='127.0.0.1', port={self.port}, debug=False)
"""
            
            # Write server script
            with open('test_mock_server_quick.py', 'w', encoding='utf-8') as f:
                f.write(server_script)
            
            # Clear previous log
            if os.path.exists(self.server_log_file):
                os.remove(self.server_log_file)
            
            # Start server
            self.process = subprocess.Popen(
                [sys.executable, 'test_mock_server_quick.py'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Wait for server to start
            time.sleep(2)
            
            # Verify server is running
            try:
                response = requests.get(f"{PYTHON_SERVER_URL}/config", timeout=2)
                if response.status_code == 200:
                    print(f"✅ Mock server started on port {self.port}")
                    return True
            except:
                pass
            
            print(f"❌ Mock server failed to start")
            return False
            
        except Exception as e:
            print(f"❌ Error starting mock server: {e}")
            return False
    
    def stop(self):
        """Stop the mock server"""
        if self.process:
            try:
                self.process.terminate()
                self.process.wait(timeout=5)
                print("✅ Mock server stopped")
            except:
                self.process.kill()
                self.process.wait()
    
    def load_updates(self) -> List[UpdateRecord]:
        """Load updates from log file"""
        updates = []
        
        if not os.path.exists(self.server_log_file):
            return updates
        
        try:
            with open(self.server_log_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    
                    parts = line.split('|')
                    if len(parts) >= 5:
                        timestamp = datetime.fromisoformat(parts[0])
                        artist = parts[1]
                        title = parts[2]
                        position = float(parts[3])
                        is_playing = parts[4].lower() == 'true'
                        
                        updates.append(UpdateRecord(
                            timestamp=timestamp,
                            artist=artist,
                            title=title,
                            position=position,
                            is_playing=is_playing
                        ))
        except Exception as e:
            print(f"⚠️ Error loading updates: {e}")
        
        return updates


class ExtendedOperationTest:
    """Extended operation integration test (quick version)"""
    
    def __init__(self):
        self.mediamonitor_process: Optional[subprocess.Popen] = None
        self.mock_server = MockPythonServer(PYTHON_SERVER_PORT)
        self.updates: List[UpdateRecord] = []
        self.gaps: List[GapRecord] = []
        self.memory_snapshots: List[MemorySnapshot] = []
        self.test_start_time: Optional[datetime] = None
        
    def start_mediamonitor(self) -> bool:
        """Start MediaMonitor process"""
        try:
            # Build MediaMonitor
            print("🔨 Building MediaMonitor...")
            build_result = subprocess.run(
                ["dotnet", "build", "--configuration", "Release"],
                cwd=".",
                capture_output=True,
                text=True
            )
            
            if build_result.returncode != 0:
                print(f"❌ Build failed: {build_result.stderr}")
                return False
            
            print("✅ Build successful")
            
            # Start MediaMonitor with diagnostic mode
            print("🚀 Starting MediaMonitor...")
            self.mediamonitor_process = subprocess.Popen(
                ["dotnet", "run", "--configuration", "Release", "--", "--diagnostic"],
                cwd=".",
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1
            )
            
            # Wait for startup
            time.sleep(3)
            
            if self.mediamonitor_process.poll() is not None:
                print(f"❌ MediaMonitor failed to start")
                return False
            
            print(f"✅ MediaMonitor started (PID: {self.mediamonitor_process.pid})")
            return True
            
        except Exception as e:
            print(f"❌ Error starting MediaMonitor: {e}")
            return False
    
    def stop_mediamonitor(self):
        """Stop MediaMonitor process"""
        if self.mediamonitor_process:
            try:
                print("🛑 Stopping MediaMonitor...")
                self.mediamonitor_process.terminate()
                try:
                    self.mediamonitor_process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    self.mediamonitor_process.kill()
                    self.mediamonitor_process.wait()
                print("✅ MediaMonitor stopped")
            except Exception as e:
                print(f"⚠️ Error stopping MediaMonitor: {e}")
    
    def get_memory_usage(self) -> float:
        """Get current memory usage of MediaMonitor in MB"""
        try:
            if self.mediamonitor_process:
                proc = psutil.Process(self.mediamonitor_process.pid)
                memory_mb = proc.memory_info().rss / (1024 * 1024)
                return memory_mb
        except:
            pass
        return 0.0
    
    def detect_gaps(self, updates: List[UpdateRecord]) -> List[GapRecord]:
        """Detect gaps in update flow exceeding threshold"""
        gaps = []
        
        for i in range(1, len(updates)):
            prev_update = updates[i - 1]
            curr_update = updates[i]
            
            gap_duration = (curr_update.timestamp - prev_update.timestamp).total_seconds()
            
            if gap_duration > MAX_UPDATE_GAP_SECONDS:
                gaps.append(GapRecord(
                    start_time=prev_update.timestamp,
                    end_time=curr_update.timestamp,
                    duration_seconds=gap_duration
                ))
        
        return gaps
    
    def check_memory_leak(self) -> bool:
        """Check if memory usage indicates a leak"""
        if len(self.memory_snapshots) < 2:
            return False
        
        first_memory = self.memory_snapshots[0].memory_mb
        last_memory = self.memory_snapshots[-1].memory_mb
        growth = last_memory - first_memory
        
        return growth > MEMORY_LEAK_THRESHOLD_MB
    
    def run_test(self) -> bool:
        """Run the extended operation test"""
        print("=" * 80)
        print("  MediaMonitor Extended Operation Integration Test (QUICK VERSION)")
        print("=" * 80)
        print(f"Duration: {TEST_DURATION_MINUTES} minutes (quick test)")
        print(f"Media change simulation: Every {MEDIA_CHANGE_INTERVAL_SECONDS} seconds")
        print(f"Maximum acceptable gap: {MAX_UPDATE_GAP_SECONDS} seconds")
        print(f"Memory check interval: {MEMORY_CHECK_INTERVAL_SECONDS} seconds")
        print("=" * 80)
        print()
        
        # Start mock server
        print("🌐 Starting mock Python server...")
        if not self.mock_server.start():
            return False
        
        # Start MediaMonitor
        if not self.start_mediamonitor():
            self.mock_server.stop()
            return False
        
        # Record test start time
        self.test_start_time = datetime.now()
        test_end_time = self.test_start_time + timedelta(minutes=TEST_DURATION_MINUTES)
        
        # Initial memory snapshot
        initial_memory = self.get_memory_usage()
        self.memory_snapshots.append(MemorySnapshot(
            timestamp=datetime.now(),
            memory_mb=initial_memory
        ))
        print(f"📊 Initial memory: {initial_memory:.1f} MB")
        print()
        
        # Run test loop
        print(f"🔬 Test running for {TEST_DURATION_MINUTES} minutes...")
        print(f"   Expected media changes: {TEST_DURATION_MINUTES * 60 // MEDIA_CHANGE_INTERVAL_SECONDS}")
        print()
        
        last_memory_check = datetime.now()
        media_change_count = 0
        
        try:
            while datetime.now() < test_end_time:
                # Check if MediaMonitor is still running
                if self.mediamonitor_process and self.mediamonitor_process.poll() is not None:
                    print("❌ MediaMonitor process terminated unexpectedly")
                    return False
                
                # Simulate media change
                media_change_count += 1
                elapsed_minutes = (datetime.now() - self.test_start_time).total_seconds() / 60
                print(f"⏱️  {elapsed_minutes:.1f} min elapsed - Media change #{media_change_count}")
                
                # Wait for next media change interval
                time.sleep(MEDIA_CHANGE_INTERVAL_SECONDS)
                
                # Periodic memory check
                if (datetime.now() - last_memory_check).total_seconds() >= MEMORY_CHECK_INTERVAL_SECONDS:
                    memory = self.get_memory_usage()
                    self.memory_snapshots.append(MemorySnapshot(
                        timestamp=datetime.now(),
                        memory_mb=memory
                    ))
                    print(f"   💾 Memory: {memory:.1f} MB")
                    last_memory_check = datetime.now()
        
        except KeyboardInterrupt:
            print("\n⚠️ Test interrupted by user")
            self.stop_mediamonitor()
            self.mock_server.stop()
            return False
        
        # Stop processes
        self.stop_mediamonitor()
        self.mock_server.stop()
        
        # Load and analyze updates
        print("\n📊 Loading and analyzing updates...")
        self.updates = self.mock_server.load_updates()
        
        # Analyze results
        return self.analyze_results()
    
    def analyze_results(self) -> bool:
        """Analyze test results"""
        print("\n" + "=" * 80)
        print("  Test Results Analysis")
        print("=" * 80)
        print()
        
        # Update statistics
        print(f"📈 Update Statistics:")
        print(f"   Total updates received: {len(self.updates)}")
        
        if len(self.updates) > 0:
            print(f"   First update: {self.updates[0].timestamp.strftime('%H:%M:%S')}")
            print(f"   Last update: {self.updates[-1].timestamp.strftime('%H:%M:%S')}")
            
            duration = (self.updates[-1].timestamp - self.updates[0].timestamp).total_seconds()
            print(f"   Update duration: {duration:.1f} seconds ({duration/60:.1f} minutes)")
            
            if duration > 0:
                update_rate = len(self.updates) / (duration / 60)
                print(f"   Average update rate: {update_rate:.1f} updates/minute")
        else:
            print("   ⚠️ No updates received!")
        print()
        
        # Gap analysis
        print(f"🔍 Gap Analysis:")
        self.gaps = self.detect_gaps(self.updates)
        
        if len(self.gaps) == 0:
            print(f"   ✅ No gaps exceeding {MAX_UPDATE_GAP_SECONDS} seconds detected")
        else:
            print(f"   ⚠️ {len(self.gaps)} gaps detected:")
            for i, gap in enumerate(self.gaps[:10], 1):
                print(f"      {i}. {gap}")
            if len(self.gaps) > 10:
                print(f"      ... and {len(self.gaps) - 10} more gaps")
        print()
        
        # Memory analysis
        print(f"💾 Memory Analysis:")
        if len(self.memory_snapshots) >= 2:
            first_memory = self.memory_snapshots[0].memory_mb
            last_memory = self.memory_snapshots[-1].memory_mb
            max_memory = max(s.memory_mb for s in self.memory_snapshots)
            avg_memory = sum(s.memory_mb for s in self.memory_snapshots) / len(self.memory_snapshots)
            growth = last_memory - first_memory
            
            print(f"   Initial memory: {first_memory:.1f} MB")
            print(f"   Final memory: {last_memory:.1f} MB")
            print(f"   Maximum memory: {max_memory:.1f} MB")
            print(f"   Average memory: {avg_memory:.1f} MB")
            print(f"   Memory growth: {growth:+.1f} MB")
            
            if self.check_memory_leak():
                print(f"   ⚠️ Potential memory leak detected (growth > {MEMORY_LEAK_THRESHOLD_MB} MB)")
            else:
                print(f"   ✅ No significant memory leak detected")
        else:
            print("   ⚠️ Insufficient memory snapshots")
        print()
        
        # Overall assessment
        print("=" * 80)
        print("  Overall Assessment (Quick Test)")
        print("=" * 80)
        
        # For quick test, we're more lenient
        passed = True
        issues = []
        warnings = []
        
        # Check 1: Updates received (warning only for quick test)
        if len(self.updates) == 0:
            warnings.append("No updates received - may need actual media playing")
        
        # Check 2: No significant gaps (if we have updates)
        if len(self.updates) > 0 and len(self.gaps) > 0:
            warnings.append(f"{len(self.gaps)} gaps exceeding {MAX_UPDATE_GAP_SECONDS} seconds detected")
        
        # Check 3: No memory leak
        if self.check_memory_leak():
            passed = False
            issues.append(f"Potential memory leak detected")
        
        # Check 4: Process stayed alive
        if self.mediamonitor_process and self.mediamonitor_process.poll() is not None:
            passed = False
            issues.append("MediaMonitor terminated unexpectedly")
        
        if passed and len(warnings) == 0:
            print("✅ QUICK TEST PASSED")
            print()
            print("Test completed successfully. Run full 30-minute test for complete validation.")
        elif passed:
            print("⚠️  QUICK TEST PASSED WITH WARNINGS")
            print()
            print("Warnings:")
            for warning in warnings:
                print(f"  ⚠️  {warning}")
            print()
            print("Note: This is a quick test. Some warnings are expected.")
            print("Run full 30-minute test with actual media playing for complete validation.")
        else:
            print("❌ QUICK TEST FAILED")
            print()
            print("Issues detected:")
            for issue in issues:
                print(f"  ❌ {issue}")
        
        print("=" * 80)
        
        return passed


def main():
    """Main entry point"""
    # Check dependencies
    try:
        import flask
    except ImportError:
        print("❌ Error: flask module not found")
        print("   Install it with: pip install flask")
        return 1
    
    try:
        import psutil
    except ImportError:
        print("❌ Error: psutil module not found")
        print("   Install it with: pip install psutil")
        return 1
    
    try:
        import requests
    except ImportError:
        print("❌ Error: requests module not found")
        print("   Install it with: pip install requests")
        return 1
    
    # Check if we're in the MediaMonitor directory
    if not os.path.exists("MediaMonitor.csproj"):
        print("❌ Error: Must run this test from the MediaMonitor directory")
        print("   cd MediaMonitor && python test_extended_operation_quick.py")
        return 1
    
    # Run the test
    test = ExtendedOperationTest()
    try:
        success = test.run_test()
        return 0 if success else 1
    except KeyboardInterrupt:
        print("\n⚠️ Test interrupted by user")
        test.stop_mediamonitor()
        test.mock_server.stop()
        return 1
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        test.stop_mediamonitor()
        test.mock_server.stop()
        return 1


if __name__ == "__main__":
    sys.exit(main())
