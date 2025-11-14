# Requirements Document

## Introduction

This specification addresses the critical issue of increasing CPU usage over time in the MediaMonitor C# component. The system currently experiences resource leaks that cause CPU consumption to grow continuously during operation, impacting system performance and user experience. The goal is to identify and eliminate resource leaks, optimize polling mechanisms, and implement proper resource disposal patterns.

## Glossary

- **MediaMonitor**: The C# component responsible for monitoring Windows media sessions via SMTC API
- **SMTC**: System Media Transport Controls - Windows API for media session management
- **HttpClient**: .NET HTTP client used for communication with Python server
- **Session**: A GlobalSystemMediaTransportControlsSession object representing an active media player
- **Resource Leak**: Failure to properly dispose of system resources leading to memory/CPU accumulation
- **Polling Interval**: The time delay between consecutive monitoring cycles

## Requirements

### Requirement 1

**User Story:** As a user running MediaMonitor continuously, I want the CPU usage to remain stable over time, so that my system performance is not degraded during extended use

#### Acceptance Criteria

1. WHEN MediaMonitor runs for 1 hour, THE MediaMonitor SHALL maintain CPU usage within 2% variance of initial baseline
2. WHEN MediaMonitor runs for 24 hours, THE MediaMonitor SHALL maintain CPU usage within 5% variance of initial baseline
3. THE MediaMonitor SHALL dispose of all Session objects after each monitoring cycle
4. THE MediaMonitor SHALL reuse the HttpClient instance without creating new instances per request
5. THE MediaMonitor SHALL implement IDisposable pattern for proper resource cleanup

### Requirement 2

**User Story:** As a developer maintaining MediaMonitor, I want proper resource disposal patterns implemented, so that no system resources leak over time

#### Acceptance Criteria

1. WHEN a Session object is obtained, THE MediaMonitor SHALL dispose of it before the next monitoring cycle
2. WHEN HttpClient sends a request, THE MediaMonitor SHALL properly dispose of HttpContent objects
3. WHEN CancellationTokenSource is created, THE MediaMonitor SHALL dispose of previous instances before creating new ones
4. THE MediaMonitor SHALL implement using statements or try-finally blocks for all IDisposable resources
5. WHEN MediaMonitor shuts down, THE MediaMonitor SHALL dispose of all held resources in a cleanup method

### Requirement 3

**User Story:** As a user with multiple media sources, I want efficient session enumeration, so that CPU usage remains minimal when checking available sources

#### Acceptance Criteria

1. WHEN enumerating sessions, THE MediaMonitor SHALL cache session list for 5 seconds minimum
2. THE MediaMonitor SHALL dispose of each enumerated Session object immediately after reading properties
3. WHEN no session changes occur, THE MediaMonitor SHALL skip re-enumeration of available sources
4. THE MediaMonitor SHALL limit source enumeration to once per 30 seconds maximum
5. WHEN GetSessions is called, THE MediaMonitor SHALL dispose of the returned session collection

### Requirement 4

**User Story:** As a system administrator, I want MediaMonitor to use async operations efficiently, so that thread pool resources are not exhausted

#### Acceptance Criteria

1. THE MediaMonitor SHALL use ConfigureAwait(false) on all await operations to prevent context capture
2. WHEN multiple async operations are pending, THE MediaMonitor SHALL cancel previous operations before starting new ones
3. THE MediaMonitor SHALL limit concurrent async operations to 1 per operation type
4. WHEN Task.Run is used, THE MediaMonitor SHALL ensure the task completes or is cancelled properly
5. THE MediaMonitor SHALL not create fire-and-forget tasks without proper cancellation handling

### Requirement 5

**User Story:** As a user, I want minimal HTTP communication overhead, so that network operations do not contribute to CPU growth

#### Acceptance Criteria

1. THE MediaMonitor SHALL batch state updates to send maximum once per 2 seconds
2. WHEN sending HTTP requests, THE MediaMonitor SHALL set appropriate timeout values of 5 seconds maximum
3. THE MediaMonitor SHALL use fire-and-forget pattern only for non-critical updates with proper error handling
4. WHEN HTTP request fails, THE MediaMonitor SHALL not retry immediately but wait for next cycle
5. THE MediaMonitor SHALL dispose of HttpResponseMessage objects when responses are read

### Requirement 6

**User Story:** As a developer debugging CPU issues, I want diagnostic logging for resource usage, so that I can identify remaining bottlenecks

#### Acceptance Criteria

1. WHEN diagnostic mode is enabled, THE MediaMonitor SHALL log active Session object count every 10 seconds
2. WHEN diagnostic mode is enabled, THE MediaMonitor SHALL log HttpClient request count per minute
3. WHEN diagnostic mode is enabled, THE MediaMonitor SHALL log memory usage delta every 30 seconds
4. THE MediaMonitor SHALL provide a command-line flag to enable diagnostic mode
5. WHEN diagnostic mode is disabled, THE MediaMonitor SHALL produce minimal console output to reduce I/O overhead
