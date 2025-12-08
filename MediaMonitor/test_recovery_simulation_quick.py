"""
Quick Recovery Simulation Test for MediaMonitor
Shorter version for rapid testing during development

This is a faster version that tests only 1 recovery cycle
For full testing, use test_recovery_simulation.py
"""

import subprocess
import sys
import os

# Import the main test class
from test_recovery_simulation import RecoverySimulationTest, RECOVERY_CYCLES_TO_TEST

# Override configuration for quick test
import test_recovery_simulation
test_recovery_simulation.RECOVERY_CYCLES_TO_TEST = 1  # Only test 1 cycle


def main():
    """Main entry point for quick test"""
    print("=" * 80)
    print("  QUICK Recovery Simulation Test (1 cycle)")
    print("  For full test, run: python test_recovery_simulation.py")
    print("=" * 80)
    print()
    
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
        print("   cd MediaMonitor && python test_recovery_simulation_quick.py")
        return 1
    
    # Run the test with modified configuration
    test = RecoverySimulationTest()
    try:
        success = test.run_test()
        test.save_detailed_report()
        
        print("\n" + "=" * 80)
        print("  Quick test completed!")
        print("  For comprehensive testing, run: python test_recovery_simulation.py")
        print("=" * 80)
        
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
