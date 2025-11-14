# Design Document

## Overview

The MediaMonitor component suffers from progressive CPU usage growth due to multiple resource leaks and inefficient patterns. Analysis of the current implementation reveals several critical issues:

1. **Session objects are never disposed** - Each call to `GetSessions()` and `GetCurrentSession()` creates COM objects that accumulate
2. **HttpResponseMessage objects leak** - Fire-and-forget HTTP calls don't dispose responses
3. **CancellationTokenSource accumulates** - Old instances are cancelled but not disposed
4. **Excessive session enumeration** - `SendAvailableSources()` and `GetSessionBySource()` enumerate all sessions repeatedly
5. **Fire-and-forget tasks** - `Task.Run` without proper tracking or cancellation

This design addresses each issue with targeted fixes while maintaining backward compatibility and existing functionality.

## Architecture

### Resource Management Strategy

The solution implements a three-tier resource management approach:

1. **Immediate Disposal Pattern**: Dispose of short-lived resources (sessions, responses) immediately after use using `using` statements
2. **Cached Resources**: Cache session lists and manager instances with time-based invalidation
3. **Lifecycle Management**: Implement IDisposable on MediaMonitor for proper cleanup on shutdown

### Key Design Decisions

**Decision 1: Session Disposal**
- **Rationale**: SMTC Session objects are COM wrappers that must be explicitly disposed
- **Implementation**: Wrap all session access in `using` statements or explicit `Dispose()` calls
- **Trade-off**: Slight code verbosity for guaranteed resource cleanup

**Decision 2: Session List Caching**
- **Rationale**: Enumerating sessions is expensive and rarely changes
- **Implementation**: Cache session list for 30 seconds, invalidate on source change
- **Trade-off**: 30-second delay in detecting new media sources vs 95% reduction in enumeration calls

**Decision 3: HttpClient Response Handling**
- **Rationale**: Fire-and-forget pattern leaks HttpResponseMessage objects
- **Implementation**: Always await and dispose responses, even for fire-and-forget semantics
- **Trade-off**: Minimal async overhead vs guaranteed resource cleanup

**Decision 4: Single Active Task**
- **Rationale**: Multiple concurrent `ProcessTrackChange` tasks accumulate
- **Implementation**: Cancel and await previous task before starting new one
- **Trade-off**: Slight delay in track changes vs no task accumulation

## Components and Interfaces

### 1. MediaMonitor (Modified)

**New Fields:**
```csharp
private DateTime lastSourceEnumeration = DateTime.MinValue;
private const int SOURCE_CACHE_SECONDS = 30;
private Task? activeTrackTask = null;
private readonly SemaphoreSlim httpSemaphore = new SemaphoreSlim(1, 1);
private bool diagnosticMode = false;
```

**New Methods:**
```csharp
public void Dispose()
- Disposes HttpClient, CancellationTokenSource, SemaphoreSlim
- Cancels any active tasks
- Implements IDisposable pattern

private bool ShouldEnumerateSources()
- Returns true if cache expired (30+ seconds since last enumeration)
- Prevents excessive session enumeration

private async Task DisposeSessionsAsync(IReadOnlyList<GlobalSystemMediaTransportControlsSession> sessions)
- Safely disposes all sessions in a collection
- Handles exceptions per session

private async Task<HttpResponseMessage> SendHttpWithDisposalAsync(HttpRequestMessage request)
- Sends HTTP request with proper response disposal
- Uses semaphore to limit concurrent requests
- Returns disposed response (caller doesn't need to dispose)
```

### 2. SessionCache (New Helper Class)

```csharp
internal class SessionCache
{
    private List<string> cachedSourceIds = new();
    private DateTime cacheTime = DateTime.MinValue;
    private const int CACHE_DURATION_SECONDS = 30;
    
    public bool IsValid()
    - Returns true if cache is less than 30 seconds old
    
    public void Update(List<string> sourceIds)
    - Updates cache with new source list and timestamp
    
    public List<string> GetCached()
    - Returns cached source IDs
}
```

### 3. DiagnosticLogger (New Helper Class)

```csharp
internal class DiagnosticLogger
{
    private int sessionAccessCount = 0;
    private int httpRequestCount = 0;
    private DateTime lastLogTime = DateTime.MinValue;
    
    public void LogSessionAccess()
    - Increments session access counter
    
    public void LogHttpRequest()
    - Increments HTTP request counter
    
    public void LogPeriodic()
    - Logs counters every 10 seconds if diagnostic mode enabled
    - Resets counters after logging
}
```

## Data Models

No changes to existing data models (CurrentMediaState). All modifications are internal to MediaMonitor.

## Error Handling

### Session Disposal Errors
- **Strategy**: Catch and log individual session disposal failures, continue with remaining sessions
- **Rationale**: One corrupted session shouldn't block cleanup of others

### HTTP Timeout Handling
- **Strategy**: Set 5-second timeout on HttpClient, catch TaskCanceledException
- **Rationale**: Prevent indefinite hangs on server unavailability

### Manager Request Failures
- **Strategy**: Retry once after 1-second delay, then skip cycle
- **Rationale**: Transient COM errors are common, but shouldn't block monitoring

## Implementation Details

### Critical Fix 1: Tick() Session Disposal

