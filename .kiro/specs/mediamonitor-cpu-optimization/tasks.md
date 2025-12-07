# Implementation Plan

- [x] 1. Implement IDisposable pattern and resource cleanup infrastructure





  - Add IDisposable interface to MediaMonitor class
  - Implement Dispose() method to clean up HttpClient, semaphores, and cancellation tokens
  - Add private disposed flag to prevent double disposal
  - Add finalizer for safety (calls Dispose)
  - _Requirements: 2.5_

- [x] 2. Add session caching helper class





  - Create SessionCache internal class with cache validation logic
  - Implement IsValid() method checking 30-second expiration
  - Implement Update() method to store source IDs and timestamp
  - Implement GetCached() method to retrieve cached source list
  - _Requirements: 3.1, 3.4_

- [x] 3. Add diagnostic logging helper class





  - Create DiagnosticLogger internal class with counters
  - Implement LogSessionAccess() to track session enumeration
  - Implement LogHttpRequest() to track HTTP calls
  - Implement LogPeriodic() to output stats every 10 seconds
  - Add command-line argument parsing for --diagnostic flag
  - _Requirements: 6.1, 6.2, 6.3, 6.4_

- [x] 4. Fix session disposal in GetSessionBySource() method





  - Wrap session enumeration in try-catch-finally block
  - Dispose non-matching sessions immediately in foreach loop
  - Keep only the matched session alive (don't dispose return value)
  - Dispose all sessions in catch block on error
  - Add diagnostic logging for session access count
  - _Requirements: 2.1, 3.2, 3.5_

- [x] 5. Fix session disposal in SendAvailableSources() method





  - Add ShouldEnumerateSources() check at method start
  - Return early if cache is valid (skip enumeration)
  - Dispose each session immediately after reading properties
  - Update lastSourceEnumeration timestamp after successful enumeration
  - Update SessionCache with new source list
  - _Requirements: 3.1, 3.2, 3.3, 3.4_

- [x] 6. Fix session disposal in Tick() method





  - Dispose manager and intermediate sessions after GetSessionBySource call
  - Keep currentSession alive for the cycle duration
  - Dispose previous currentSession before assigning new one
  - Add using statement for session collections in error logging
  - _Requirements: 1.3, 2.1_

- [x] 7. Implement HTTP response disposal with semaphore





  - Add SemaphoreSlim field (limit 1 concurrent request)
  - Create SendHttpWithDisposalAsync() helper method
  - Wrap all HTTP calls with semaphore WaitAsync/Release
  - Use using statement for HttpResponseMessage disposal
  - Set 5-second timeout on HttpClient in constructor
  - Replace fire-and-forget PostAsync calls with awaited disposal pattern
  - _Requirements: 2.2, 4.1, 5.1, 5.2, 5.3, 5.5_

- [x] 8. Fix CancellationTokenSource disposal





  - Store old CTS reference before creating new one
  - Cancel old CTS before disposing
  - Dispose old CTS after cancellation
  - Apply pattern to all CTS creation points (track changes, LoadSelectedSource)
  - _Requirements: 2.3, 2.4_

- [x] 9. Fix Task.Run tracking and cancellation





  - Add activeTrackTask field to track running ProcessTrackChange task
  - Check if activeTrackTask is running before starting new one
  - Cancel and await previous task before starting new one
  - Handle cancellation exceptions gracefully
  - Ensure task completes or is cancelled properly
  - _Requirements: 4.2, 4.3, 4.4, 4.5_

- [x] 10. Add ConfigureAwait(false) to all async operations





  - Add ConfigureAwait(false) to all await statements in Tick()
  - Add ConfigureAwait(false) to all await statements in LoadSelectedSource()
  - Add ConfigureAwait(false) to all await statements in SendAvailableSources()
  - Add ConfigureAwait(false) to all await statements in ProcessTrackChange()
  - Add ConfigureAwait(false) to all await statements in HTTP methods
  - _Requirements: 4.1_

- [x] 11. Implement batched state updates





  - Modify SendUpdate() to enforce minimum 2-second interval
  - Change UPDATE_COOLDOWN constant from 0.1 to 2.0 seconds
  - Ensure force parameter bypasses cooldown only for critical updates
  - _Requirements: 5.1_

- [x] 12. Add HTTP error handling and retry logic





  - Wrap HTTP calls in try-catch for timeout exceptions
  - Remove immediate retry logic (wait for next cycle)
  - Log HTTP errors only in diagnostic mode
  - _Requirements: 5.4_

- [x] 13. Create integration test for long-running CPU stability





  - Write test harness that runs MediaMonitor for 1 hour
  - Measure CPU usage every 5 minutes
  - Assert CPU variance stays within 2% of baseline
  - Output diagnostic logs for analysis
  - _Requirements: 1.1_

- [x] 14. Create integration test for 24-hour memory stability




  - Write test harness that runs MediaMonitor for 24 hours
  - Measure memory usage and handle count every hour
  - Assert no memory growth beyond 5% variance
  - Assert handle count remains stable
  - _Requirements: 1.2_

- [x] 15. Update Program.cs to support diagnostic mode





  - Parse command-line arguments for --diagnostic flag
  - Pass diagnostic flag to MediaMonitor constructor
  - Update MediaMonitor constructor to accept diagnosticMode parameter
  - Initialize DiagnosticLogger based on flag
  - _Requirements: 6.4, 6.5_

- [x] 16. Add cleanup call in Program.cs shutdown





  - Wrap MediaMonitor.Start() in using statement
  - Add graceful shutdown handler (Ctrl+C)
  - Call Dispose() on MediaMonitor before exit
  - Log shutdown message
  - _Requirements: 2.5_
