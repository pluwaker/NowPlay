using System;
using System.Diagnostics;
using System.Threading.Tasks;
using Windows.Media.Control;

namespace NowMediaMonitor
{
    /// <summary>
    /// Event arguments for media update events
    /// </summary>
    public class MediaUpdateEventArgs : EventArgs
    {
        public string Artist { get; set; } = string.Empty;
        public string Title { get; set; } = string.Empty;
        public double Position { get; set; }
        public double Duration { get; set; }
        public bool IsPlaying { get; set; }
        public string SourceId { get; set; } = string.Empty;
        public DateTime Timestamp { get; set; }
    }

    /// <summary>
    /// Centralizes event subscription lifecycle management with enhanced logging
    /// </summary>
    public class EventSubscriptionManager : IDisposable
    {
        private GlobalSystemMediaTransportControlsSession? currentSession;
        private bool isSubscribed = false;
        private readonly object lockObject = new object();
        
        // Events
        public event EventHandler<MediaUpdateEventArgs>? MediaUpdated;
        
        /// <summary>
        /// Gets whether the subscription manager is healthy (has active subscriptions)
        /// </summary>
        public bool IsHealthy
        {
            get
            {
                lock (lockObject)
                {
                    return isSubscribed && currentSession != null;
                }
            }
        }
        
        /// <summary>
        /// Subscribes to events from the specified session with diagnostic logging
        /// </summary>
        public async Task Subscribe(GlobalSystemMediaTransportControlsSession session)
        {
            if (session == null)
            {
                throw new ArgumentNullException(nameof(session));
            }
            
            await Task.Run(() =>
            {
                lock (lockObject)
                {
                    // Unsubscribe from previous session if any
                    if (isSubscribed && currentSession != null)
                    {
                        Console.WriteLine($"📤 EventSubscriptionManager: Unsubscribing from previous session");
                        UnsubscribeInternal();
                    }
                    
                    currentSession = session;
                    
                    try
                    {
                        var appId = session.SourceAppUserModelId ?? "unknown";
                        Console.WriteLine($"📥 EventSubscriptionManager: Subscribing to session: {appId}");
                        Console.WriteLine($"⏰ Subscription timestamp: {DateTime.Now:HH:mm:ss.fff}");
                        
                        DiagnosticLogger.LogSubscription("Subscribe", appId);
                        
                        // Subscribe to all media events
                        session.MediaPropertiesChanged += OnMediaPropertiesChanged;
                        Console.WriteLine($"  ✅ Subscribed to MediaPropertiesChanged");
                        DiagnosticLogger.LogSubscription("Subscribe", appId, "MediaPropertiesChanged");
                        
                        session.PlaybackInfoChanged += OnPlaybackInfoChanged;
                        Console.WriteLine($"  ✅ Subscribed to PlaybackInfoChanged");
                        DiagnosticLogger.LogSubscription("Subscribe", appId, "PlaybackInfoChanged");
                        
                        session.TimelinePropertiesChanged += OnTimelinePropertiesChanged;
                        Console.WriteLine($"  ✅ Subscribed to TimelinePropertiesChanged");
                        DiagnosticLogger.LogSubscription("Subscribe", appId, "TimelinePropertiesChanged");
                        
                        isSubscribed = true;
                        Console.WriteLine($"✅ EventSubscriptionManager: All subscriptions established");
                    }
                    catch (Exception ex)
                    {
                        Console.WriteLine($"❌ EventSubscriptionManager: Subscription failed: {ex.Message}");
                        isSubscribed = false;
                        throw;
                    }
                }
            });
        }
        
        /// <summary>
        /// Unsubscribes from all events with cleanup verification
        /// </summary>
        public void Unsubscribe()
        {
            lock (lockObject)
            {
                if (!isSubscribed || currentSession == null)
                {
                    Console.WriteLine($"ℹ️ EventSubscriptionManager: No active subscriptions to unsubscribe");
                    return;
                }
                
                Console.WriteLine($"📤 EventSubscriptionManager: Starting unsubscribe process");
                Console.WriteLine($"⏰ Unsubscribe timestamp: {DateTime.Now:HH:mm:ss.fff}");
                
                UnsubscribeInternal();
                
                Console.WriteLine($"✅ EventSubscriptionManager: Cleanup verification complete");
            }
        }
        
