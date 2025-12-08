# Design Document: Media Source Refresh Fix

## Overview

This design addresses the critical issue where MediaMonitor stops receiving track updates after extended operation. The root cause is event subscription degradation in the WinRT GlobalSystemMediaTransportControlsSession API. The solution implements a health monitoring system with automatic recovery, enhanced diagnostics, and isolation of potentially interfering components.

## Architecture

### Current Architecture Issues

1. **Event Subscription Fragility**: WinRT event handlers can silently fail or detach without notification
2. **Blocking Operations**: ConfigPoller and HTTP operations can block the main event loop
3. **Lock Contention**: Debounce timer and HTTP semaphore can deadlock under certain conditions
4. **No Health Monitoring**: System has no way to detect when updates stop flowing

### Proposed Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      MediaMonitor                            │
│                                                              │
│  ┌────────────────┐      ┌──────────────────┐              │
│  │ Health Monitor │─────▶│ Recovery Manager │              │
│  │  - Heartbeat   │      │  - Resubscribe   │              │
│  │  - Timeout     │      │  - Reinitialize  │              │
│  └────────────────┘      └──────────────────┘              │
│         │                                                    │
│         ▼                                                    │
│  ┌────────────────────────────────────────┐                │
│  │      Event Subscription Manager         │                │
│  │  - MediaPropertiesChanged              │                │
│  │  - PlaybackInfoChanged                 │                │
│  │  - TimelinePropertiesChanged           │                │
│  │  - SessionsChanged                     │                │
│  └────────────────────────────────────────┘                │
│         │                                                    │
│         ▼                                                    │
│  ┌────────────────┐      ┌──────────────────┐              │
│  │ Update Queue   │─────▶│ HTTP Client Pool │              │
│  │  - Debounce    │      │  - Timeout       │              │
│  │  - Batch       │      │  - Retry         │              │
│  └────────────────┘      └──────────────────┘              │
│                                                              │
│  ┌────────────────────────────────────────┐                │
│  │      Isolated ConfigPoller              │                │
│  │  - Separate HTTP client                │                │
│  │  - Non-blocking queue                  │                │
│  └────────────────────────────────────────┘                │
└─────────────────────────────────────────────────────────────┘
```

## Components and Interfaces

### 1. Health Monitor

**Purpose**: Continuously monitors event subscription health and triggers recovery when needed.

**Interface**:
```csharp
public class HealthMonitor
{
    // Configuration
    private readonly TimeSpan updateTimeout = TimeSpan.FromSeconds(30);
    private readonly TimeSpan heartbeatInterval = TimeSpan.FromSeconds(5);
    
    // State tracking
    private DateTime lastUpdateReceived;
    private Timer heartbeatTimer;
    
    // Events
    public event EventHandler<HealthStatusEventArgs> HealthStatusChanged;
    public event EventHandler RecoveryNeeded;
    
    // Methods
    public void RecordUpdate();  // Called when track update received
    public void Start();
    public void Stop();
    private void CheckHealth(object state);
}
```

**Behavior**:
- Runs a timer every 5 seconds to check if updates have been received
- If no updates for 30 seconds, fires `RecoveryNeeded` event
- Logs health status changes for diagnostics

### 2. Recovery Manager

**Purpose**: Handles automatic recovery from event subscription failures.

**Interface**:
```csharp
public class RecoveryManager
{
    private readonly MediaMonitor monitor;
    private int recoveryAttempts = 0;
    private const int MAX_RECOVERY_ATTEMPTS = 3;
    
    public async Task<bool> AttemptRecovery();
    private async Task UnsubscribeAll();
    private async Task ReinitializeSessionManager();
    private async Task ReestablishSubscriptions();
}
```

**Recovery Procedure**:
1. Log recovery initiation with timestamp
2. Unsubscribe from all current event handlers
3. Dispose and recreate SessionManager
4. Re-establish event subscriptions
5. Force immediate update to verify recovery
6. Log recovery outcome

### 3. Event Subscription Manager

**Purpose**: Centralizes event subscription lifecycle management with enhanced logging.

**Interface**:
```csharp
public class EventSubscriptionManager
{
    private GlobalSystemMediaTransportControlsSession currentSession;
    private bool isSubscribed = false;
    
    public event EventHandler<MediaUpdateEventArgs> MediaUpdated;
    
    public async Task Subscribe(GlobalSystemMediaTransportControlsSession session);
    public void Unsubscribe();
    public bool IsHealthy { get; }
    
    // Event handlers with diagnostic logging
    private void OnMediaPropertiesChanged(object sender, MediaPropertiesChangedEventArgs args);
    private void OnPlaybackInfoChanged(object sender, PlaybackInfoChangedEventArgs args);
    private void OnTimelinePropertiesChanged(object sender, TimelinePropertiesChangedEventArgs args);
}
```

**Diagnostic Logging**:
- Log every event invocation with timestamp and event type
- Log event handler execution time
- Log any exceptions during event handling
- Track event frequency to detect anomalies

### 4. Update Queue with Timeout-Protected Locks

**Purpose**: Batches updates with deadlock prevention.

**Interface**:
```csharp
public class UpdateQueue
{
    private readonly SemaphoreSlim updateLock = new SemaphoreSlim(1, 1);
    private readonly TimeSpan lockTimeout = TimeSpan.FromSeconds(5);
    private Timer debounceTimer;
    private bool pendingUpdate = false;
    
