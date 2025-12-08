# Implementation Plan

- [x] 1. Implement HealthMonitor component





  - Create HealthMonitor class with heartbeat timer and timeout detection
  - Implement RecordUpdate() method to track last update timestamp
  - Implement CheckHealth() method to detect 30-second timeout
  - Add HealthStatusChanged and RecoveryNeeded events
  - Add diagnostic logging for health status changes
  - _Requirements: 1.2, 2.5, 3.1_

- [ ]* 1.1 Write property test for HealthMonitor timeout detection
  - **Property 2: Recovery triggers on timeout**
  - **Validates: Requirements 3.1**

- [x] 2. Implement RecoveryManager component





  - Create RecoveryManager class with recovery procedure
  - Implement AttemptRecovery() method with step-by-step recovery
  - Implement UnsubscribeAll() to clean up existing subscriptions
  - Implement ReinitializeSessionManager() to recreate session manager
  - Implement ReestablishSubscriptions() to restore event handlers
  - Add recovery attempt counter with maximum limit (3 attempts)
  - Add diagnostic logging for each recovery step
  - _Requirements: 1.3, 1.5, 3.2, 3.3, 3.4, 3.5_

- [ ]* 2.1 Write property test for event subscription cleanup
  - **Property 3: Event subscription cleanup**
  - **Validates: Requirements 1.5**

- [ ]* 2.2 Write property test for recovery success verification
  - **Property 8: Recovery success verification**
  - **Validates: Requirements 3.5**

- [x] 3. Implement EventSubscriptionManager component





  - Create EventSubscriptionManager class to centralize subscription management
  - Implement Subscribe() method with diagnostic logging
  - Implement Unsubscribe() method with cleanup verification
  - Add event handler wrappers with timestamp and duration logging
  - Implement IsHealthy property to check subscription status
  - Add MediaUpdated event to propagate updates to MediaMonitor
  - _Requirements: 1.1, 2.1, 2.4_

- [ ]* 3.1 Write property test for diagnostic logging completeness
  - **Property 6: Diagnostic logging completeness**
  - **Validates: Requirements 2.1, 2.2, 2.3, 2.4**

- [x] 4. Implement UpdateQueue with timeout-protected locks





  - Create UpdateQueue class with debounce timer
  - Modify lock acquisition to use WaitAsync(timeout) with 5-second timeout
  - Add timeout logging when lock cannot be acquired
  - Implement update skipping when timeout occurs
  - Add counter for repeated timeouts to trigger recovery
  - _Requirements: 5.1, 5.3, 5.5_

- [ ]* 4.1 Write property test for lock timeout prevention
  - **Property 4: Lock timeout prevents deadlock**
  - **Validates: Requirements 5.1, 5.2, 5.3**

- [x] 5. Implement HttpClientPool with retry logic





  - Create HttpClientPool class with semaphore and timeout
  - Implement SendUpdate() with timeout-protected semaphore acquisition
  - Implement SendWithRetry() with exponential backoff (100ms, 500ms, 1000ms)
  - Add semaphore release in finally block to guarantee release
  - Add diagnostic logging for all HTTP requests with timing
  - _Requirements: 2.2, 5.2, 5.4_

- [ ]* 5.1 Write property test for HTTP semaphore release guarantee
  - **Property 7: HTTP semaphore release guarantee**
  - **Validates: Requirements 5.4**

- [x] 6. Implement IsolatedConfigPoller component





  - Create IsolatedConfigPoller class with dedicated HttpClient
  - Implement PollConfiguration() method with error isolation
  - Implement change queue (ConcurrentQueue) for non-blocking updates
  - Implement ProcessQueuedChanges() with debouncing (minimum 2 seconds)
  - Add SourceChanged event for configuration updates
  - Add error handling that doesn't propagate to main event loop
  - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5_

- [ ]* 6.1 Write property test for ConfigPoller isolation
  - **Property 5: ConfigPoller isolation**
  - **Validates: Requirements 4.2**

- [x] 7. Integrate all components into MediaMonitor





  - Replace inline health checking with HealthMonitor
  - Replace inline recovery with RecoveryManager
  - Replace direct event subscriptions with EventSubscriptionManager
  - Replace debounce timer with UpdateQueue
  - Replace direct HTTP calls with HttpClientPool
  - Replace inline ConfigPoller with IsolatedConfigPoller
  - Wire up all event handlers between components
  - _Requirements: 1.1, 1.2, 1.3_

- [ ]* 7.1 Write property test for update continuity
  - **Property 1: Update continuity under normal operation**
  - **Validates: Requirements 1.1, 1.2**

- [x] 8. Add diagnostic mode command-line flag





  - Add --diagnostic command-line argument parsing
  - Enable verbose logging when diagnostic mode is active
  - Add log file output for diagnostic mode
  - Add console output formatting for readability
  - _Requirements: 1.4, 2.1, 2.2, 2.3, 2.4, 2.5_

- [x] 9. Update Dispose() method for new components





  - Add disposal for HealthMonitor timer
  - Add disposal for RecoveryManager resources
  - Add disposal for EventSubscriptionManager
  - Add disposal for UpdateQueue timer and semaphore
  - Add disposal for HttpClientPool client and semaphore
  - Add disposal for IsolatedConfigPoller timer and client
  - Verify all resources are properly cleaned up
  - _Requirements: 1.5, 4.5_

- [x] 10. Checkpoint - Ensure all tests pass





  - Ensure all tests pass, ask the user if questions arise.

- [x] 11. Create extended operation integration test





  - Create test that runs MediaMonitor for 30 minutes
  - Simulate media changes every 30 seconds
  - Verify continuous update flow with no gaps > 5 seconds
  - Verify no memory leaks using process memory monitoring
  - Log test results with update count and any detected issues
  - _Requirements: 1.2, 6.1, 6.2, 6.3, 6.4, 6.5_

- [ ]* 11.1 Write unit tests for extended operation test harness
  - Test media change simulation
  - Test gap detection logic
  - Test memory leak detection

- [x] 12. Create recovery simulation integration test





  - Create test that forces event subscription failure
  - Verify automatic recovery is triggered
  - Verify updates resume within 10 seconds after recovery
  - Test multiple recovery cycles
  - Log recovery timing and success rate
  - _Requirements: 1.3, 3.1, 3.5_

- [ ]* 12.1 Write unit tests for recovery simulation test harness
  - Test subscription failure injection
  - Test recovery detection logic
  - Test update resumption verification

- [x] 13. Create stress test for high-frequency updates





  - Create test with rapid media changes (every 2 seconds)
  - Run for 10 minutes with continuous changes
  - Verify no updates are lost
  - Verify system remains responsive
  - Log update success rate and any timeouts
  - _Requirements: 1.1, 5.1, 5.2_

- [ ]* 13.1 Write unit tests for stress test harness
  - Test rapid change generation
  - Test update loss detection
  - Test responsiveness measurement

- [x] 14. Create ConfigPoller isolation integration test




  - Create test that simulates ConfigPoller failures
  - Verify media updates continue unaffected during failures
  - Verify configuration eventually syncs after failures stop
  - Log isolation effectiveness metrics
  - _Requirements: 4.2, 4.3_

- [ ]* 14.1 Write unit tests for ConfigPoller isolation test harness
  - Test failure injection
  - Test media update continuity verification
  - Test configuration sync detection

- [x] 15. Update documentation





  - Update MediaMonitor/README.md with new architecture
  - Document diagnostic mode usage
  - Document recovery behavior
  - Add troubleshooting guide for common issues
  - Update API documentation for new components
  - _Requirements: 1.4, 2.5_

- [ ] 16. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.
