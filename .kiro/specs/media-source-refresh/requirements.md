# Requirements Document

## Introduction

This document specifies requirements for fixing the media track update freeze issue in the NowPlay application. After some time of operation, the system stops receiving new track updates from Windows Media API, even though media is actively playing and changing in Windows. The C# MediaMonitor continues to detect available sources but fails to propagate track changes to the Python server.

## Glossary

- **MediaMonitor**: The C# component that monitors Windows Media API for track changes
- **Event Subscription**: WinRT event handlers attached to GlobalSystemMediaTransportControlsSession
- **Debounce Timer**: A timer mechanism that batches updates to reduce HTTP request frequency
- **HTTP Semaphore**: A synchronization primitive limiting concurrent HTTP requests
- **Session Manager**: GlobalSystemMediaTransportControlsSessionManager that provides access to media sessions
- **Track Update**: Information about currently playing media (artist, title, position, duration, playback state)

## Requirements

### Requirement 1

**User Story:** As a user, I want the application to continuously receive track updates without freezing, so that I always see current media information.

#### Acceptance Criteria

1. WHEN media tracks change in Windows THEN the MediaMonitor SHALL detect and propagate these changes to the Python server
2. WHEN the application runs for extended periods THEN the MediaMonitor SHALL maintain active event subscriptions without degradation
3. WHEN event subscriptions fail THEN the MediaMonitor SHALL detect the failure and re-establish subscriptions
4. WHEN track updates stop flowing THEN the system SHALL log diagnostic information indicating the failure point
5. WHEN the MediaMonitor restarts event subscriptions THEN existing listeners SHALL be properly cleaned up to prevent memory leaks

### Requirement 2

**User Story:** As a developer, I want comprehensive diagnostics for event subscription health, so that I can identify when and why track updates stop flowing.

#### Acceptance Criteria

1. WHEN event handlers are invoked THEN the MediaMonitor SHALL log the event type and timestamp
2. WHEN HTTP requests are sent THEN the MediaMonitor SHALL log request success/failure with timing information
3. WHEN the debounce timer fires THEN the MediaMonitor SHALL log whether updates were pending
4. WHEN event subscriptions are established or removed THEN the MediaMonitor SHALL log subscription lifecycle events
5. WHEN the system detects no updates for a configurable threshold THEN the MediaMonitor SHALL log a warning and attempt recovery

### Requirement 3

**User Story:** As a user, I want the system to automatically recover from event subscription failures, so that I don't need to manually restart the application.

#### Acceptance Criteria

1. WHEN no track updates are received for 30 seconds THEN the MediaMonitor SHALL trigger an automatic recovery procedure
2. WHEN recovery is triggered THEN the MediaMonitor SHALL unsubscribe from all current events
3. WHEN recovery is triggered THEN the MediaMonitor SHALL re-initialize the session manager
4. WHEN recovery is triggered THEN the MediaMonitor SHALL re-establish event subscriptions
5. WHEN recovery completes THEN the MediaMonitor SHALL log the recovery outcome (success or failure)

### Requirement 4

**User Story:** As a developer, I want to isolate the ConfigPoller from the main event loop, so that configuration polling doesn't interfere with track updates.

#### Acceptance Criteria

1. WHEN ConfigPoller checks for configuration changes THEN it SHALL use a separate HTTP client instance
2. WHEN ConfigPoller operations fail THEN failures SHALL NOT block the main event processing loop
3. WHEN ConfigPoller detects source changes THEN it SHALL queue the change for processing rather than blocking
4. WHEN multiple configuration changes occur rapidly THEN the ConfigPoller SHALL debounce changes to prevent thrashing
5. WHEN ConfigPoller is disposed THEN it SHALL properly clean up its timer and HTTP resources

### Requirement 5

**User Story:** As a developer, I want to ensure the debounce timer and HTTP semaphore cannot deadlock, so that updates always flow through the system.

#### Acceptance Criteria

1. WHEN the debounce timer fires THEN it SHALL use a timeout when acquiring the update lock
2. WHEN acquiring the HTTP semaphore THEN the MediaMonitor SHALL use a timeout to prevent indefinite blocking
3. WHEN a timeout occurs acquiring locks THEN the MediaMonitor SHALL log the timeout and skip the update
4. WHEN HTTP requests timeout THEN the MediaMonitor SHALL release the semaphore and allow subsequent requests
5. WHEN the system detects repeated lock timeouts THEN it SHALL trigger the recovery procedure

### Requirement 6

**User Story:** As a developer, I want to verify event subscription health through automated tests, so that I can detect subscription failures before deployment.

#### Acceptance Criteria

1. WHEN running stability tests THEN the test SHALL simulate extended operation periods (minimum 5 minutes)
2. WHEN running stability tests THEN the test SHALL verify continuous track update flow
3. WHEN running stability tests THEN the test SHALL inject simulated media changes at regular intervals
4. WHEN running stability tests THEN the test SHALL detect gaps in update flow exceeding 5 seconds
5. WHEN stability tests complete THEN they SHALL report the number of successful updates and any detected gaps
