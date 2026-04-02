# MediaMonitor CPU Stability Tests

This directory contains integration tests for verifying MediaMonitor's CPU stability over extended periods.

## Prerequisites

1. **Python 3.7+** with the following packages:
   ```bash
   pip install psutil
   ```

2. **.NET SDK** (already required for MediaMonitor)

3. **Python server running** (optional but recommended for realistic testing):
   ```bash
   python main.py
   ```

## Test: Long-Running CPU Stability

**File:** `test_cpu_stability.py`

**Purpose:** Verifies that MediaMonitor maintains stable CPU usage over 1 hour of continuous operation.

**Requirements tested:** Requirement 1.1 - CPU usage within 2% variance of baseline after 1 hour

### How to Run

```bash
cd MediaMonitor
python test_cpu_stability.py
```

### Test Parameters

- **Duration:** 60 minutes (1 hour)
- **Measurement interval:** Every 5 minutes
- **Baseline measurement:** After 30-second warmup
- **Pass criteria:** CPU variance ≤ 2% from baseline

### What the Test Does

1. Builds MediaMonitor in Release configuration
2. Starts MediaMonitor with `--diagnostic` flag enabled
3. Waits 30 seconds for warmup
4. Measures baseline CPU usage (average of 3 samples)
5. Takes CPU measurements every 5 minutes for 1 hour
6. Calculates variance from baseline for each measurement
7. Reports pass/fail based on 2% variance threshold
8. Saves diagnostic logs to file

### Expected Output

```
======================================================================
  MediaMonitor CPU Stability Test
======================================================================
Duration: 60 minutes
Measurement interval: 5 minutes
CPU variance threshold: ±2.0%
======================================================================

🔨 Building MediaMonitor...
✅ Build successful
🚀 Starting MediaMonitor with diagnostic mode...
✅ MediaMonitor started (PID: 12345)

⏳ Warming up for 30 seconds...
📊 Measuring baseline CPU usage...
   Sample 1: 1.85%
   Sample 2: 1.92%
   Sample 3: 1.88%
✅ Baseline CPU: 1.88%

🔬 Starting 12 measurements over 60 minutes...

⏳ Waiting 5 minutes until next measurement...
📊 Measurement 1/12 (at 5.0 min):
   CPU: 1.95% (baseline: 1.88%)
   Variance: +0.07%
   ✅ Within acceptable range

[... more measurements ...]

======================================================================
  Test Results Analysis
======================================================================

Baseline CPU: 1.88%
Average CPU: 1.92%
Min CPU: 1.85%
Max CPU: 2.15%
Max variance from baseline: 0.27%

Detailed measurements:
  0. 14:30:45 (t+  0.0m):  1.88% (+0.00%)
  1. 14:35:45 (t+  5.0m):  1.95% (+0.07%)
  2. 14:40:45 (t+ 10.0m):  1.89% (+0.01%)
  [...]

======================================================================
✅ TEST PASSED
   CPU variance (0.27%) is within threshold (±2.0%)
======================================================================

📝 Diagnostic logs saved to: cpu_test_log_20241114_143045.txt
```

### Interpreting Results

**PASS:** CPU variance stays within ±2% of baseline throughout the test
- Indicates proper resource cleanup and no memory/handle leaks
- MediaMonitor is stable for long-running operation

**FAIL:** CPU variance exceeds ±2% threshold
- Indicates potential resource leaks or accumulation issues
- Review diagnostic logs for patterns
- Check for:
  - Increasing session access counts
  - Growing HTTP request rates
  - Memory growth over time

### Diagnostic Logs

The test saves detailed logs to `cpu_test_log_YYYYMMDD_HHMMSS.txt` containing:
- All CPU measurements with timestamps
- Variance calculations
- Can be used for further analysis or graphing

### Customizing Test Parameters

Edit the constants at the top of `test_cpu_stability.py`:

```python
TEST_DURATION_MINUTES = 60  # Change test duration
MEASUREMENT_INTERVAL_MINUTES = 5  # Change measurement frequency
CPU_VARIANCE_THRESHOLD = 2.0  # Change pass/fail threshold
WARMUP_SECONDS = 30  # Change warmup period
```

### Troubleshooting

**"psutil module not found"**
```bash
pip install psutil
```

**"Must run this test from the MediaMonitor directory"**
```bash
cd MediaMonitor
python test_cpu_stability.py
```

**"Build failed"**
- Ensure .NET SDK is installed: `dotnet --version`
- Check for compilation errors in MediaMonitor.cs

**"MediaMonitor process terminated unexpectedly"**
- Check if Python server is running (recommended)
- Review MediaMonitor console output for errors
- Ensure no port conflicts (default: 8080)

**High baseline CPU (>5%)**
- Close other media applications
- Ensure system is not under heavy load
- Wait for system to stabilize before running test

## Test: High-Frequency Update Stress Test

**Files:** 
- `test_stress_high_frequency.py` (full 10-minute test)
- `test_stress_high_frequency_quick.py` (quick 2-minute test)

**Purpose:** Verifies that MediaMonitor can handle rapid media changes (every 2 seconds) without losing updates or becoming unresponsive.

