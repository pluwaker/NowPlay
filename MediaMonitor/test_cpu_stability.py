"""
Integration test for MediaMonitor long-running CPU stability
Tests that CPU usage remains stable over 1 hour of continuous operation
"""
import subprocess
import psutil
import time
import sys
import os
from datetime import datetime, timedelta
from typing import List, Tuple

# Test configuration
TEST_DURATION_MINUTES = 60  # 1 hour
MEASUREMENT_INTERVAL_MINUTES = 5  # Measure every 5 minutes
CPU_VARIANCE_THRESHOLD = 2.0  # Maximum 2% variance from baseline
WARMUP_SECONDS = 30  # Allow 30 seconds for warmup before baseline measurement

class CPUStabilityTest:
    def __init__(self):
        self.process = None
        self.measurements: List[Tuple[datetime, float]] = []
        self.baseline_cpu = 0.0
        
    def start_mediamonitor(self) -> bool:
        """Start MediaMonitor process with diagnostic mode enabled"""
        try:
            # Build the MediaMonitor project first
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
            print("🚀 Starting MediaMonitor with diagnostic mode...")
            self.process = subprocess.Popen(
                ["dotnet", "run", "--configuration", "Release", "--", "--diagnostic"],
                cwd=".",
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1
            )
            
            # Wait a moment to ensure process started
            time.sleep(2)
            
            if self.process.poll() is not None:
                print(f"❌ MediaMonitor failed to start")
                return False
            
            print(f"✅ MediaMonitor started (PID: {self.process.pid})")
            return True
            
        except Exception as e:
            print(f"❌ Error starting MediaMonitor: {e}")
            return False
    
    def get_cpu_usage(self) -> float:
        """Get current CPU usage of MediaMonitor process"""
        try:
            if self.process is None:
                return 0.0
            
            # Get process object
            proc = psutil.Process(self.process.pid)
            
            # Measure CPU over 1 second interval
            cpu_percent = proc.cpu_percent(interval=1.0)
            
            return cpu_percent
            
        except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
            print(f"⚠️ Error measuring CPU: {e}")
            return 0.0
    
    def measure_baseline(self) -> bool:
        """Measure baseline CPU after warmup period"""
        print(f"\n⏳ Warming up for {WARMUP_SECONDS} seconds...")
        time.sleep(WARMUP_SECONDS)
        
        print("📊 Measuring baseline CPU usage...")
        # Take 3 measurements and average them
        samples = []
        for i in range(3):
            cpu = self.get_cpu_usage()
            samples.append(cpu)
            print(f"   Sample {i+1}: {cpu:.2f}%")
            time.sleep(1)
        
        self.baseline_cpu = sum(samples) / len(samples)
        print(f"✅ Baseline CPU: {self.baseline_cpu:.2f}%\n")
        
        # Record baseline measurement
        self.measurements.append((datetime.now(), self.baseline_cpu))
        
        return True
    
    def run_test(self) -> bool:
        """Run the 1-hour CPU stability test"""
        print("=" * 70)
        print("  MediaMonitor CPU Stability Test")
        print("=" * 70)
        print(f"Duration: {TEST_DURATION_MINUTES} minutes")
        print(f"Measurement interval: {MEASUREMENT_INTERVAL_MINUTES} minutes")
        print(f"CPU variance threshold: ±{CPU_VARIANCE_THRESHOLD}%")
        print("=" * 70)
        print()
        
        # Start MediaMonitor
        if not self.start_mediamonitor():
            return False
        
        # Measure baseline
        if not self.measure_baseline():
            self.stop_mediamonitor()
            return False
        
        # Calculate number of measurements
        num_measurements = TEST_DURATION_MINUTES // MEASUREMENT_INTERVAL_MINUTES
        
        print(f"🔬 Starting {num_measurements} measurements over {TEST_DURATION_MINUTES} minutes...")
        print()
        
        # Run measurements
        start_time = datetime.now()
        for i in range(num_measurements):
            # Wait for measurement interval
            print(f"⏳ Waiting {MEASUREMENT_INTERVAL_MINUTES} minutes until next measurement...")
            time.sleep(MEASUREMENT_INTERVAL_MINUTES * 60)
            
            # Check if process is still running
            if self.process.poll() is not None:
                print("❌ MediaMonitor process terminated unexpectedly")
                return False
            
            # Measure CPU
            cpu = self.get_cpu_usage()
            timestamp = datetime.now()
            self.measurements.append((timestamp, cpu))
            
            # Calculate variance from baseline
            variance = cpu - self.baseline_cpu
            elapsed = (timestamp - start_time).total_seconds() / 60
            
            print(f"📊 Measurement {i+1}/{num_measurements} (at {elapsed:.1f} min):")
            print(f"   CPU: {cpu:.2f}% (baseline: {self.baseline_cpu:.2f}%)")
            print(f"   Variance: {variance:+.2f}%")
            
            # Check if variance exceeds threshold
            if abs(variance) > CPU_VARIANCE_THRESHOLD:
                print(f"   ⚠️ WARNING: Variance exceeds threshold of ±{CPU_VARIANCE_THRESHOLD}%")
            else:
                print(f"   ✅ Within acceptable range")
            print()
        
        # Stop MediaMonitor
        self.stop_mediamonitor()
        
        # Analyze results
        return self.analyze_results()
    
    def stop_mediamonitor(self):
        """Stop MediaMonitor process gracefully"""
        if self.process is None:
            return
        
        print("🛑 Stopping MediaMonitor...")
        try:
            # Try graceful termination first
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                # Force kill if graceful termination fails
                self.process.kill()
                self.process.wait()
            
            print("✅ MediaMonitor stopped")
        except Exception as e:
            print(f"⚠️ Error stopping MediaMonitor: {e}")
    
    def analyze_results(self) -> bool:
        """Analyze test results and determine pass/fail"""
        print("=" * 70)
        print("  Test Results Analysis")
        print("=" * 70)
        print()
        
        if len(self.measurements) < 2:
            print("❌ Insufficient measurements collected")
            return False
        
        # Calculate statistics
        cpu_values = [cpu for _, cpu in self.measurements]
        min_cpu = min(cpu_values)
        max_cpu = max(cpu_values)
        avg_cpu = sum(cpu_values) / len(cpu_values)
        
        # Calculate variance from baseline
        variances = [cpu - self.baseline_cpu for _, cpu in self.measurements[1:]]  # Exclude baseline itself
        max_variance = max(abs(v) for v in variances)
        
        print(f"Baseline CPU: {self.baseline_cpu:.2f}%")
        print(f"Average CPU: {avg_cpu:.2f}%")
        print(f"Min CPU: {min_cpu:.2f}%")
        print(f"Max CPU: {max_cpu:.2f}%")
        print(f"Max variance from baseline: {max_variance:.2f}%")
        print()
        
        # Print all measurements
        print("Detailed measurements:")
        for i, (timestamp, cpu) in enumerate(self.measurements):
            variance = cpu - self.baseline_cpu
            elapsed = (timestamp - self.measurements[0][0]).total_seconds() / 60
            print(f"  {i}. {timestamp.strftime('%H:%M:%S')} (t+{elapsed:5.1f}m): {cpu:5.2f}% ({variance:+.2f}%)")
        print()
        
        # Determine pass/fail
        if max_variance <= CPU_VARIANCE_THRESHOLD:
            print("=" * 70)
            print(f"✅ TEST PASSED")
            print(f"   CPU variance ({max_variance:.2f}%) is within threshold (±{CPU_VARIANCE_THRESHOLD}%)")
            print("=" * 70)
            return True
        else:
            print("=" * 70)
            print(f"❌ TEST FAILED")
            print(f"   CPU variance ({max_variance:.2f}%) exceeds threshold (±{CPU_VARIANCE_THRESHOLD}%)")
            print("=" * 70)
            return False
    
    def save_diagnostic_logs(self):
        """Save diagnostic output to file for analysis"""
        if self.process is None:
            return
        
        try:
            log_filename = f"cpu_test_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            with open(log_filename, 'w', encoding='utf-8') as f:
                f.write("MediaMonitor CPU Stability Test - Diagnostic Output\n")
                f.write("=" * 70 + "\n\n")
                
                # Write measurements
                f.write("CPU Measurements:\n")
                for timestamp, cpu in self.measurements:
                    variance = cpu - self.baseline_cpu
                    f.write(f"{timestamp.strftime('%Y-%m-%d %H:%M:%S')}: {cpu:.2f}% ({variance:+.2f}%)\n")
                
                f.write("\n")
            
            print(f"📝 Diagnostic logs saved to: {log_filename}")
        except Exception as e:
            print(f"⚠️ Error saving diagnostic logs: {e}")

def main():
    """Main entry point for CPU stability test"""
    # Check if psutil is installed
    try:
        import psutil
    except ImportError:
        print("❌ Error: psutil module not found")
        print("   Install it with: pip install psutil")
        return 1
    
    # Check if we're in the MediaMonitor directory
    if not os.path.exists("MediaMonitor.csproj"):
        print("❌ Error: Must run this test from the MediaMonitor directory")
        print("   cd MediaMonitor && python test_cpu_stability.py")
        return 1
    
    # Run the test
    test = CPUStabilityTest()
    try:
        success = test.run_test()
        test.save_diagnostic_logs()
        return 0 if success else 1
    except KeyboardInterrupt:
        print("\n⚠️ Test interrupted by user")
        test.stop_mediamonitor()
        return 1
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        test.stop_mediamonitor()
        return 1

if __name__ == "__main__":
    sys.exit(main())
