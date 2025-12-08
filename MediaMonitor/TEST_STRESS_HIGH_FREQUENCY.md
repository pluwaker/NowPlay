# High-Frequency Update Stress Test

## Overview

This test validates that MediaMonitor can handle rapid media changes (every 2 seconds) for an extended period (10 minutes) without losing updates or becoming unresponsive.

## Test Files

- **test_stress_high_frequency.py** - Full 10-minute stress test
- **test_stress_high_frequency_quick.py** - Quick 2-minute version for development

## Requirements Validated

- **1.1**: MediaMonitor detects and propagates track changes continuously
- **5.1**: Debounce timer uses timeout when acquiring update lock (prevents deadlock)
- **5.2**: HTTP semaphore uses timeout to prevent indefinite blocking

## Test Configuration

### Full Test (test_stress_high_frequency.py)
- **Duration**: 10 minutes
- **Media change interval**: 2 seconds
- **Expected updates**: ~300 updates
- **Success criteria**:
  - Update success rate >= 90%
  - No intervals > 10 seconds between updates
  - System remains responsive throughout

### Quick Test (test_stress_high_frequency_quick.py)
- **Duration**: 2 minutes
- **Media change interval**: 2 seconds
- **Expected updates**: ~60 updates
- **Success criteria**: Same as full test

## How It Works

1. **Mock Python Server**: Starts a Flask server on port 8080 to receive updates
2. **MediaMonitor**: Starts with diagnostic mode enabled
3. **Media Simulator**: Tracks expected media changes (every 2 seconds)
4. **Monitoring**: Continuously monitors:
   - Update count and success rate
   - Inter-update intervals (responsiveness)
   - System resource usage (memory, CPU)
   - Timeout events (lock and HTTP timeouts)

## Running the Tests

### Prerequisites

```bash
pip install flask psutil requests
```

### Run Full Test (10 minutes)

```bash
cd MediaMonitor
python test_stress_high_frequency.py
```

### Run Quick Test (2 minutes)

```bash
cd MediaMonitor
python test_stress_high_frequency_quick.py
```

## Test Output

The test provides real-time status updates:

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
   Monitoring system responsiveness and update flow...

⏱️  1.0 min elapsed:
   Simulated changes: 30
   Updates received: 28
   Memory: 46.1 MB
   CPU: 2.3%

⏱️  2.0 min elapsed:
   Simulated changes: 60
   Updates received: 57
   Memory: 46.3 MB
   CPU: 2.1%

...
```

## Test Results

After completion, the test analyzes:

### Update Statistics
- Total updates received vs expected
- Update success rate (%)
- Average update rate (updates/minute)

### Lost Update Analysis
- Checks for gaps in sequence numbers
- Reports any lost updates

### System Responsiveness
- Average inter-update interval
- Maximum inter-update interval
- Identifies any long delays (> 3x expected interval)

### Timeout Analysis
- Lock acquisition timeouts
- HTTP semaphore timeouts

## Success Criteria

The test passes if:

1. ✅ Updates are received throughout the test
2. ✅ Update success rate >= 90% (allows for some debouncing)
3. ✅ No intervals > 10 seconds between updates (system remains responsive)
4. ✅ No critical timeouts that indicate deadlock

## Example Output

```
================================================================================
  Test Results Analysis
================================================================================

📈 Update Statistics:
   Total updates received: 285
   Expected updates: ~300
   Update success rate: 95.0%
   Average update rate: 28.5 updates/minute
   Expected update rate: 30.0 updates/minute

🔍 Lost Update Analysis:
   ✅ No lost updates detected (all sequence numbers consecutive)

⚡ System Responsiveness:
   Average inter-update interval: 2.11s
   Minimum inter-update interval: 1.98s
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
```

## Detailed Report

The test saves a detailed report to a timestamped file:
- `stress_test_report_YYYYMMDD_HHMMSS.txt`

This report includes:
- Complete test configuration
- All updates received (first 100)
- All timeout events detected
- Full analysis results

## Troubleshooting

### No Updates Received

If no updates are received:
1. Check that MediaMonitor built successfully
2. Verify the mock server started on port 8080
3. Check if Windows media is actually playing
4. Review MediaMonitor diagnostic output

### Low Success Rate

If success rate is < 90%:
1. This may indicate debouncing is too aggressive
2. Check for lock timeout messages in diagnostic output
3. Review HTTP semaphore timeout events
4. Consider system load (other processes competing for resources)

### System Unresponsive

If intervals > 10 seconds are detected:
1. Check for deadlock indicators in diagnostic output
2. Review lock acquisition timeout messages
3. Check system resource usage (CPU, memory)
4. Verify HTTP client pool is releasing semaphores

## Integration with CI/CD

The quick test (2 minutes) can be integrated into CI/CD pipelines:

```bash
# Run quick stress test as part of CI
cd MediaMonitor
python test_stress_high_frequency_quick.py
if [ $? -ne 0 ]; then
    echo "Stress test failed"
    exit 1
fi
```

The full test (10 minutes) is recommended for:
- Pre-release validation
- Performance regression testing
- Nightly builds

## Notes

- The test simulates rapid media changes but relies on MediaMonitor's internal update mechanism
- In a real scenario, Windows media would be changing every 2 seconds
- The test validates that the system can handle high-frequency updates without deadlock or data loss
- Some update loss (< 10%) is acceptable due to debouncing, which is designed to reduce HTTP request frequency