        /// <summary>
        /// Internal unsubscribe logic (must be called within lock)
        /// </summary>
        private void UnsubscribeInternal()
        {
            if (currentSession == null)
            {
                return;
            }
            
            try
            {
                var appId = currentSession.SourceAppUserModelId ?? "unknown";
                Console.WriteLine($"  - Unsubscribing from session: {appId}");
                
                DiagnosticLogger.LogSubscription("Unsubscribe", appId);
                
                currentSession.MediaPropertiesChanged -= OnMediaPropertiesChanged;
                Console.WriteLine($"  ✅ Unsubscribed from MediaPropertiesChanged");
                DiagnosticLogger.LogSubscription("Unsubscribe", appId, "MediaPropertiesChanged");
                
                currentSession.PlaybackInfoChanged -= OnPlaybackInfoChanged;
                Console.WriteLine($"  ✅ Unsubscribed from PlaybackInfoChanged");
                DiagnosticLogger.LogSubscription("Unsubscribe", appId, "PlaybackInfoChanged");
                
                currentSession.TimelinePropertiesChanged -= OnTimelinePropertiesChanged;
                Console.WriteLine($"  ✅ Unsubscribed from TimelinePropertiesChanged");
                DiagnosticLogger.LogSubscription("Unsubscribe", appId, "TimelinePropertiesChanged");
                
                currentSession = null;
                isSubscribed = false;
            }
            catch (Exception ex)
            {
                Console.WriteLine($"⚠️ EventSubscriptionManager: Warning during unsubscribe: {ex.Message}");
                // Continue with cleanup even if unsubscribe fails
                currentSession = null;
                isSubscribed = false;
            }
        }
        
        /// <summary>
        /// Event handler for MediaPropertiesChanged with timestamp and duration logging
        /// </summary>
        private void OnMediaPropertiesChanged(GlobalSystemMediaTransportControlsSession sender, MediaPropertiesChangedEventArgs args)
        {
            var stopwatch = Stopwatch.StartNew();
            var timestamp = DateTime.Now;
            
            try
            {
                Console.WriteLine($"🎵 Event: MediaPropertiesChanged at {timestamp:HH:mm:ss.fff}");
                
                // Propagate event to MediaMonitor
                _ = Task.Run(async () =>
                {
                    try
                    {
                        var mediaInfo = await sender.TryGetMediaPropertiesAsync();
                        var timeline = sender.GetTimelineProperties();
                        var playback = sender.GetPlaybackInfo();
                        
                        var updateArgs = new MediaUpdateEventArgs
                        {
                            Artist = mediaInfo.Artist ?? "Unknown Artist",
                            Title = mediaInfo.Title ?? "Unknown Title",
                            Position = timeline?.Position.TotalSeconds ?? 0,
                            Duration = timeline?.EndTime.TotalSeconds ?? 0,
                            IsPlaying = playback.PlaybackStatus == GlobalSystemMediaTransportControlsSessionPlaybackStatus.Playing,
                            SourceId = sender.SourceAppUserModelId ?? "",
                            Timestamp = timestamp
                        };
                        
                        OnMediaUpdated(updateArgs);
                        
                        stopwatch.Stop();
                        Console.WriteLine($"  ⏱ Handler execution time: {stopwatch.ElapsedMilliseconds}ms");
                        DiagnosticLogger.LogEvent("EventSubscriptionManager", "MediaPropertiesChanged", 
                            $"{updateArgs.Artist} - {updateArgs.Title}", stopwatch.ElapsedMilliseconds);
                    }
                    catch (Exception ex)
                    {
                        Console.WriteLine($"  ❌ Error in MediaPropertiesChanged handler: {ex.Message}");
                    }
                });
            }
            catch (Exception ex)
            {
                stopwatch.Stop();
                Console.WriteLine($"  ❌ Error in MediaPropertiesChanged event: {ex.Message}");
                Console.WriteLine($"  ⏱ Handler execution time: {stopwatch.ElapsedMilliseconds}ms");
            }
        }
        
        /// <summary>
        /// Event handler for PlaybackInfoChanged with timestamp and duration logging
        /// </summary>
        private void OnPlaybackInfoChanged(GlobalSystemMediaTransportControlsSession sender, PlaybackInfoChangedEventArgs args)
        {
            var stopwatch = Stopwatch.StartNew();
            var timestamp = DateTime.Now;
            
            try
            {
                Console.WriteLine($"▶️ Event: PlaybackInfoChanged at {timestamp:HH:mm:ss.fff}");
                
                // Propagate event to MediaMonitor
                _ = Task.Run(async () =>
                {
                    try
                    {
                        var mediaInfo = await sender.TryGetMediaPropertiesAsync();
                        var timeline = sender.GetTimelineProperties();
                        var playback = sender.GetPlaybackInfo();
                        
                        bool isPlaying = playback.PlaybackStatus == GlobalSystemMediaTransportControlsSessionPlaybackStatus.Playing;
                        Console.WriteLine($"  - Playback status: {(isPlaying ? "Playing" : "Paused")}");
                        
                        var updateArgs = new MediaUpdateEventArgs
                        {
                            Artist = mediaInfo.Artist ?? "Unknown Artist",
                            Title = mediaInfo.Title ?? "Unknown Title",
                            Position = timeline?.Position.TotalSeconds ?? 0,
                            Duration = timeline?.EndTime.TotalSeconds ?? 0,
                            IsPlaying = isPlaying,
                            SourceId = sender.SourceAppUserModelId ?? "",
                            Timestamp = timestamp
                        };
                        
                        OnMediaUpdated(updateArgs);
                        
                        stopwatch.Stop();
                        Console.WriteLine($"  ⏱ Handler execution time: {stopwatch.ElapsedMilliseconds}ms");
                        DiagnosticLogger.LogEvent("EventSubscriptionManager", "PlaybackInfoChanged", 
                            isPlaying ? "Playing" : "Paused", stopwatch.ElapsedMilliseconds);
                    }
                    catch (Exception ex)
                    {
                        Console.WriteLine($"  ❌ Error in PlaybackInfoChanged handler: {ex.Message}");
                    }
                });
            }
            catch (Exception ex)
            {
                stopwatch.Stop();
                Console.WriteLine($"  ❌ Error in PlaybackInfoChanged event: {ex.Message}");
                Console.WriteLine($"  ⏱ Handler execution time: {stopwatch.ElapsedMilliseconds}ms");
            }
        }
        
