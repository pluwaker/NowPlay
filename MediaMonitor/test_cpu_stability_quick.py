"""
Quick CPU stability test for MediaMonitor (5-minute version)
Useful for rapid validation during development
"""
import sys
import os

# Import the main test class
from test_cpu_stability import CPUStabilityTest

# Override test parameters for quick testing
TEST_DURATION_MINUTES = 5  # 5 minutes instead of 60
MEASUREMENT_INTERVAL_MINUTES = 1  # Measure every 1 minute
CPU_VARIANCE_THRESHOLD = 2.0  # Same threshold
WARMUP_SECONDS = 10  # Shorter warmup

def main():
    """Run quick 5-minute CPU stability test"""
    print("🚀 Quick CPU Stability Test (5 minutes)")
    print("   This is a shortened version for rapid validation")
    print()
    
    # Check prerequisites
    try:
        import psutil
    except ImportError:
        print("❌ Error: psutil module not found")
        print("   Install it with: pip install psutil")
        return 1
    
    if not os.path.exists("MediaMonitor.csproj"):
        print("❌ Error: Must run this test from the MediaMonitor directory")
        return 1
    
    # Monkey-patch the test parameters
    import test_cpu_stability
    test_cpu_stability.TEST_DURATION_MINUTES = TEST_DURATION_MINUTES
    test_cpu_stability.MEASUREMENT_INTERVAL_MINUTES = MEASUREMENT_INTERVAL_MINUTES
    test_cpu_stability.CPU_VARIANCE_THRESHOLD = CPU_VARIANCE_THRESHOLD
    test_cpu_stability.WARMUP_SECONDS = WARMUP_SECONDS
    
    # Run the test
    test = CPUStabilityTest()
    try:
        success = test.run_test()
        test.save_diagnostic_logs()
        
        print()
        print("💡 Note: This was a quick 5-minute test.")
        print("   For full validation, run: python test_cpu_stability.py")
        
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