**Requirements tested:** 
- 1.1: MediaMonitor detects and propagates track changes continuously
- 5.1: Debounce timer uses timeout when acquiring update lock
- 5.2: HTTP semaphore uses timeout to prevent indefinite blocking

### How to Run

Full test (10 minutes):
```bash
cd MediaMonitor
python test_stress_high_frequency.py
```

Quick test (2 minutes):
```bash
cd MediaMonitor
python test_stress_high_frequency_quick.py
```

### Test Parameters

**Full Test:**
- **Duration:** 10 minutes
- **Media change interval:** 2 seconds
- **Expected updates:** ~300
- **Pass criteria:** 
  - Update success rate ≥ 90%
  - No intervals > 10 seconds between updates
  - System remains responsive

**Quick Test:**
- **Duration:** 2 minutes
- **Media change interval:** 2 seconds
- **Expected updates:** ~60
- **Pass criteria:** Same as full test

### What the Test Does

1. Starts a mock Python server to receive updates
2. Builds and starts MediaMonitor with diagnostic mode
3. Simulates rapid media changes every 2 seconds
4. Monitors:
   - Update count and success rate
   - Inter-update intervals (responsiveness)
   - System resource usage (memory, CPU)
   - Timeout events (lock and HTTP timeouts)
5. Analyzes results and determines pass/fail
6. Saves detailed report to file

### Expected Output

```
================================================================================
  MediaMonitor High-Frequency Update Stress Test
================================================================================
Duration: 10 minutes
Media change interval: 2 seconds
Expected updates: ~300
================================================================================

🌐 Starting mock Python server...
✅ Mock server started on port 8080
🔨 Building MediaMonitor...
✅ Build successful
🚀 Starting MediaMonitor...
✅ MediaMonitor started (PID: 12345)
🎵 Starting media change simulator...
✅ Media simulator started (changes every 2s)
📊 Initial memory: 45.2 MB

🔬 Test running for 10 minutes...

⏱️  1.0 min elapsed:
   Simulated changes: 30
   Updates received: 28
   Memory: 46.1 MB
   CPU: 2.3%

[... more status updates ...]

================================================================================
  Test Results Analysis
================================================================================

📈 Update Statistics:
   Total updates received: 285
   Expected updates: ~300
   Update success rate: 95.0%
   Average update rate: 28.5 updates/minute

🔍 Lost Update Analysis:
   ✅ No lost updates detected (all sequence numbers consecutive)

⚡ System Responsiveness:
   Average inter-update interval: 2.11s
   Maximum inter-update interval: 3.45s
   Expected interval: 2s
   ✅ No significant delays detected

⏱️  Timeout Analysis:
   ✅ No timeouts detected

================================================================================
  Overall Assessment
================================================================================
✅ TEST PASSED

Requirements validated:
  ✅ 1.1: MediaMonitor detected and propagated track changes continuously
  ✅ 5.1: Debounce timer handled high-frequency updates without deadlock
  ✅ 5.2: HTTP semaphore prevented indefinite blocking
  ✅ Update success rate: 95.0%
  ✅ System remained responsive throughout test
================================================================================

📝 Detailed report saved to: stress_test_report_20241208_143045.txt
```

### Interpreting Results

**PASS:** 
- Update success rate ≥ 90%
- No intervals > 10 seconds
- System remained responsive
- Indicates proper handling of high-frequency updates

**FAIL:**
- Low success rate (< 90%) may indicate:
  - Debouncing too aggressive
  - Lock timeout issues
  - HTTP semaphore problems
- Long intervals (> 10s) may indicate:
  - Deadlock conditions
  - Resource exhaustion
  - System overload

### Detailed Report

The test saves a detailed report to `stress_test_report_YYYYMMDD_HHMMSS.txt` containing:
- Complete test configuration
- All updates received (first 100)
- All timeout events detected
- Full analysis results

See `TEST_STRESS_HIGH_FREQUENCY.md` for more details.

## Test: Extended Operation Test

**Files:**
- `test_extended_operation.py` (full 30-minute test)
- `test_extended_operation_quick.py` (quick 5-minute test)

**Purpose:** Verifies continuous operation for extended periods with simulated media changes.

**Requirements tested:**
- 1.2: Maintains active event subscriptions without degradation
- 6.1-6.5: Extended operation validation

See `TEST_EXTENDED_OPERATION.md` for details.

## Test: Recovery Simulation Test

**Files:**
- `test_recovery_simulation.py` (full test with multiple cycles)
- `test_recovery_simulation_quick.py` (quick single-cycle test)

**Purpose:** Tests automatic recovery from event subscription failures.

**Requirements tested:**
- 1.3: Detects event subscription failure and re-establishes subscriptions
- 3.1: Triggers automatic recovery after 30 seconds without updates
- 3.5: Logs recovery outcome and verifies success

See `TEST_RECOVERY_SIMULATION.md` for details.

## Future Tests

Additional tests planned (see tasks.md):

- **ConfigPoller isolation test** (Task 14)
  - Simulates ConfigPoller failures
  - Verifies media updates continue unaffected
  - Tests configuration sync after failures stop
