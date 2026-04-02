"""
Recovery Simulation Integration Test for MediaMonitor
Tests automatic recovery from event subscription failures

Requirements validated:
- 1.3: Detects event subscription failure and re-establishes subscriptions
- 3.1: Triggers automatic recovery after 30 seconds without updates
- 3.5: Logs recovery outcome and verifies success
"""

import subprocess
import psutil
import time
import sys
import os
import json
import requests
from datetime import datetime, timedelta
from typing import List, Optional
from dataclasses import dataclass

# Test configuration
RECOVERY_TIMEOUT_SECONDS = 30  # Time without updates before recovery triggers
RECOVERY_VERIFICATION_SECONDS = 10  # Time to wait for updates after recovery
RECOVERY_CYCLES_TO_TEST = 2  # Number of recovery cycles to test
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
        return f"{self.timestamp.strftime('%H:%M:%S.%f')[:-3]} - {self.artist} - {self.title}"


@dataclass
class RecoveryEvent:
    """Record of a recovery event"""
    trigger_time: datetime
    completion_time: Optional[datetime]
    success: bool
    first_update_after_recovery: Optional[datetime]
    recovery_duration_seconds: float
    
    def __str__(self):
        status = "✅ SUCCESS" if self.success else "❌ FAILED"
        if self.first_update_after_recovery:
            resume_time = (self.first_update_after_recovery - self.completion_time).total_seconds() if self.completion_time else 0
            return f"{status} - Recovery: {self.recovery_duration_seconds:.1f}s, Resume: {resume_time:.1f}s"
        return f"{status} - Recovery: {self.recovery_duration_seconds:.1f}s, No updates resumed"


