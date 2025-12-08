#!/usr/bin/env python3
"""
Integration test for diagnostic mode
Runs MediaMonitor briefly to verify log file creation
"""

import os
import subprocess
import time
import sys
import glob

def test_diagnostic_integration():
    """Run MediaMonitor with diagnostic mode and verify log file creation"""
    
    print("=" * 60)
    print("Diagnostic Mode Integration Test")
    print("=" * 60)
    
    # Clean up old logs
    if os.path.exists("logs"):
        print("Cleaning up old logs...")
        for f in glob.glob("logs/mediamonitor_diagnostic_*.log"):
            try:
                os.remove(f)
            except:
                pass
    
    exe_path = "bin/Debug/net6.0-windows10.0.19041.0/MediaMonitor.exe"
    
    if not os.path.exists(exe_path):
        print(f"❌ Executable not found: {exe_path}")
        print("   Run 'dotnet build' first")
        return False
    
    print(f"✅ Found executable: {exe_path}")
    print("\nStarting MediaMonitor with --diagnostic flag...")
    print("(Will run for 5 seconds then terminate)")
    
    try:
        # Start process with diagnostic mode
        process = subprocess.Popen(
            [exe_path, "--diagnostic"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            universal_newlines=True
        )
        
        # Capture output for 5 seconds
        output_lines = []
        start_time = time.time()
        
        while time.time() - start_time < 5:
            line = process.stdout.readline()
            if line:
                output_lines.append(line.strip())
                print(f"  {line.strip()}")
            time.sleep(0.1)
        
        # Terminate process
        print("\nTerminating process...")
        process.terminate()
        
        try:
            process.wait(timeout=3)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()
        
        print("\n" + "=" * 60)
        print("Verification")
        print("=" * 60)
        
        # Check output
        output_text = "\n".join(output_lines)
        
        checks = [
            ("🔍 Diagnostic mode enabled", "Diagnostic mode enabled message"),
            ("📝 Verbose logging active", "Verbose logging message"),
            ("📁 Log file will be created", "Log file creation message"),
        ]
        
        all_passed = True
        for check_str, description in checks:
            if check_str in output_text:
                print(f"✅ {description}")
            else:
                print(f"⚠️  {description} not found in output")
                all_passed = False
        
        # Check for log file
        if os.path.exists("logs"):
            log_files = glob.glob("logs/mediamonitor_diagnostic_*.log")
            if log_files:
                log_file = log_files[0]
                print(f"✅ Log file created: {log_file}")
                
                # Check log file content
                with open(log_file, 'r', encoding='utf-8') as f:
                    log_content = f.read()
                    
                    if log_content:
                        print(f"✅ Log file contains {len(log_content)} characters")
                        
                        # Check for diagnostic entries
                        if "[DiagnosticLogger]" in log_content:
                            print("✅ Log file contains DiagnosticLogger entries")
                        else:
                            print("⚠️  Log file missing DiagnosticLogger entries")
                            all_passed = False
                        
                        # Show first few lines
                        lines = log_content.split('\n')[:5]
                        print("\nFirst few log entries:")
                        for line in lines:
                            if line.strip():
                                print(f"  {line}")
                    else:
                        print("⚠️  Log file is empty")
                        all_passed = False
            else:
                print("⚠️  No log files found in logs directory")
                all_passed = False
        else:
            print("⚠️  Logs directory not created")
            all_passed = False
        
        print("\n" + "=" * 60)
        if all_passed:
            print("✅ Integration test PASSED")
            print("\nDiagnostic mode is working correctly:")
            print("  • Command-line flag parsing works")
            print("  • Console output formatting works")
            print("  • Log file creation works")
            print("  • Log file writing works")
        else:
            print("⚠️  Integration test completed with warnings")
        print("=" * 60)
        
        return all_passed
        
    except Exception as e:
        print(f"\n❌ Error during test: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    success = test_diagnostic_integration()
    sys.exit(0 if success else 1)