**Current Problem:**
```csharp
var manager = await GlobalSystemMediaTransportControlsSessionManager.RequestAsync();
currentSession = await GetSessionBySource(manager);
// manager and intermediate sessions never disposed
```

**Solution:**
```csharp
var manager = await GlobalSystemMediaTransportControlsSessionManager.RequestAsync();
try
{
    currentSession = await GetSessionBySource(manager);
    // Use currentSession
}
finally
{
    // Dispose intermediate sessions from GetSessionBySource
    // Keep currentSession alive for this cycle
}
```

### Critical Fix 2: GetSessionBySource() Disposal

**Current Problem:**
```csharp
var sessions = manager.GetSessions(); // Returns IReadOnlyList<Session>
foreach (var session in sessions)
{
    // session objects never disposed
}
```

**Solution:**
```csharp
var sessions = manager.GetSessions();
try
{
    GlobalSystemMediaTransportControlsSession? result = null;
    foreach (var session in sessions)
    {
        if (session.SourceAppUserModelId == selectedSource)
        {
            result = session;
            // Don't dispose the one we're returning
        }
        else
        {
            session?.Dispose(); // Dispose non-matching sessions immediately
        }
    }
    return result;
}
catch
{
    // Dispose all sessions on error
    foreach (var session in sessions)
        session?.Dispose();
    throw;
}
```

### Critical Fix 3: SendAvailableSources() Caching

**Current Problem:**
```csharp
// Called on every LoadSelectedSource, enumerates all sessions
var sessions = manager.GetSessions();
foreach (var session in sessions) { /* never disposed */ }
```

**Solution:**
```csharp
if (!ShouldEnumerateSources())
    return; // Skip if cache valid

var sessions = manager.GetSessions();
try
{
    // Process sessions
    foreach (var session in sessions)
    {
        // Extract info
        session.Dispose(); // Dispose immediately after reading
    }
}
finally
{
    lastSourceEnumeration = DateTime.Now;
}
```

### Critical Fix 4: HTTP Response Disposal

**Current Problem:**
```csharp
_ = httpClient.PostAsync($"{pythonServerUrl}/update_from_cs", content);
// Response never disposed, accumulates in memory
```

**Solution:**
```csharp
await httpSemaphore.WaitAsync();
try
{
    using var response = await httpClient.PostAsync(url, content);
    // Response automatically disposed
}
finally
{
    httpSemaphore.Release();
}
```

### Critical Fix 5: CancellationTokenSource Disposal

**Current Problem:**
```csharp
trackTaskCTS?.Cancel();
trackTaskCTS = new CancellationTokenSource();
// Old CTS never disposed
```

**Solution:**
```csharp
var oldCts = trackTaskCTS;
trackTaskCTS = new CancellationTokenSource();
oldCts?.Cancel();
oldCts?.Dispose(); // Dispose after cancelling
```

### Critical Fix 6: Task.Run Tracking

**Current Problem:**
```csharp
_ = Task.Run(() => ProcessTrackChange(mediaInfo, trackTaskCTS.Token));
// Multiple tasks can accumulate
```

**Solution:**
```csharp
if (activeTrackTask != null && !activeTrackTask.IsCompleted)
{
    trackTaskCTS?.Cancel();
    try { await activeTrackTask; } catch { }
}

activeTrackTask = Task.Run(() => ProcessTrackChange(mediaInfo, trackTaskCTS.Token));
```

## Testing Strategy

### Unit Tests (Optional)

Focus on resource disposal verification:

1. **SessionDisposalTest**: Verify sessions are disposed after enumeration
2. **HttpResponseDisposalTest**: Verify responses are disposed after requests
3. **CancellationTokenDisposalTest**: Verify old CTS instances are disposed

### Integration Tests

1. **LongRunningCpuTest**: Run MediaMonitor for 1 hour, measure CPU variance
2. **MemoryLeakTest**: Monitor memory usage over 24 hours, verify no growth
3. **SessionEnumerationTest**: Verify sources are cached for 30 seconds

### Manual Testing

1. Run MediaMonitor with diagnostic mode enabled
2. Monitor console output for resource counters
3. Use Windows Performance Monitor to track:
   - CPU usage over time
   - Handle count (should remain stable)
   - Private bytes (should remain stable)

### Performance Benchmarks

**Baseline (Current):**
- Initial CPU: ~2%
- After 1 hour: ~8-12%
- After 4 hours: ~20-30%

**Target (After Fix):**
- Initial CPU: ~1-2%
- After 1 hour: ~1-3% (within 2% variance)
- After 24 hours: ~1-4% (within 5% variance)

## Diagnostic Mode

Enable via command-line argument: `MediaMonitor.exe --diagnostic`

**Output every 10 seconds:**
```
[DIAG] Sessions accessed: 45, HTTP requests: 23, Memory delta: +2.1 MB
```

This helps identify if fixes are effective and pinpoint remaining issues.

## Migration Path

1. Implement fixes incrementally, starting with highest-impact (session disposal)
2. Test each fix independently with 1-hour CPU monitoring
3. Combine all fixes and run 24-hour stability test
4. Deploy with diagnostic mode enabled for first week
5. Monitor production metrics, adjust cache timings if needed

## Backward Compatibility

All changes are internal to MediaMonitor.cs. No API changes, no breaking changes to:
- Python server communication protocol
- CurrentMediaState structure
- Configuration format
- Command-line interface (except new --diagnostic flag)