    public void QueueUpdate(CurrentMediaState state);
    private async Task ProcessUpdate();
}
```

**Deadlock Prevention**:
- Use `WaitAsync(timeout)` instead of `WaitAsync()`
- Log timeout events
- Skip update if lock cannot be acquired
- Trigger recovery if repeated timeouts occur

### 5. HTTP Client Pool with Retry Logic

**Purpose**: Manages HTTP requests with timeout and retry handling.

**Interface**:
```csharp
public class HttpClientPool
{
    private readonly HttpClient client;
    private readonly SemaphoreSlim httpSemaphore = new SemaphoreSlim(1, 1);
    private readonly TimeSpan requestTimeout = TimeSpan.FromSeconds(5);
    private readonly TimeSpan semaphoreTimeout = TimeSpan.FromSeconds(3);
    
    public async Task<bool> SendUpdate(object data, string endpoint);
    private async Task<bool> SendWithRetry(HttpContent content, string url, int maxRetries = 2);
}
```

**Retry Strategy**:
- Retry on timeout or network errors
- Exponential backoff: 100ms, 500ms, 1000ms
- Always release semaphore in finally block
- Log all retry attempts

### 6. Isolated ConfigPoller

**Purpose**: Polls configuration changes without blocking main event loop.

**Interface**:
```csharp
public class IsolatedConfigPoller
{
    private readonly HttpClient dedicatedClient;  // Separate from main HTTP client
    private readonly Timer pollerTimer;
    private readonly ConcurrentQueue<string> sourceChangeQueue;
    private string lastKnownSource = "";
    
    public event EventHandler<SourceChangedEventArgs> SourceChanged;
    
    public void Start();
    public void Stop();
    private async Task PollConfiguration();
    private void ProcessQueuedChanges();
}
```

**Isolation Strategy**:
- Uses dedicated HttpClient instance
- Queues source changes instead of blocking
- Debounces rapid changes (minimum 2 seconds between changes)
- Failures don't affect main event loop

## Data Models

### HealthStatusEventArgs
```csharp
public class HealthStatusEventArgs : EventArgs
{
    public bool IsHealthy { get; set; }
    public TimeSpan TimeSinceLastUpdate { get; set; }
    public string Reason { get; set; }
}
```

### MediaUpdateEventArgs
```csharp
public class MediaUpdateEventArgs : EventArgs
{
    public string Artist { get; set; }
    public string Title { get; set; }
    public double Position { get; set; }
    public double Duration { get; set; }
    public bool IsPlaying { get; set; }
    public string SourceId { get; set; }
    public DateTime Timestamp { get; set; }
}
```

### DiagnosticLogEntry
```csharp
public class DiagnosticLogEntry
{
    public DateTime Timestamp { get; set; }
    public string EventType { get; set; }  // "MediaUpdate", "EventFired", "HttpRequest", etc.
    public string Details { get; set; }
    public TimeSpan? Duration { get; set; }
    public bool Success { get; set; }
}
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Update continuity under normal operation
*For any* sequence of media changes in Windows, when the MediaMonitor is running and media is actively playing, track updates should be received and propagated within 5 seconds of each change.
**Validates: Requirements 1.1, 1.2**

### Property 2: Recovery triggers on timeout
*For any* state where no updates have been received for 30 seconds, the HealthMonitor should trigger the recovery procedure exactly once.
**Validates: Requirements 3.1**

### Property 3: Event subscription cleanup
*For any* recovery procedure execution, all previous event subscriptions should be unsubscribed before new subscriptions are established, preventing memory leaks.
**Validates: Requirements 1.5**

### Property 4: Lock timeout prevents deadlock
*For any* attempt to acquire the update lock or HTTP semaphore, if the lock cannot be acquired within the timeout period, the operation should be skipped and logged without blocking indefinitely.
**Validates: Requirements 5.1, 5.2, 5.3**

### Property 5: ConfigPoller isolation
*For any* configuration polling operation failure, the failure should not prevent or delay media update event processing.
**Validates: Requirements 4.2**

### Property 6: Diagnostic logging completeness
*For any* event handler invocation, HTTP request, or recovery procedure, a diagnostic log entry should be created with timestamp and outcome.
**Validates: Requirements 2.1, 2.2, 2.3, 2.4**

### Property 7: HTTP semaphore release guarantee
*For any* HTTP request attempt (successful or failed), the HTTP semaphore should be released exactly once, preventing semaphore exhaustion.
**Validates: Requirements 5.4**

### Property 8: Recovery success verification
*For any* completed recovery procedure, the system should verify recovery success by checking if a track update is received within 10 seconds.
**Validates: Requirements 3.5**

## Error Handling

