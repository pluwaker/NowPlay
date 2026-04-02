# ConfigPoller Isolation Integration Test

## Overview

This test validates that the IsolatedConfigPoller component properly isolates configuration polling failures from the main media update event loop. The test simulates configuration endpoint failures and verifies that media updates continue unaffected.

## Requirements Validated

- **4.2**: ConfigPoller operation failures do not block main event processing loop
- **4.3**: ConfigPoller queues changes for processing rather than blocking

## Test Scenarios

### Full Test (`test_configpoller_isolation.py`)

**Duration**: 5 minutes

**Test Phases**:
1. **Baseline Operation (30 seconds)**: Establish normal operation baseline
2. **Config Failures (60 seconds)**: Simulate config endpoint failures
3. **Config Recovery (30 seconds)**: Verify config endpoint recovers
4. **Continued Monitoring**: Monitor for remainder of test duration

**Success Criteria**:
- Media updates continue during config failures
- No significant gaps (>30s) in media updates during failures
- Config endpoint recovers after failures stop
- System remains stable throughout test

### Quick Test (`test_configpoller_isolation_quick.py`)

**Duration**: 2 minutes

**Test Phases**:
1. **Baseline Operation (15 seconds)**: Establish normal operation baseline
2. **Config Failures (30 seconds)**: Simulate config endpoint failures
3. **Config Recovery (15 seconds)**: Verify config endpoint recovers
4. **Continued Monitoring**: Monitor for remainder of test duration

**Success Criteria**:
- System doesn't crash during config failures
- Config endpoint recovers after failures stop

## How It Works

### Mock Server

The test creates a Flask-based mock Python server that:
- Accepts media updates on `/update` endpoint
- Provides configuration on `/get_config` endpoint
- Can simulate failures on `/get_config` via control endpoint
- Logs all requests for analysis

### Failure Simulation

Config failures are simulated by:
1. Enabling failure mode via `/control/config_failure` endpoint
2. Mock server returns HTTP 500 errors for `/get_config` requests
3. After failure period, disabling failure mode
4. Mock server resumes normal responses

### Metrics Collected

1. **Media Updates**:
   - Total updates received
   - Updates before, during, and after failures
   - Update rate during failures
   - Gaps in update flow

2. **Config Requests**:
   - Total config requests
   - Successful vs failed requests
   - Requests during failure period
   - Recovery time after failures stop

3. **Isolation Effectiveness**:
   - Whether media updates continued during failures
   - Maximum gap in updates during failures
   - System stability during failures

## Running the Tests

### Prerequisites

```bash
pip install flask psutil requests
```

### Full Test

```bash
cd MediaMonitor
python test_configpoller_isolation.py
```

### Quick Test

```bash
cd MediaMonitor
python test_configpoller_isolation_quick.py
```

## Expected Output

### Successful Test

```
================================================================================
  MediaMonitor ConfigPoller Isolation Integration Test
================================================================================
Test duration: 5 minutes
Config failure duration: 60 seconds
================================================================================

🌐 Starting mock Python server...
✅ Mock server started on port 8080
🔨 Building MediaMonitor...
✅ Build successful
🚀 Starting MediaMonitor...
✅ MediaMonitor started (PID: 12345)

📝 Test Plan:
   1. Run normally for 30 seconds (baseline)
   2. Enable config failures for 60 seconds
   3. Disable config failures and verify recovery
   4. Continue monitoring for remainder of test

================================================================================
  Phase 1: Baseline Operation (30 seconds)
================================================================================
✅ Baseline complete: 5 updates received

================================================================================
  Phase 2: Config Failures (60 seconds)
================================================================================
🔴 Config failures enabled at 14:30:00
   Monitoring media updates during config failures...

   ⏱️  5s elapsed - Updates during failures: 1
   ⏱️  10s elapsed - Updates during failures: 2
   ...

✅ Failure period complete
   Updates received during failures: 10

================================================================================
  Phase 3: Config Recovery (30 seconds)
================================================================================
🟢 Config failures disabled at 14:31:00
   Monitoring config recovery...

✅ Config recovered: 3 successful requests

================================================================================
  Phase 4: Continued Monitoring
================================================================================
✅ Test duration complete

📊 Loading and analyzing results...

================================================================================
  Test Results Analysis
================================================================================

📈 Media Update Statistics:
   Total updates received: 25
   First update: 14:29:30.123
   Last update: 14:34:30.456
   Updates before failures: 5
   Updates during failures: 10
   Updates after failures: 10

🔍 Config Request Statistics:
   Total config requests: 150
   Successful requests: 120
   Failed requests: 30
   Requests during failure period: 30
   Failed during failure period: 30
   Requests after failure period: 90
   Successful after failure period: 90

🛡️  Isolation Effectiveness:
   ✅ Media updates continued during config failures
   Update rate during failures: 10.0 updates/minute
   ✅ No significant gaps in updates during failures

🔄 Config Recovery:
   ✅ Config recovered after 2.1s
   Successful requests after recovery: 90

================================================================================
  Overall Assessment
================================================================================
✅ TEST PASSED

Requirements validated:
  ✅ 4.2: ConfigPoller failures did not block main event processing
  ✅ 4.3: ConfigPoller queued changes for non-blocking processing
  ✅ Media updates continued unaffected during config failures
  ✅ Configuration eventually synced after failures stopped
================================================================================

📝 Detailed report saved to: configpoller_isolation_report_20241208_143500.txt
```

## Interpreting Results

### Pass Criteria

The test passes if:
1. Media updates continue during config failures (at least some updates received)
2. No gaps >30 seconds in media updates during failures
3. Config endpoint recovers after failures stop (successful requests resume)

### Common Issues

1. **No updates received**: Likely no media is playing during test
   - Solution: Play media in Windows during test

2. **Config doesn't recover**: Mock server may have crashed
   - Check mock server logs
   - Verify Flask is installed correctly

3. **MediaMonitor crashes**: Check MediaMonitor diagnostic output
   - Look for unhandled exceptions
   - Verify IsolatedConfigPoller error handling

## Test Reports

Detailed reports are saved to:
- `configpoller_isolation_report_YYYYMMDD_HHMMSS.txt`

Reports include:
- All media updates with timestamps
- All config requests with success/failure status
- Detailed timing analysis
- Isolation effectiveness metrics

## Architecture Validation

This test validates the isolation architecture:

```
┌─────────────────────────────────────────┐
│           MediaMonitor                   │
│                                          │
│  ┌────────────────────────────────────┐ │
│  │   Main Event Loop                  │ │
│  │   - Media updates                  │ │
│  │   - Event subscriptions            │ │
│  └────────────────────────────────────┘ │
│                                          │
│  ┌────────────────────────────────────┐ │
│  │   IsolatedConfigPoller             │ │
│  │   - Dedicated HTTP client          │ │
│  │   - Error isolation                │ │
│  │   - Non-blocking queue             │ │
│  └────────────────────────────────────┘ │
│                                          │
└─────────────────────────────────────────┘
         │                    │
         │                    │ (isolated)
         ▼                    ▼
    /update              /get_config
   (continues)          (may fail)
```

The test confirms that failures in the config polling path do not affect the media update path.
