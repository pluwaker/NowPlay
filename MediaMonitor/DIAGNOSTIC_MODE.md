# Diagnostic Mode Documentation

## Overview

MediaMonitor now includes a comprehensive diagnostic mode that provides verbose logging for troubleshooting event subscription issues and tracking media update flow.

## Enabling Diagnostic Mode

To enable diagnostic mode, run MediaMonitor with the `--diagnostic` or `-d` command-line flag:

```bash
MediaMonitor.exe --diagnostic
```

or

```bash
MediaMonitor.exe -d
```

## Features

When diagnostic mode is enabled, the following features are activated:

### 1. Console Output Formatting
- All log messages include precise timestamps (HH:mm:ss.fff format)
- Component names are clearly labeled in brackets
- Events are categorized by type (Event, HTTP Request, Health Status, etc.)

### 2. Log File Output
- A log file is automatically created in the `logs` directory
- Log file naming format: `mediamonitor_diagnostic_YYYYMMDD_HHmmss.log`
- All console output is also written to the log file
- Log file location is displayed when diagnostic mode starts

### 3. Verbose Event Logging

#### Health Monitor Events
- Update recordings
- Health status changes (HEALTHY/UNHEALTHY)
- Recovery trigger events
- Time since last update

#### Event Subscription Events
- Subscription lifecycle (subscribe/unsubscribe)
- Individual event handler subscriptions (MediaPropertiesChanged, PlaybackInfoChanged, TimelinePropertiesChanged)
- Event invocation timestamps
- Event handler execution duration

#### Update Queue Events
- Lock acquisition attempts and results
- Lock timeout events
- Consecutive timeout tracking
- Update processing details

#### HTTP Request Events
- Request initiation
- Semaphore acquisition
- Request duration
- Success/failure status
- Retry attempts with delays
- Error messages

#### Recovery Events
- Recovery procedure initiation
- Each recovery step (Unsubscribe, Reinitialize, Resubscribe, Verify)
- Recovery success/failure
- Recovery attempt counter

## Log Format

Diagnostic log entries follow this format:

```
[HH:mm:ss.fff] [ComponentName] Message
```

Example:
```
[14:23:45.123] [HealthMonitor] Update recorded
[14:23:45.125] [EventSubscriptionManager] Event: MediaPropertiesChanged - Artist - Title (duration: 15ms)
[14:23:45.140] [UpdateQueue] Lock Acquire: SUCCESS (5ms)
[14:23:45.145] [HttpClientPool] HTTP SUCCESS: /update_from_cs (120ms)
```

## Use Cases

### Troubleshooting Event Subscription Failures
When media updates stop flowing, diagnostic mode helps identify:
- When the last event was received
- Whether event handlers are being invoked
- If lock timeouts are occurring
- HTTP request success/failure patterns

### Performance Analysis
Diagnostic mode provides timing information for:
- Event handler execution time
- Lock acquisition duration
- HTTP request duration
- Recovery procedure timing

### Recovery Monitoring
Track the automatic recovery process:
- When recovery is triggered
- Which recovery steps succeed/fail
- How long recovery takes
- Whether updates resume after recovery

## Example Output

### Normal Operation
```
🔍 Diagnostic mode enabled
📝 Verbose logging active - all events will be logged
📁 Log file will be created in the 'logs' directory
📝 Diagnostic log file: H:\VKR\NowPlay\MediaMonitor\logs\mediamonitor_diagnostic_20241208_142345.log

[14:23:45.100] [DiagnosticLogger] Diagnostic mode initialized
✅ MediaMonitor запущен!
[14:23:45.200] [EventSubscriptionManager] Subscribe: Spotify.exe
[14:23:45.201] [EventSubscriptionManager] Subscribe: Spotify.exe - Event: MediaPropertiesChanged
[14:23:46.500] [EventSubscriptionManager] Event: MediaPropertiesChanged - Artist - Song Title (duration: 15ms)
[14:23:46.515] [HealthMonitor] Update recorded
[14:23:46.520] [UpdateQueue] Lock Acquire: SUCCESS (5ms)
[14:23:46.525] [UpdateQueue] Processing update: Artist - Song Title
[14:23:46.650] [HttpClientPool] HTTP SUCCESS: /update_from_cs (120ms)
```

### Recovery Scenario
```
[14:25:15.000] [HealthMonitor] Health Status: UNHEALTHY - No updates received for 30.0 seconds (time since last update: 30.0s)
[14:25:15.001] [RecoveryManager] Recovery Started: SUCCESS - Attempt 1/3
[14:25:15.002] [RecoveryManager] Recovery Step 1: Unsubscribe: SUCCESS - Starting
[14:25:15.010] [EventSubscriptionManager] Unsubscribe: Spotify.exe
[14:25:15.015] [RecoveryManager] Recovery Step 1: Unsubscribe: SUCCESS - Complete
[14:25:15.016] [RecoveryManager] Recovery Step 2: Reinitialize: SUCCESS - Starting
[14:25:15.100] [RecoveryManager] Recovery Step 2: Reinitialize: SUCCESS - Complete
[14:25:15.101] [RecoveryManager] Recovery Step 3: Resubscribe: SUCCESS - Starting
[14:25:15.150] [EventSubscriptionManager] Subscribe: Spotify.exe
[14:25:15.155] [RecoveryManager] Recovery Step 3: Resubscribe: SUCCESS - Complete
[14:25:15.156] [RecoveryManager] Recovery Step 4: Verify: SUCCESS - Starting
[14:25:15.200] [RecoveryManager] Recovery Step 4: Verify: SUCCESS - Complete
[14:25:15.201] [RecoveryManager] Recovery Completed: SUCCESS - All steps successful
```

## Performance Impact

Diagnostic mode has minimal performance impact:
- Log file writes are buffered and asynchronous
- Diagnostic logging only occurs when diagnostic mode is enabled
- No overhead in normal operation mode

## Disabling Diagnostic Mode

Simply run MediaMonitor without the `--diagnostic` or `-d` flag:

```bash
MediaMonitor.exe
```

In normal mode, only essential console messages are displayed, and no log file is created.

## Requirements Validation

This implementation satisfies the following requirements:

- **Requirement 1.4**: Diagnostic information is logged when track updates stop flowing
- **Requirement 2.1**: Event handler invocations are logged with event type and timestamp
- **Requirement 2.2**: HTTP requests are logged with success/failure and timing information
- **Requirement 2.3**: Debounce timer events are logged (via UpdateQueue)
- **Requirement 2.4**: Event subscription lifecycle events are logged
- **Requirement 2.5**: Health monitoring warnings are logged when no updates are received

## Log File Management

Log files are stored in the `logs` directory within the MediaMonitor application directory. Each diagnostic session creates a new log file with a timestamp. Consider periodically cleaning old log files to manage disk space.