### Event Subscription Errors
- **Symptom**: Exception during event handler attachment
- **Handling**: Log error, attempt recovery after 5 seconds
- **User Impact**: Temporary loss of updates, automatic recovery

### HTTP Timeout Errors
- **Symptom**: HTTP request exceeds 5-second timeout
- **Handling**: Release semaphore, log timeout, retry with exponential backoff
- **User Impact**: Delayed update propagation, no data loss

### Lock Acquisition Timeout
- **Symptom**: Cannot acquire update lock within 5 seconds
- **Handling**: Skip update, log timeout, trigger recovery if repeated
- **User Impact**: Missed intermediate updates, critical updates still propagate

### Recovery Failure
- **Symptom**: Recovery procedure fails after 3 attempts
- **Handling**: Log critical error, enter degraded mode, notify user
- **User Impact**: Manual restart required

### ConfigPoller Errors
- **Symptom**: Configuration polling fails
- **Handling**: Log error, continue with last known configuration
- **User Impact**: Configuration changes delayed until next successful poll

## Testing Strategy

### Unit Tests

Unit tests verify specific components in isolation:

1. **HealthMonitor Tests**
   - Test heartbeat timer fires at correct intervals
   - Test recovery trigger after timeout threshold
   - Test update recording resets timeout

2. **RecoveryManager Tests**
   - Test recovery procedure steps execute in order
   - Test maximum recovery attempt limit
   - Test recovery success verification

3. **EventSubscriptionManager Tests**
   - Test subscription lifecycle (subscribe/unsubscribe)
   - Test event handler invocation logging
   - Test exception handling in event handlers

4. **UpdateQueue Tests**
   - Test debounce timer behavior
   - Test lock timeout handling
   - Test update batching

5. **HttpClientPool Tests**
   - Test retry logic with exponential backoff
   - Test semaphore release in all code paths
   - Test timeout handling

6. **IsolatedConfigPoller Tests**
   - Test configuration change detection
   - Test change debouncing
   - Test isolation from main event loop

### Property-Based Tests

Property-based tests verify universal properties across many inputs:

1. **Property Test: Update Continuity**
   - Generate random sequences of media changes
   - Verify all changes propagate within 5 seconds
   - Run for minimum 100 iterations

2. **Property Test: Recovery Trigger**
   - Generate random update patterns with gaps
   - Verify recovery triggers exactly once per 30-second gap
   - Run for minimum 100 iterations

3. **Property Test: Lock Timeout**
   - Generate random concurrent lock acquisition attempts
   - Verify no indefinite blocking occurs
   - Run for minimum 100 iterations

4. **Property Test: Semaphore Release**
   - Generate random HTTP request patterns (success/failure)
   - Verify semaphore count never goes negative
   - Run for minimum 100 iterations

5. **Property Test: Diagnostic Logging**
   - Generate random event sequences
   - Verify every event has corresponding log entry
   - Run for minimum 100 iterations

### Integration Tests

1. **Extended Operation Test**
   - Run MediaMonitor for 30 minutes
   - Simulate media changes every 30 seconds
   - Verify continuous update flow
   - Verify no memory leaks

2. **Recovery Simulation Test**
   - Force event subscription failure
   - Verify automatic recovery
   - Verify updates resume after recovery

3. **Stress Test**
   - Rapid media changes (every 2 seconds)
   - Verify system handles high update frequency
   - Verify no updates lost

4. **ConfigPoller Isolation Test**
   - Simulate ConfigPoller failures
   - Verify media updates continue unaffected
   - Verify configuration eventually syncs

### Testing Framework

- **Unit Tests**: xUnit for C# components
- **Property-Based Tests**: FsCheck for C# (integrates with xUnit)
- **Integration Tests**: Custom Python test harness (existing test_cpu_stability.py as template)
- **Test Configuration**: Minimum 100 iterations for property tests

## Implementation Notes

### Phase 1: Core Infrastructure
- Implement HealthMonitor
- Implement RecoveryManager
- Add diagnostic logging to existing event handlers

### Phase 2: Deadlock Prevention
- Implement timeout-protected locks in UpdateQueue
- Implement HttpClientPool with retry logic
- Add semaphore release verification

### Phase 3: ConfigPoller Isolation
- Extract ConfigPoller to separate class
- Implement dedicated HTTP client
- Implement change queue

### Phase 4: Testing
- Write unit tests for all new components
- Write property-based tests for correctness properties
- Run extended operation tests

### Phase 5: Integration
- Wire all components together in MediaMonitor
- Add command-line flag for diagnostic mode
- Update documentation

## Performance Considerations

- **Health Monitor**: 5-second heartbeat adds negligible CPU overhead
- **Diagnostic Logging**: Use buffered logging to minimize I/O impact
- **Lock Timeouts**: 5-second timeout prevents indefinite blocking without impacting normal operation
- **HTTP Retry**: Exponential backoff prevents network flooding
- **ConfigPoller**: 2-second poll interval is sufficient for configuration changes

## Backward Compatibility

- All changes are internal to MediaMonitor.cs
- Python server API remains unchanged
- Configuration file format unchanged
- Existing tests continue to work
