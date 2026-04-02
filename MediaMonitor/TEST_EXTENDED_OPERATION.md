# Extended Operation Integration Test

## Overview

This test validates that MediaMonitor maintains continuous operation over extended periods without degradation in event subscription health or memory leaks.

## Requirements Validated

- **1.2**: Maintains active event subscriptions without degradation
- **6.1**: Simulates extended operation periods (30 minutes)
- **6.2**: Verifies continuous track update flow
- **6.3**: Injects simulated media changes at regular intervals (every 30 seconds)
- **6.4**: Detects gaps in update flow exceeding 5 seconds
- **6.5**: Reports successful updates and detected gaps

## Test Files

### test_extended_operation.py
Full 30-minute integration test as specified in requirements.

**Configuration:**
- Duration: 30 minutes
- Media change simulation: Every 30 seconds
- Maximum acceptable gap: 5 seconds
- Memory check interval: 60 seconds
- Memory leak threshold: 50 MB growth

### test_extended_operation_quick.py
Shortened 2-minute version for rapid testing and development.

**Configuration:**
- Duration: 2 minutes
- Media change simulation: Every 10 seconds
- Maximum acceptable gap: 5 seconds
- Memory check interval: 20 seconds
- Memory leak threshold: 50 MB growth

## Prerequisites

Install required Python packages:

```bash
pip install flask psutil requests
```

## Running the Tests

### Full Test (30 minutes)

```bash
cd MediaMonitor
python test_extended_operation.py
```

This will:
1. Build MediaMonitor in Release configuration
2. Start a mock Python server on port 8080
3. Start MediaMonitor with diagnostic mode enabled
4. Run for 30 minutes, monitoring updates and memory
5. Generate a detailed report

### Quick Test (2 minutes)

```bash
cd MediaMonitor
python test_extended_operation_quick.py
```

Use this for rapid validation during development.

## Test Architecture

### Components

1. **MockPythonServer**: Simulates the Python server that receives updates from MediaMonitor
   - Listens on port 8080
   - Logs all received updates to a file
   - Provides `/update`, `/config`, and `/sources` endpoints

2. **ExtendedOperationTest**: Main test orchestrator
   - Starts and manages MediaMonitor process
   - Monitors memory usage
   - Collects and analyzes updates
   - Detects gaps in update flow
   - Generates test reports

### What the Test Measures

1. **Update Continuity**: Verifies that updates are received continuously throughout the test period

2. **Gap Detection**: Identifies any gaps in update flow exceeding 5 seconds
   - Gaps indicate potential event subscription failures
   - Should be zero for a passing test

3. **Memory Stability**: Monitors memory usage over time
   - Takes snapshots at regular intervals
   - Detects memory growth exceeding threshold
   - Identifies potential memory leaks

4. **Process Stability**: Ensures MediaMonitor stays running
   - Detects unexpected terminations
   - Validates graceful shutdown

## Test Output

### Console Output

The test provides real-time progress updates:
- Build status
- Server startup
- MediaMonitor startup
- Periodic progress updates with elapsed time
- Memory snapshots
- Final analysis and results

### Detailed Report

A detailed report file is generated: `extended_operation_report_YYYYMMDD_HHMMSS.txt`

Contains:
- Test configuration
- All received updates with timestamps
- All detected gaps
- Memory snapshots over time

### Log Files

- `test_server_log.txt` (or `test_server_log_quick.txt`): Raw update log from mock server
- `logs/mediamonitor_diagnostic_*.log`: MediaMonitor diagnostic logs (if diagnostic mode enabled)

## Interpreting Results

### Passing Test

```
✅ TEST PASSED

Requirements validated:
  ✅ 1.2: Event subscriptions maintained without degradation
  ✅ 6.1: Extended operation period completed (30 minutes)
  ✅ 6.2: Continuous update flow verified
  ✅ 6.3: Media changes simulated at regular intervals
  ✅ 6.4: No gaps exceeding 5 seconds detected
  ✅ 6.5: Update count and gaps reported
```

### Failing Test

```
❌ TEST FAILED

Issues detected:
  ❌ No updates received during test
  ❌ 3 gaps exceeding 5 seconds detected
  ❌ Potential memory leak detected
```

## Troubleshooting

### No Updates Received

**Possible causes:**
- No media is actually playing in Windows
- MediaMonitor failed to subscribe to events
- Mock server not receiving requests

**Solutions:**
- Play some media (Spotify, YouTube, etc.) during the test
- Check MediaMonitor diagnostic logs for subscription errors
- Verify mock server is running on port 8080

### Gaps Detected

**Possible causes:**
- Event subscription degradation (the issue this feature aims to fix)
- System resource constraints
- Network issues between MediaMonitor and mock server

**Solutions:**
- Review diagnostic logs around gap timestamps
- Check system resource usage during test
- Verify recovery mechanism is working

### Memory Leak Detected

**Possible causes:**
- Event handlers not being properly cleaned up
- Resources not being disposed
- Accumulating data structures

**Solutions:**
- Review component disposal in MediaMonitor
- Check for event handler leaks
- Verify all IDisposable resources are properly disposed

### Process Terminated Unexpectedly

**Possible causes:**
- Unhandled exception in MediaMonitor
- System killed the process
- Build errors

**Solutions:**
- Check MediaMonitor stderr output
- Review diagnostic logs
- Verify build completed successfully

## Notes

### Simulated vs Real Media Changes

The current test simulates media changes by simply waiting for intervals. In a real scenario:
- Media would actually be playing and changing in Windows
- MediaMonitor would receive real events from Windows Media API
- Updates would be triggered by actual media state changes

For the most realistic test, play media that changes tracks during the test period.

### Test Duration

The 30-minute duration is chosen to:
- Allow sufficient time for event subscription issues to manifest
- Provide enough data points for memory leak detection
- Match typical user session lengths

### Quick Test Limitations

The 2-minute quick test:
- May not catch issues that only appear after extended operation
- Has fewer data points for analysis
- Is useful for rapid iteration but not for final validation

Always run the full 30-minute test before considering the feature complete.

## Integration with CI/CD

To integrate this test into CI/CD:

```bash
# Run quick test in CI
cd MediaMonitor
python test_extended_operation_quick.py

# Run full test nightly
cd MediaMonitor
python test_extended_operation.py
```

Exit codes:
- `0`: Test passed
- `1`: Test failed or error occurred

## Future Enhancements

Potential improvements to the test:

1. **Actual Media Simulation**: Use Windows Media API to programmatically control media playback
2. **Stress Testing**: Add concurrent operations or high-frequency changes
3. **Network Failure Simulation**: Test recovery from HTTP failures
4. **Multiple Sources**: Test source switching during operation
5. **Performance Metrics**: Add CPU usage monitoring alongside memory

## Related Tests

- `test_cpu_stability.py`: Tests CPU usage stability over 1 hour
- `test_diagnostic_integration.py`: Tests diagnostic mode functionality
- `test_diagnostic_mode.py`: Validates diagnostic logging implementation
