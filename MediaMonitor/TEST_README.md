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

## Future Tests

Additional tests planned (see tasks.md):

- **24-hour memory stability test** (Task 14)
  - Longer duration test
  - Monitors memory growth and handle count
  - Verifies no memory leaks over extended operation