        /// <summary>
        /// Event handler for TimelinePropertiesChanged with timestamp and duration logging
        /// </summary>
        private void OnTimelinePropertiesChanged(GlobalSystemMediaTransportControlsSession sender, TimelinePropertiesChangedEventArgs args)
        {
            var stopwatch = Stopwatch.StartNew();
            var timestamp = DateTime.Now;
            
            try
            {
                Console.WriteLine($"⏱ Event: TimelinePropertiesChanged at {timestamp:HH:mm:ss.fff}");
                
                // Propagate event to MediaMonitor
                _ = Task.Run(async () =>
                {
                    try
                    {
                        var mediaInfo = await sender.TryGetMediaPropertiesAsync();
                        var timeline = sender.GetTimelineProperties();
                        var playback = sender.GetPlaybackInfo();
                        
                        if (timeline != null)
                        {
                            double position = timeline.Position.TotalSeconds;
                            double duration = timeline.EndTime.TotalSeconds;
                            
                            Console.WriteLine($"  - Position: {position:F1}s / Duration: {duration:F1}s");
                            
                            var updateArgs = new MediaUpdateEventArgs
                            {
                                Artist = mediaInfo.Artist ?? "Unknown Artist",
                                Title = mediaInfo.Title ?? "Unknown Title",
                                Position = position,
                                Duration = duration,
                                IsPlaying = playback.PlaybackStatus == GlobalSystemMediaTransportControlsSessionPlaybackStatus.Playing,
                                SourceId = sender.SourceAppUserModelId ?? "",
                                Timestamp = timestamp
                            };
                            
                            OnMediaUpdated(updateArgs);
                            
                            DiagnosticLogger.LogEvent("EventSubscriptionManager", "TimelinePropertiesChanged", 
                                $"Position: {position:F1}s / Duration: {duration:F1}s", stopwatch.ElapsedMilliseconds);
                        }
                        
                        stopwatch.Stop();
                        Console.WriteLine($"  ⏱ Handler execution time: {stopwatch.ElapsedMilliseconds}ms");
                    }
                    catch (Exception ex)
                    {
                        Console.WriteLine($"  ❌ Error in TimelinePropertiesChanged handler: {ex.Message}");
                    }
                });
            }
            catch (Exception ex)
            {
                stopwatch.Stop();
                Console.WriteLine($"  ❌ Error in TimelinePropertiesChanged event: {ex.Message}");
                Console.WriteLine($"  ⏱ Handler execution time: {stopwatch.ElapsedMilliseconds}ms");
            }
        }
        
        /// <summary>
        /// Raises the MediaUpdated event
        /// </summary>
        private void OnMediaUpdated(MediaUpdateEventArgs e)
        {
            Console.WriteLine($"🔔 OnMediaUpdated вызван: {e.Artist} - {e.Title}, Position: {e.Position:F1}s, IsPlaying: {e.IsPlaying}");
            Console.WriteLine($"   Подписчиков на MediaUpdated: {MediaUpdated?.GetInvocationList().Length ?? 0}");
            MediaUpdated?.Invoke(this, e);
            Console.WriteLine($"   MediaUpdated.Invoke завершен");
        }
        
        // IDisposable implementation
        private bool disposed = false;
        
        public void Dispose()
        {
            Dispose(true);
            GC.SuppressFinalize(this);
        }
        
        protected virtual void Dispose(bool disposing)
        {
            if (!disposed)
            {
                if (disposing)
                {
                    Unsubscribe();
                    Console.WriteLine("🧹 EventSubscriptionManager disposed");
                }
                disposed = true;
            }
        }
    }
}
