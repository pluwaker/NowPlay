using System;
using System.Collections.Concurrent;
using System.Net.Http;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;

namespace NowMediaMonitor
{
    /// <summary>
    /// Isolated configuration poller that monitors configuration changes without blocking the main event loop.
    /// Uses a dedicated HTTP client and queues changes for non-blocking processing.
    /// </summary>
    public class IsolatedConfigPoller : IDisposable
    {
        private readonly HttpClient dedicatedClient;
        private readonly Timer pollerTimer;
        private readonly ConcurrentQueue<string> sourceChangeQueue;
        private string lastKnownSource = "";
        private readonly string pythonServerUrl;
        private DateTime lastChangeProcessed = DateTime.MinValue;
        private const int POLL_INTERVAL_MS = 2000;
        private const double DEBOUNCE_SECONDS = 2.0;
        private bool disposed = false;

        /// <summary>
        /// Event fired when the selected media source changes in configuration.
        /// </summary>
        public event EventHandler<SourceChangedEventArgs>? SourceChanged;

        public IsolatedConfigPoller(string serverUrl)
        {
            pythonServerUrl = serverUrl;
            sourceChangeQueue = new ConcurrentQueue<string>();
            
            // Dedicated HTTP client with timeout for isolation
            dedicatedClient = new HttpClient
            {
                Timeout = TimeSpan.FromSeconds(5)
            };

            // Initialize polling timer
            pollerTimer = new Timer(
                OnPollerTimerElapsed,
                null,
                POLL_INTERVAL_MS,
                POLL_INTERVAL_MS
            );
        }

        /// <summary>
        /// Starts the configuration poller.
        /// </summary>
        public void Start()
        {
            Console.WriteLine("✅ IsolatedConfigPoller started");
        }

        /// <summary>
        /// Stops the configuration poller.
        /// </summary>
        public void Stop()
        {
            pollerTimer.Change(Timeout.Infinite, Timeout.Infinite);
            Console.WriteLine("⏸️ IsolatedConfigPoller stopped");
        }

        private void OnPollerTimerElapsed(object? state)
        {
            // Run polling asynchronously without blocking
            _ = Task.Run(async () =>
            {
                try
                {
                    await PollConfiguration();
                    ProcessQueuedChanges();
                }
                catch (Exception ex)
                {
                    // Error isolation: log but don't propagate to main event loop
                    Console.WriteLine($"⚠️ ConfigPoller error (isolated): {ex.Message}");
                }
            });
        }

        /// <summary>
        /// Polls the configuration from the Python server with error isolation.
        /// Errors in this method do not propagate to the main event loop.
        /// </summary>
        private async Task PollConfiguration()
        {
            try
            {
                using var response = await dedicatedClient
                    .GetAsync($"{pythonServerUrl}/get_config")
                    .ConfigureAwait(false);

                if (response.IsSuccessStatusCode)
                {
                    var json = await response.Content.ReadAsStringAsync().ConfigureAwait(false);
                    var config = JsonSerializer.Deserialize<JsonElement>(json);

                    if (config.TryGetProperty("selected_media_source", out var source))
                    {
                        string newSource = source.GetString() ?? "auto";

                        // Check if source changed
                        if (newSource != lastKnownSource)
                        {
                            Console.WriteLine($"🔄 ConfigPoller detected change: {lastKnownSource} → {newSource}");
                            
                            // Queue the change for non-blocking processing
                            sourceChangeQueue.Enqueue(newSource);
                            lastKnownSource = newSource;
                        }
                    }
                }
            }
            catch (HttpRequestException ex)
            {
                // Server unavailable - isolated error, don't propagate
                Console.WriteLine($"⚠️ ConfigPoller HTTP error (isolated): {ex.Message}");
            }
            catch (TaskCanceledException)
            {
                // Timeout - isolated error, don't propagate
                Console.WriteLine("⚠️ ConfigPoller timeout (isolated)");
            }
            catch (Exception ex)
            {
                // Any other error - isolated, don't propagate
                Console.WriteLine($"⚠️ ConfigPoller unexpected error (isolated): {ex.Message}");
            }
        }

        /// <summary>
        /// Processes queued configuration changes with debouncing.
        /// Ensures minimum 2 seconds between processing changes to prevent thrashing.
        /// </summary>
        private void ProcessQueuedChanges()
        {
            // Debounce: ensure minimum time between processing changes
            var timeSinceLastChange = (DateTime.Now - lastChangeProcessed).TotalSeconds;
            if (timeSinceLastChange < DEBOUNCE_SECONDS)
            {
                return;
            }

            // Process only the most recent change
            string? latestSource = null;
            while (sourceChangeQueue.TryDequeue(out var source))
            {
                latestSource = source;
            }

            if (latestSource != null)
            {
                lastChangeProcessed = DateTime.Now;
                
                // Fire event with the latest source change
                try
                {
                    SourceChanged?.Invoke(this, new SourceChangedEventArgs(latestSource));
                    Console.WriteLine($"✅ ConfigPoller processed source change: {latestSource}");
                }
                catch (Exception ex)
                {
                    // Event handler error - log but don't crash
                    Console.WriteLine($"⚠️ Error in SourceChanged event handler: {ex.Message}");
                }
            }
        }

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
                    try
                    {
                        // Stop the timer
                        pollerTimer?.Dispose();
                        
                        // Dispose dedicated HTTP client
                        dedicatedClient?.Dispose();
                        
                        Console.WriteLine("🧹 IsolatedConfigPoller resources cleaned up");
                    }
                    catch (Exception ex)
                    {
                        Console.WriteLine($"⚠️ Error during IsolatedConfigPoller cleanup: {ex.Message}");
                    }
                }

                disposed = true;
            }
        }
    }

    /// <summary>
    /// Event arguments for source change events.
    /// </summary>
    public class SourceChangedEventArgs : EventArgs
    {
        public string NewSource { get; }

        public SourceChangedEventArgs(string newSource)
        {
            NewSource = newSource;
        }
    }
}