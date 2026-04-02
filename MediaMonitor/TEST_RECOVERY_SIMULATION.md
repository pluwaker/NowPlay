# Recovery Simulation Integration Test

## Overview

This test validates the automatic recovery mechanism in MediaMonitor when event subscriptions fail or stop receiving updates.

## Prerequisites

1. **Python 3.7+** with the following packages:
   ```bash
   pip install psutil flask requests
   ```

2. **.NET SDK** (already required for MediaMonitor)

3. **No media playing**: The test relies on the HealthMonitor detecting no updates to trigger recovery

## Requirements Validated

- **1.3**: Event subscription failure detection and re-establishment
- **3.1**: Automatic recovery triggered after 30 seconds without updates
- **3.5**: Recovery outcome logging and success verification

## Test Design

### Test Strategy

The test simulates the scenario where MediaMonitor stops receiving track updates (which can happen when Windows Media API event subscriptions silently fail). It verifies that:

1. The HealthMonitor detects the lack of updates after 30 seconds
2. Recovery is automatically triggered
3. The RecoveryManager successfully re-establishes event subscriptions
4. Updates resume within 10 seconds after recovery completes
5. Multiple recovery cycles work correctly

### Test Components

1. **Mock Python Server**: Receives and logs updates from MediaMonitor
2. **MediaMonitor Process**: Runs with diagnostic mode enabled
3. **Output Monitor**: Watches MediaMonitor output for recovery events
4. **Update Tracker**: Monitors when updates are received

### Test Flow

```
1. Start Mock Python Server
2. Start MediaMonitor with diagnostic mode
3. For each recovery cycle:
   a. Wait for HealthMonitor to detect timeout (30s)
   b. Verify recovery procedure is triggered
   c. Wait for recovery to complete
   d. Verify updates resume within 10 seconds
4. Analyze results and generate report
```

## Running the Tests

### Full Test (2 Recovery Cycles)

```bash
cd MediaMonitor
python test_recovery_simulation.py
```

**Duration**: ~2-3 minutes per cycle (total ~5-6 minutes)

### Quick Test (1 Recovery Cycle)

```bash
cd MediaMonitor
python test_recovery_simulation_quick.py
```

**Duration**: ~2-3 minutes

## Test Configuration

| Parameter | Value | Description |
|-----------|-------|-------------|
| `RECOVERY_TIMEOUT_SECONDS` | 30 | Time without updates before recovery triggers |
| `RECOVERY_VERIFICATION_SECONDS` | 10 | Maximum time to wait for updates after recovery |
| `RECOVERY_CYCLES_TO_TEST` | 2 | Number of recovery cycles to test (full test) |
| `PYTHON_SERVER_PORT` | 8080 | Port for mock Python server |

## Expected Output

### Successful Test

```
================================================================================
  MediaMonitor Recovery Simulation Integration Test
================================================================================
Recovery timeout: 30 seconds
Recovery verification: 10 seconds
Recovery cycles to test: 2
================================================================================

🌐 Starting mock Python server...
✅ Mock server started on port 8080
🔨 Building MediaMonitor...
✅ Build successful
🚀 Starting MediaMonitor...
✅ MediaMonitor started (PID: 12345)

================================================================================
  Recovery Cycle #1
================================================================================
⏳ Waiting up to 45s for recovery to trigger...
✅ Recovery triggered at 12:34:56.789
⏳ Waiting up to 15s for recovery to complete...
✅ Recovery completed at 12:34:58.123
⏳ Waiting up to 10s for updates to resume...
✅ Updates resumed at 12:34:59.456

📊 Cycle 1 Result: ✅ SUCCESS - Recovery: 1.3s, Resume: 1.3s

⏳ Waiting 10 seconds before next recovery cycle...

================================================================================
  Recovery Cycle #2
================================================================================
⏳ Waiting up to 45s for recovery to trigger...
✅ Recovery triggered at 12:35:40.123
⏳ Waiting up to 15s for recovery to complete...
✅ Recovery completed at 12:35:41.456
⏳ Waiting up to 10s for updates to resume...
✅ Updates resumed at 12:35:42.789

📊 Cycle 2 Result: ✅ SUCCESS - Recovery: 1.3s, Resume: 1.3s

================================================================================
  Test Results Analysis
================================================================================

📈 Recovery Statistics:
   Total recovery cycles tested: 2
   Successful recoveries: 2/2
   Average recovery duration: 1.3s
   Average time to resume updates: 1.3s
   Maximum time to resume updates: 1.3s

🔍 Detailed Recovery Events:
   1. ✅ SUCCESS - Recovery: 1.3s, Resume: 1.3s
   2. ✅ SUCCESS - Recovery: 1.3s, Resume: 1.3s

================================================================================
  Overall Assessment
================================================================================
✅ TEST PASSED

Requirements validated:
  ✅ 1.3: Event subscription failure detected and re-established
  ✅ 3.1: Automatic recovery triggered after 30 seconds without updates
  ✅ 3.5: Recovery outcome logged and success verified
  ✅ Multiple recovery cycles tested (2 cycles)
  ✅ Updates resumed within 10 seconds after recovery
================================================================================
```