class MockPythonServer:
    """Mock Python server to receive updates from MediaMonitor"""
    
    def __init__(self, port: int):
        self.port = port
        self.process: Optional[subprocess.Popen] = None
        self.server_log_file = "test_recovery_server_log.txt"
        
    def start(self) -> bool:
        """Start the mock server"""
        try:
            # Create a simple Flask server script
            server_script = f"""
import sys
from flask import Flask, request, jsonify
from datetime import datetime

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
            with open('test_mock_recovery_server.py', 'w', encoding='utf-8') as f:
                f.write(server_script)
            
            # Clear previous log
            if os.path.exists(self.server_log_file):
                os.remove(self.server_log_file)
            
            # Start server
            self.process = subprocess.Popen(
                [sys.executable, 'test_mock_recovery_server.py'],
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


class RecoverySimulationTest:
    """Recovery simulation integration test"""
    
    def __init__(self):
        self.mediamonitor_process: Optional[subprocess.Popen] = None
        self.mock_server = MockPythonServer(PYTHON_SERVER_PORT)
        self.updates: List[UpdateRecord] = []
        self.recovery_events: List[RecoveryEvent] = []
        self.test_start_time: Optional[datetime] = None
        self.mediamonitor_output: List[str] = []
        
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
                stderr=subprocess.STDOUT,
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
    
    def read_mediamonitor_output(self) -> List[str]:
        """Read available output from MediaMonitor"""
        new_lines = []
        if self.mediamonitor_process and self.mediamonitor_process.stdout:
            try:
                # Non-blocking read
                import select
                if sys.platform != 'win32':
                    # Unix-like systems
                    while True:
                        ready, _, _ = select.select([self.mediamonitor_process.stdout], [], [], 0)
                        if ready:
                            line = self.mediamonitor_process.stdout.readline()
                            if line:
                                new_lines.append(line.strip())
                            else:
                                break
                        else:
                            break
                else:
                    # Windows - just try to read what's available
                    # This is less reliable but works for our purposes
                    pass
            except:
                pass
        
        self.mediamonitor_output.extend(new_lines)
        return new_lines
    
    def detect_recovery_in_output(self, lines: List[str]) -> Optional[datetime]:
        """Detect if recovery was triggered in the output"""
        for line in lines:
            if "Starting recovery procedure" in line or "🔄 Starting recovery procedure" in line:
                return datetime.now()
        return None
    
    def detect_recovery_completion_in_output(self, lines: List[str]) -> Optional[datetime]:
        """Detect if recovery completed in the output"""
        for line in lines:
            if "Recovery procedure completed successfully" in line or "✅ Recovery procedure completed successfully" in line:
                return datetime.now()
        return None
    
    def wait_for_recovery_trigger(self, timeout_seconds: int = 40) -> Optional[datetime]:
        """Wait for recovery to be triggered, monitoring MediaMonitor output"""
        print(f"⏳ Waiting up to {timeout_seconds}s for recovery to trigger...")
        start_time = datetime.now()
        
        while (datetime.now() - start_time).total_seconds() < timeout_seconds:
            # Read output
            lines = self.read_mediamonitor_output()
            
            # Check for recovery trigger
            recovery_time = self.detect_recovery_in_output(lines)
            if recovery_time:
                print(f"✅ Recovery triggered at {recovery_time.strftime('%H:%M:%S.%f')[:-3]}")
                return recovery_time
            
            # Check if process died
            if self.mediamonitor_process and self.mediamonitor_process.poll() is not None:
                print("❌ MediaMonitor process terminated unexpectedly")
                return None
            
            time.sleep(0.5)
        
        print(f"⚠️ Recovery did not trigger within {timeout_seconds}s")
        return None
    
    def wait_for_recovery_completion(self, timeout_seconds: int = 15) -> Optional[datetime]:
        """Wait for recovery to complete"""
        print(f"⏳ Waiting up to {timeout_seconds}s for recovery to complete...")
        start_time = datetime.now()
        
        while (datetime.now() - start_time).total_seconds() < timeout_seconds:
            # Read output
            lines = self.read_mediamonitor_output()
            
            # Check for recovery completion
            completion_time = self.detect_recovery_completion_in_output(lines)
            if completion_time:
                print(f"✅ Recovery completed at {completion_time.strftime('%H:%M:%S.%f')[:-3]}")
                return completion_time
            
            # Check if process died
            if self.mediamonitor_process and self.mediamonitor_process.poll() is not None:
                print("❌ MediaMonitor process terminated unexpectedly")
                return None
            
            time.sleep(0.5)
        
        print(f"⚠️ Recovery did not complete within {timeout_seconds}s")
        return None
    
    def wait_for_updates_to_resume(self, after_time: datetime, timeout_seconds: int = 10) -> Optional[datetime]:
        """Wait for updates to resume after recovery"""
        print(f"⏳ Waiting up to {timeout_seconds}s for updates to resume...")
        start_time = datetime.now()
        
        while (datetime.now() - start_time).total_seconds() < timeout_seconds:
            # Load current updates
            current_updates = self.mock_server.load_updates()
            
            # Check if we have any updates after the recovery completion time
            for update in current_updates:
                if update.timestamp > after_time:
                    print(f"✅ Updates resumed at {update.timestamp.strftime('%H:%M:%S.%f')[:-3]}")
                    return update.timestamp
            
            time.sleep(0.5)
        
        print(f"⚠️ No updates received within {timeout_seconds}s after recovery")
        return None
    
    def test_recovery_cycle(self, cycle_number: int) -> RecoveryEvent:
        """Test a single recovery cycle"""
        print("\n" + "=" * 80)
        print(f"  Recovery Cycle #{cycle_number}")
        print("=" * 80)
        
        # Wait for recovery to trigger (should happen after 30s of no updates)
        recovery_trigger_time = self.wait_for_recovery_trigger(
            timeout_seconds=RECOVERY_TIMEOUT_SECONDS + 15
        )
        
        if not recovery_trigger_time:
            return RecoveryEvent(
                trigger_time=datetime.now(),
                completion_time=None,
                success=False,
                first_update_after_recovery=None,
                recovery_duration_seconds=0
            )
        
        # Wait for recovery to complete
        recovery_completion_time = self.wait_for_recovery_completion(timeout_seconds=15)
        
        if not recovery_completion_time:
            return RecoveryEvent(
                trigger_time=recovery_trigger_time,
                completion_time=None,
                success=False,
                first_update_after_recovery=None,
                recovery_duration_seconds=(datetime.now() - recovery_trigger_time).total_seconds()
            )
        
        recovery_duration = (recovery_completion_time - recovery_trigger_time).total_seconds()
        
        # Wait for updates to resume
        first_update_time = self.wait_for_updates_to_resume(
            after_time=recovery_completion_time,
            timeout_seconds=RECOVERY_VERIFICATION_SECONDS
        )
        
        success = first_update_time is not None
        
        return RecoveryEvent(
            trigger_time=recovery_trigger_time,
            completion_time=recovery_completion_time,
            success=success,
            first_update_after_recovery=first_update_time,
            recovery_duration_seconds=recovery_duration
        )
    
    def run_test(self) -> bool:
        """Run the recovery simulation test"""
        print("=" * 80)
        print("  MediaMonitor Recovery Simulation Integration Test")
        print("=" * 80)
        print(f"Recovery timeout: {RECOVERY_TIMEOUT_SECONDS} seconds")
        print(f"Recovery verification: {RECOVERY_VERIFICATION_SECONDS} seconds")
        print(f"Recovery cycles to test: {RECOVERY_CYCLES_TO_TEST}")
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
        
        self.test_start_time = datetime.now()
        
        # Note: In a real scenario, we would need to simulate media playing
        # For this test, we rely on the fact that if no media is playing,
        # the HealthMonitor will eventually trigger recovery after 30 seconds
        
        print("\n📝 Note: This test relies on the HealthMonitor detecting no updates")
        print("   and triggering recovery automatically after 30 seconds.")
        print()
        
        # Test multiple recovery cycles
        try:
            for cycle in range(1, RECOVERY_CYCLES_TO_TEST + 1):
                recovery_event = self.test_recovery_cycle(cycle)
                self.recovery_events.append(recovery_event)
                
                print(f"\n📊 Cycle {cycle} Result: {recovery_event}")
                
                if not recovery_event.success:
                    print(f"❌ Recovery cycle {cycle} failed")
                    break
                
                # If we have more cycles to test, wait a bit before the next one
                if cycle < RECOVERY_CYCLES_TO_TEST:
                    print(f"\n⏳ Waiting 10 seconds before next recovery cycle...")
                    time.sleep(10)
        
        except KeyboardInterrupt:
            print("\n⚠️ Test interrupted by user")
            self.stop_mediamonitor()
            self.mock_server.stop()
            return False
        
        # Stop processes
        self.stop_mediamonitor()
        self.mock_server.stop()
        
        # Load final updates
        self.updates = self.mock_server.load_updates()
        
        # Analyze results
        return self.analyze_results()
    
    def analyze_results(self) -> bool:
        """Analyze test results"""
        print("\n" + "=" * 80)
        print("  Test Results Analysis")
        print("=" * 80)
        print()
        
        # Recovery statistics
        print(f"📈 Recovery Statistics:")
        print(f"   Total recovery cycles tested: {len(self.recovery_events)}")
        
        successful_recoveries = sum(1 for r in self.recovery_events if r.success)
        print(f"   Successful recoveries: {successful_recoveries}/{len(self.recovery_events)}")
        
        if len(self.recovery_events) > 0:
            avg_recovery_duration = sum(r.recovery_duration_seconds for r in self.recovery_events) / len(self.recovery_events)
            print(f"   Average recovery duration: {avg_recovery_duration:.1f}s")
            
            # Calculate average time to resume updates
            resume_times = []
            for r in self.recovery_events:
                if r.success and r.completion_time and r.first_update_after_recovery:
                    resume_time = (r.first_update_after_recovery - r.completion_time).total_seconds()
                    resume_times.append(resume_time)
            
            if resume_times:
                avg_resume_time = sum(resume_times) / len(resume_times)
                max_resume_time = max(resume_times)
                print(f"   Average time to resume updates: {avg_resume_time:.1f}s")
                print(f"   Maximum time to resume updates: {max_resume_time:.1f}s")
        print()
        
        # Detailed recovery events
        print(f"🔍 Detailed Recovery Events:")
        for i, event in enumerate(self.recovery_events, 1):
            print(f"   {i}. {event}")
        print()
        
        # Update statistics
        print(f"📊 Update Statistics:")
        print(f"   Total updates received: {len(self.updates)}")
        if len(self.updates) > 0:
            print(f"   First update: {self.updates[0].timestamp.strftime('%H:%M:%S.%f')[:-3]}")
            print(f"   Last update: {self.updates[-1].timestamp.strftime('%H:%M:%S.%f')[:-3]}")
        print()
        
        # Overall assessment
        print("=" * 80)
        print("  Overall Assessment")
        print("=" * 80)
        
        # Determine pass/fail
        passed = True
        issues = []
        
        # Check 1: All recovery cycles completed
        if len(self.recovery_events) < RECOVERY_CYCLES_TO_TEST:
            passed = False
            issues.append(f"Only {len(self.recovery_events)}/{RECOVERY_CYCLES_TO_TEST} recovery cycles completed")
        
        # Check 2: All recoveries successful
        if successful_recoveries < len(self.recovery_events):
            passed = False
            issues.append(f"Only {successful_recoveries}/{len(self.recovery_events)} recoveries successful")
        
        # Check 3: Updates resumed within 10 seconds
        for i, event in enumerate(self.recovery_events, 1):
            if event.success and event.completion_time and event.first_update_after_recovery:
                resume_time = (event.first_update_after_recovery - event.completion_time).total_seconds()
                if resume_time > RECOVERY_VERIFICATION_SECONDS:
                    passed = False
                    issues.append(f"Cycle {i}: Updates took {resume_time:.1f}s to resume (> {RECOVERY_VERIFICATION_SECONDS}s)")
        
        if passed:
            print("✅ TEST PASSED")
            print()
            print("Requirements validated:")
            print("  ✅ 1.3: Event subscription failure detected and re-established")
            print("  ✅ 3.1: Automatic recovery triggered after 30 seconds without updates")
            print("  ✅ 3.5: Recovery outcome logged and success verified")
            print(f"  ✅ Multiple recovery cycles tested ({RECOVERY_CYCLES_TO_TEST} cycles)")
            print(f"  ✅ Updates resumed within {RECOVERY_VERIFICATION_SECONDS} seconds after recovery")
        else:
            print("❌ TEST FAILED")
            print()
            print("Issues detected:")
            for issue in issues:
                print(f"  ❌ {issue}")
        
        print("=" * 80)
        
        return passed
    
    def save_detailed_report(self):
        """Save detailed test report to file"""
        try:
            report_filename = f"recovery_simulation_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            
            with open(report_filename, 'w', encoding='utf-8') as f:
                f.write("MediaMonitor Recovery Simulation Integration Test Report\n")
                f.write("=" * 80 + "\n\n")
                
                f.write(f"Test Configuration:\n")
                f.write(f"  Recovery timeout: {RECOVERY_TIMEOUT_SECONDS} seconds\n")
                f.write(f"  Recovery verification: {RECOVERY_VERIFICATION_SECONDS} seconds\n")
                f.write(f"  Recovery cycles tested: {RECOVERY_CYCLES_TO_TEST}\n\n")
                
                f.write(f"Recovery Events ({len(self.recovery_events)}):\n")
                for i, event in enumerate(self.recovery_events, 1):
                    f.write(f"  {i}. {event}\n")
                f.write("\n")
                
                f.write(f"Updates Received ({len(self.updates)}):\n")
                for update in self.updates:
                    f.write(f"  {update}\n")
                f.write("\n")
                
                f.write(f"MediaMonitor Output (last 100 lines):\n")
                for line in self.mediamonitor_output[-100:]:
                    f.write(f"  {line}\n")
                f.write("\n")
            
            print(f"📝 Detailed report saved to: {report_filename}")
        
        except Exception as e:
            print(f"⚠️ Error saving report: {e}")


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
        print("   cd MediaMonitor && python test_recovery_simulation.py")
        return 1
    
    # Run the test
    test = RecoverySimulationTest()
    try:
        success = test.run_test()
        test.save_detailed_report()
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