## Test Artifacts

After running the test, the following files are created:

1. **recovery_simulation_report_YYYYMMDD_HHMMSS.txt**: Detailed test report with all events and updates
2. **test_recovery_server_log.txt**: Raw update log from mock server
3. **test_mock_recovery_server.py**: Generated Flask server script (temporary)

## Troubleshooting

### Test Fails: Recovery Not Triggered

**Symptom**: Test times out waiting for recovery to trigger

**Possible Causes**:
- MediaMonitor is receiving updates (media is actually playing)
- HealthMonitor timeout is configured differently
- MediaMonitor process crashed

**Solution**:
- Ensure no media is playing in Windows
- Check MediaMonitor output for errors
- Verify HealthMonitor configuration in code

### Test Fails: Updates Don't Resume

**Symptom**: Recovery completes but no updates are received

**Possible Causes**:
- Recovery procedure failed to re-establish subscriptions
- No media sources available
- Mock server not receiving updates

**Solution**:
- Check MediaMonitor diagnostic output
- Verify mock server is running
- Check for errors in recovery procedure

### Test Fails: Process Crashes

**Symptom**: MediaMonitor process terminates unexpectedly

**Possible Causes**:
- Unhandled exception in recovery code
- Resource exhaustion
- Build issues

**Solution**:
- Check build output for errors
- Review MediaMonitor output for exceptions
- Check system resources (memory, CPU)

## Integration with CI/CD

This test can be integrated into CI/CD pipelines:

```yaml
# Example GitHub Actions workflow
- name: Run Recovery Simulation Test
  run: |
    cd MediaMonitor
    python test_recovery_simulation_quick.py
  timeout-minutes: 5
```

For comprehensive testing in nightly builds:

```yaml
# Example nightly test
- name: Run Full Recovery Simulation Test
  run: |
    cd MediaMonitor
    python test_recovery_simulation.py
  timeout-minutes: 10
```

## Limitations

1. **Simulated Failure**: The test relies on natural timeout (no media playing) rather than forcing event subscription failure
2. **Platform Dependent**: Requires Windows with Windows Media API
3. **Timing Sensitive**: Test timing may vary based on system load
4. **No Media Required**: Test doesn't require actual media playback

## Future Enhancements

Potential improvements for this test:

1. **Forced Failure Injection**: Modify MediaMonitor to support forced event subscription failure for testing
2. **Concurrent Media Changes**: Simulate media changes during recovery
3. **Stress Testing**: Test recovery under high load conditions
4. **Network Failure Simulation**: Test recovery when HTTP server is unavailable
5. **Multiple Simultaneous Recoveries**: Test behavior when multiple recovery triggers occur

## Related Tests

- `test_extended_operation.py`: Tests long-running stability
- `test_cpu_stability.py`: Tests CPU usage over time
- `test_diagnostic_integration.py`: Tests diagnostic mode functionality

## References

- Design Document: `.kiro/specs/media-source-refresh/design.md`
- Requirements: `.kiro/specs/media-source-refresh/requirements.md`
- HealthMonitor: `MediaMonitor/HealthMonitor.cs`
- RecoveryManager: `MediaMonitor/RecoveryManager.cs`
