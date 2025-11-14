using System;
using System.Collections.Generic;
using System.Runtime.InteropServices;
using System.Threading;
using System.Threading.Tasks;
using System.IO;
using System.Net.Http;
using System.Text;
using System.Text.Json;
using WinRT;
using Windows.Media.Control;
using Windows.Storage.Streams;

namespace NowMediaMonitor
{
    public class MediaMonitor : IDisposable
    {
        public CurrentMediaState State = new();

        private GlobalSystemMediaTransportControlsSession? currentSession;
        private CancellationTokenSource? trackTaskCTS;
        private Task? activeTrackTask = null;

        private DateTime lastUpdate = DateTime.MinValue;
        private readonly double UPDATE_COOLDOWN = 2.0;

        private readonly HttpClient httpClient = new HttpClient();
        private readonly string pythonServerUrl = "http://localhost:8080";
        
        // Для отслеживания изменений
        private double lastPosition = 0;
        private bool lastIsPlaying = false;
        private string selectedSource = "";
        private bool hasLoggedNoSession = false; // Чтобы не спамить логами
        
        // IDisposable pattern
        private bool disposed = false;

        // Diagnostic logging
        private readonly DiagnosticLogger diagnosticLogger;
        
        // Session caching to reduce expensive enumeration
        private readonly SessionCache sessionCache = new SessionCache();
        private DateTime lastSourceEnumeration = DateTime.MinValue;
        private const int SOURCE_CACHE_SECONDS = 30;
        
        // HTTP semaphore to limit concurrent requests
        private readonly SemaphoreSlim httpSemaphore = new SemaphoreSlim(1, 1);

        public MediaMonitor(bool diagnosticMode = false)
        {
            diagnosticLogger = new DiagnosticLogger(diagnosticMode);
            
            // Set 5-second timeout on HttpClient
            httpClient.Timeout = TimeSpan.FromSeconds(5);
        }

        /// <summary>
        /// Helper method to send HTTP requests with proper response disposal and semaphore control
        /// </summary>
        /// <param name="requestFunc">Function that creates and sends the HTTP request</param>
        /// <returns>Task that completes when the request is sent and response is disposed</returns>
        private async Task SendHttpWithDisposalAsync(Func<Task<HttpResponseMessage>> requestFunc)
        {
            await httpSemaphore.WaitAsync().ConfigureAwait(false);
            try
            {
                using var response = await requestFunc().ConfigureAwait(false);
                // Response is automatically disposed here
            }
            catch (TaskCanceledException ex)
            {
                // Timeout occurred - log only in diagnostic mode
                diagnosticLogger.LogHttpError("HTTP request timeout", ex);
            }
            catch (HttpRequestException ex)
            {
                // HTTP-specific errors (connection failed, DNS issues, etc.) - log only in diagnostic mode
                diagnosticLogger.LogHttpError("HTTP request failed", ex);
            }
            catch (Exception ex)
            {
                // Other unexpected errors - log only in diagnostic mode
                diagnosticLogger.LogHttpError("Unexpected HTTP error", ex);
            }
            finally
            {
                httpSemaphore.Release();
            }
        }

        public async Task Start()
        {
            // ОПТИМИЗАЦИЯ: Снижаем приоритет процесса для минимального влияния на игры
            try
            {
                using var process = System.Diagnostics.Process.GetCurrentProcess();
                process.PriorityClass = System.Diagnostics.ProcessPriorityClass.BelowNormal;
                Console.WriteLine("⚡ Приоритет процесса снижен для оптимизации");
            }
            catch
            {
                // Игнорируем ошибки изменения приоритета
            }
            
            Console.WriteLine("✅ MediaMonitor запущен!");
            Console.WriteLine($"🔗 Подключение к серверу: {pythonServerUrl}");
            
            // Загружаем выбранный источник из конфига
            await LoadSelectedSource().ConfigureAwait(false);
            
            Console.WriteLine("🎵 Начинаем мониторинг медиа...");

            while (true)
            {
                try
                {
                    await Tick().ConfigureAwait(false);
                    
                    // Log diagnostic information periodically
                    diagnosticLogger.LogPeriodic();
                }
                catch (Exception ex)
                {
                    Console.WriteLine($"Ошибка monitor: {ex.Message}");
                }

                // Увеличиваем интервал до 2 секунд для снижения нагрузки
                await Task.Delay(2000).ConfigureAwait(false);
            }
        }
        
        private async Task LoadSelectedSource()
        {
            try
            {
                diagnosticLogger.LogHttpRequest();
                
                await httpSemaphore.WaitAsync().ConfigureAwait(false);
                try
                {
                    using var response = await httpClient.GetAsync($"{pythonServerUrl}/get_config").ConfigureAwait(false);
                    if (response.IsSuccessStatusCode)
                    {
                        var json = await response.Content.ReadAsStringAsync().ConfigureAwait(false);
                        var config = JsonSerializer.Deserialize<JsonElement>(json);
                        
                        if (config.TryGetProperty("selected_media_source", out var source))
                        {
                            selectedSource = source.GetString() ?? "";
                            if (!string.IsNullOrEmpty(selectedSource) && selectedSource != "auto")
                            {
                                Console.WriteLine($"📻 Выбран источник: {selectedSource}");
                            }
                        }
                    }
                }
                catch (TaskCanceledException ex)
                {
                    // Timeout occurred - log only in diagnostic mode
                    diagnosticLogger.LogHttpError("Config request timeout", ex);
                }
                catch (HttpRequestException ex)
                {
                    // HTTP-specific errors - log only in diagnostic mode
                    diagnosticLogger.LogHttpError("Config request failed", ex);
                }
                catch (Exception ex)
                {
                    // Other unexpected errors - log only in diagnostic mode
                    diagnosticLogger.LogHttpError("Unexpected error loading config", ex);
                }
                finally
                {
                    httpSemaphore.Release();
                }
                
                // Отправляем список доступных источников на сервер
                await SendAvailableSources().ConfigureAwait(false);
            }
            catch
            {
                // Outer catch to ensure method doesn't throw
            }
        }
        
        /// <summary>
        /// Checks if source enumeration should be performed based on cache validity
        /// </summary>
        /// <returns>True if cache is expired and enumeration is needed</returns>
        private bool ShouldEnumerateSources()
        {
            var elapsed = (DateTime.Now - lastSourceEnumeration).TotalSeconds;
            return elapsed >= SOURCE_CACHE_SECONDS;
        }
        
        private async Task SendAvailableSources()
        {
            try
            {
                // Check if we should skip enumeration due to valid cache
                if (!ShouldEnumerateSources())
                {
                    return;
                }
                
                var manager = await GlobalSystemMediaTransportControlsSessionManager.RequestAsync().AsTask().ConfigureAwait(false);
                var sessions = manager.GetSessions();
                
                // Log session enumeration for diagnostics
                diagnosticLogger.LogSessionAccess();
                
                var sources = new List<object>();
                var seenIds = new HashSet<string>();
                var sourceIds = new List<string>();
                
                try
                {
                    foreach (var session in sessions)
                    {
                        try
                        {
                            var appId = session.SourceAppUserModelId;
                            if (!string.IsNullOrEmpty(appId) && !seenIds.Contains(appId))
                            {
                                seenIds.Add(appId);
                                sourceIds.Add(appId);
                                
                                // Пытаемся получить читаемое имя
                                string displayName = appId;
                                try
                                {
                                    var parts = appId.Split('!');
                                    if (parts.Length > 0)
                                    {
                                        var appParts = parts[0].Split('.');
                                        if (appParts.Length > 0)
                                        {
                                            displayName = appParts[appParts.Length - 1];
                                        }
                                    }
                                }
                                catch { }
                                
                                sources.Add(new { id = appId, name = displayName });
                            }
                        }
                        catch { }
                        finally
                        {
                            // Dispose each session immediately after reading properties
                            try
                            {
                                if (Marshal.IsComObject(session))
                                {
                                    Marshal.ReleaseComObject(session);
                                }
                            }
                            catch { }
                        }
                    }
                    
                    var data = new { sources };
                    var json = JsonSerializer.Serialize(data);
                    var content = new StringContent(json, Encoding.UTF8, "application/json");
                    
                    diagnosticLogger.LogHttpRequest();
                    await SendHttpWithDisposalAsync(() => httpClient.PostAsync($"{pythonServerUrl}/update_sources", content)).ConfigureAwait(false);
                    Console.WriteLine($"📻 Найдено источников: {sources.Count}");
                    
                    // Update cache and timestamp after successful enumeration
                    sessionCache.Update(sourceIds);
                    lastSourceEnumeration = DateTime.Now;
                }
                catch
                {
                    // On error, ensure all sessions are disposed
                    foreach (var session in sessions)
                    {
                        try
                        {
                            if (Marshal.IsComObject(session))
                            {
                                Marshal.ReleaseComObject(session);
                            }
                        }
                        catch { }
                    }
                    throw;
                }
            }
            catch
            {
                // Игнорируем ошибки отправки источников
            }
        }

        private async Task Tick()
        {
            GlobalSystemMediaTransportControlsSessionManager? manager = null;
            GlobalSystemMediaTransportControlsSession? newSession = null;
            
            try
            {
                manager = await GlobalSystemMediaTransportControlsSessionManager.RequestAsync().AsTask().ConfigureAwait(false);
                
                // Получаем сессию с учетом выбранного источника
                newSession = await GetSessionBySource(manager).ConfigureAwait(false);

                if (newSession == null)
                {
                    // Выводим отладочную информацию только один раз
                    if (!hasLoggedNoSession)
                    {
                        var allSessions = manager.GetSessions();
                        diagnosticLogger.LogSessionAccess();
                        Console.WriteLine($"⚠️ Сессия не найдена. Всего сессий: {allSessions.Count}");
                        
                        if (allSessions.Count > 0)
                        {
                            Console.WriteLine($"   Выбранный источник: '{selectedSource}'");
                            Console.WriteLine("   Доступные сессии:");
                            
                            try
                            {
                                foreach (var session in allSessions)
                                {
                                    try
                                    {
                                        var appId = session.SourceAppUserModelId;
                                        var props = await session.TryGetMediaPropertiesAsync().AsTask().ConfigureAwait(false);
                                        Console.WriteLine($"   - {appId}");
                                        Console.WriteLine($"     Трек: {props.Artist} - {props.Title}");
                                    }
                                    catch (Exception ex)
                                    {
                                        Console.WriteLine($"   - Ошибка получения информации: {ex.Message}");
                                    }
                                    finally
                                    {
                                        // Dispose each session after reading properties
                                        try
                                        {
                                            if (Marshal.IsComObject(session))
                                            {
                                                Marshal.ReleaseComObject(session);
                                            }
                                        }
                                        catch { }
                                    }
                                }
                            }
                            catch
                            {
                                // Ensure all sessions are disposed on error
                                foreach (var session in allSessions)
                                {
                                    try
                                    {
                                        if (Marshal.IsComObject(session))
                                        {
                                            Marshal.ReleaseComObject(session);
                                        }
                                    }
                                    catch { }
                                }
                            }
                        }
                        
                        hasLoggedNoSession = true;
                    }
                    
                    SetNoPlayback();
                    return;
                }
                
                // Dispose previous currentSession before assigning new one
                if (currentSession != null && currentSession != newSession)
                {
                    try
                    {
                        if (Marshal.IsComObject(currentSession))
                        {
                            Marshal.ReleaseComObject(currentSession);
                        }
                    }
                    catch { }
                }
                
                // Keep newSession alive for the cycle duration
                currentSession = newSession;
                
                // Если нашли сессию, сбрасываем флаг
                hasLoggedNoSession = false;
            }
            catch (Exception ex)
            {
                // Логируем критические ошибки только один раз
                if (!hasLoggedNoSession)
                {
                    Console.WriteLine($"❌ Критическая ошибка в Tick(): {ex.Message}");
                    hasLoggedNoSession = true;
                }
                SetNoPlayback();
                return;
            }
            finally
            {
                // Dispose manager after GetSessionBySource call
                // Note: We don't dispose currentSession here as it needs to stay alive for the cycle
                if (manager != null)
                {
                    try
                    {
                        if (Marshal.IsComObject(manager))
                        {
                            Marshal.ReleaseComObject(manager);
                        }
                    }
                    catch { }
                }
            }

            var mediaInfo = await currentSession.TryGetMediaPropertiesAsync().AsTask().ConfigureAwait(false);
            var timeline = currentSession.GetTimelineProperties();
            var playback = currentSession.GetPlaybackInfo();

            string artist = mediaInfo.Artist ?? "Unknown Artist";
            string title = mediaInfo.Title ?? "Unknown Title";
            double position = timeline?.Position.TotalSeconds ?? 0;
            double duration = timeline?.EndTime.TotalSeconds ?? 0;
            bool isPlaying = playback.PlaybackStatus == GlobalSystemMediaTransportControlsSessionPlaybackStatus.Playing;

            bool trackChanged = artist != State.Artist || title != State.Title;
            
            // Проверяем значительные изменения позиции (перемотка)
            bool positionJumped = Math.Abs(position - lastPosition) > 3;
            bool playbackChanged = isPlaying != lastIsPlaying;

            if (trackChanged)
            {
                // Выводим только при смене трека
                Console.WriteLine($"🎵 {artist} — {title}");

                // Check if activeTrackTask is running before starting new one
                if (activeTrackTask != null && !activeTrackTask.IsCompleted)
                {
                    // Cancel and await previous task before starting new one
                    var oldCts = trackTaskCTS;
                    if (oldCts != null)
                    {
                        try
                        {
                            oldCts.Cancel();
                        }
                        catch { }
                    }
                    
                    // Handle cancellation exceptions gracefully
                    try
                    {
                        await activeTrackTask.ConfigureAwait(false);
                    }
                    catch (OperationCanceledException)
                    {
                        // Expected when task is cancelled
                    }
                    catch
                    {
                        // Ignore other exceptions from cancelled task
                    }
                    
                    // Dispose old CTS after task completes
                    if (oldCts != null)
                    {
                        try
                        {
                            oldCts.Dispose();
                        }
                        catch { }
                    }
                }
                
                // Create new CTS for the new task
                trackTaskCTS = new CancellationTokenSource();

                State.Artist = artist;
                State.Title = title;
                State.Position = position;
                State.Duration = duration;
                State.IsPlaying = isPlaying;

                lastPosition = position;
                lastIsPlaying = isPlaying;

                await SendUpdate(force: true).ConfigureAwait(false);

                // Track the running ProcessTrackChange task
                activeTrackTask = Task.Run(() => ProcessTrackChange(mediaInfo, trackTaskCTS.Token));
            }
            else if (positionJumped || playbackChanged)
            {
                // Отправляем только при перемотке или смене статуса воспроизведения
                State.Position = position;
                State.Duration = duration;
                State.IsPlaying = isPlaying;

                lastPosition = position;
                lastIsPlaying = isPlaying;

                await SendUpdate(force: true).ConfigureAwait(false);
            }
            else
            {
                // Просто обновляем локальное состояние без отправки
                State.Position = position;
                State.Duration = duration;
                State.IsPlaying = isPlaying;
                lastPosition = position;
            }
        }
        
        private async Task<GlobalSystemMediaTransportControlsSession?> GetSessionBySource(
            GlobalSystemMediaTransportControlsSessionManager manager)
        {
            // Log session enumeration for diagnostics
            diagnosticLogger.LogSessionAccess();
            
            // Если источник не выбран, берем текущую сессию
            if (string.IsNullOrEmpty(selectedSource) || selectedSource == "auto")
            {
                return manager.GetCurrentSession();
            }

            // Ищем сессию по выбранному источнику
            GlobalSystemMediaTransportControlsSession? matchedSession = null;
            IReadOnlyList<GlobalSystemMediaTransportControlsSession>? sessions = null;
            
            try
            {
                sessions = manager.GetSessions();
                
                foreach (var session in sessions)
                {
                    try
                    {
                        var appId = session.SourceAppUserModelId;
                        if (appId == selectedSource)
                        {
                            // Keep the matched session alive
                            matchedSession = session;
                            // Don't release the matched session - we're returning it
                        }
                        else
                        {
                            // Release non-matching sessions immediately to free COM resources
                            try
                            {
                                if (Marshal.IsComObject(session))
                                {
                                    Marshal.ReleaseComObject(session);
                                }
                            }
                            catch { }
                        }
                    }
                    catch
                    {
                        // If error reading properties, release the session
                        try
                        {
                            if (Marshal.IsComObject(session))
                            {
                                Marshal.ReleaseComObject(session);
                            }
                        }
                        catch { }
                    }
                }
            }
            catch
            {
                // On error, release all sessions including matched one
                if (sessions != null)
                {
                    foreach (var session in sessions)
                    {
                        try
                        {
                            if (Marshal.IsComObject(session))
                            {
                                Marshal.ReleaseComObject(session);
                            }
                        }
                        catch { }
                    }
                }
                matchedSession = null;
                throw;
            }

            // Если не нашли, возвращаем текущую
            if (matchedSession == null)
            {
                return manager.GetCurrentSession();
            }
            
            return matchedSession;
        }

        private async Task ProcessTrackChange(
            GlobalSystemMediaTransportControlsSessionMediaProperties mediaInfo,
            CancellationToken token)
        {
            try
            {
                // Получаем длительность
                double duration = await WaitForDuration(currentSession).ConfigureAwait(false);

                if (token.IsCancellationRequested)
                    return;

                State.Duration = duration;

                await SendUpdate(force: true).ConfigureAwait(false);
            }
            catch
            {
                // Игнорируем ошибки для снижения нагрузки
            }
        }

        private async Task<double> WaitForDuration(GlobalSystemMediaTransportControlsSession session)
        {
            for (int i = 0; i < 10; i++)
            {
                try
                {
                    var t = session.GetTimelineProperties();
                    if (t?.EndTime.TotalSeconds > 0)
                        return t.EndTime.TotalSeconds;
                }
                catch { }

                await Task.Delay(300).ConfigureAwait(false);
            }

            return 0;
        }

        private void SetNoPlayback()
        {
            if (State.Artist != "Не воспроизводится")
            {
                State.Artist = "Не воспроизводится";
                State.Title = "Нет данных";
                State.Position = 0;
                State.Duration = 0;
                State.IsPlaying = false;
                
                // Не выводим в консоль для снижения нагрузки
            }
        }

        private async Task SendUpdate(bool force = false)
        {
            if (!force)
            {
                var dt = (DateTime.Now - lastUpdate).TotalSeconds;
                if (dt < UPDATE_COOLDOWN)
                    return;
            }

            lastUpdate = DateTime.Now;

            // Не выводим State.Print() для снижения нагрузки
            await SendToPythonServer().ConfigureAwait(false);
        }

        private async Task SendToPythonServer()
        {
            try
            {
                var data = new
                {
                    artist = State.Artist,
                    title = State.Title,
                    position = State.Position,
                    duration = State.Duration,
                    is_playing = State.IsPlaying,
                    cover_version = State.CoverVersion,
                    status = State.Status
                };

                var json = JsonSerializer.Serialize(data);
                var content = new StringContent(json, Encoding.UTF8, "application/json");

                // Use proper disposal pattern instead of fire-and-forget
                diagnosticLogger.LogHttpRequest();
                await SendHttpWithDisposalAsync(() => httpClient.PostAsync($"{pythonServerUrl}/update_from_cs", content)).ConfigureAwait(false);
            }
            catch
            {
                // Игнорируем ошибки отправки чтобы не нагружать CPU логами
            }
        }

        // IDisposable implementation
        public void Dispose()
        {
            Dispose(true);
            GC.SuppressFinalize(this);
        }

        protected virtual void Dispose(bool disposing)
        {
            if (disposed)
                return;

            if (disposing)
            {
                // Dispose managed resources
                try
                {
                    // Cancel and wait for active track task to complete
                    if (activeTrackTask != null && !activeTrackTask.IsCompleted)
                    {
                        if (trackTaskCTS != null)
                        {
                            trackTaskCTS.Cancel();
                        }
                        
                        try
                        {
                            // Wait for task to complete with timeout
                            activeTrackTask.Wait(TimeSpan.FromSeconds(2));
                        }
                        catch (AggregateException)
                        {
                            // Expected when task is cancelled
                        }
                        catch
                        {
                            // Ignore other exceptions
                        }
                        
                        activeTrackTask = null;
                    }
                    
                    // Cancel and dispose CancellationTokenSource
                    if (trackTaskCTS != null)
                    {
                        trackTaskCTS.Cancel();
                        trackTaskCTS.Dispose();
                        trackTaskCTS = null;
                    }

                    // Clear current session reference (sessions don't implement IDisposable)
                    currentSession = null;

                    // Dispose HttpClient
                    httpClient?.Dispose();
                    
                    // Dispose semaphore
                    httpSemaphore?.Dispose();
                }
                catch
                {
                    // Ignore disposal errors
                }
            }

            disposed = true;
        }

        // Finalizer
        ~MediaMonitor()
        {
            Dispose(false);
        }
    }

    /// <summary>
    /// Internal helper class for caching session source IDs to reduce expensive session enumeration
    /// </summary>
    internal class SessionCache
    {
        private List<string> cachedSourceIds = new List<string>();
        private DateTime cacheTime = DateTime.MinValue;
        private const int CACHE_DURATION_SECONDS = 30;

        /// <summary>
        /// Checks if the cache is still valid (less than 30 seconds old)
        /// </summary>
        /// <returns>True if cache is valid, false if expired</returns>
        public bool IsValid()
        {
            var elapsed = (DateTime.Now - cacheTime).TotalSeconds;
            return elapsed < CACHE_DURATION_SECONDS;
        }

        /// <summary>
        /// Updates the cache with new source IDs and resets the timestamp
        /// </summary>
        /// <param name="sourceIds">List of source IDs to cache</param>
        public void Update(List<string> sourceIds)
        {
            cachedSourceIds = new List<string>(sourceIds);
            cacheTime = DateTime.Now;
        }

        /// <summary>
        /// Retrieves the cached source IDs
        /// </summary>
        /// <returns>List of cached source IDs</returns>
        public List<string> GetCached()
        {
            return new List<string>(cachedSourceIds);
        }
    }

    /// <summary>
    /// Internal helper class for diagnostic logging to track resource usage
    /// </summary>
    internal class DiagnosticLogger
    {
        private int sessionAccessCount = 0;
        private int httpRequestCount = 0;
        private DateTime lastLogTime = DateTime.MinValue;
        private long lastMemoryBytes = 0;
        private DateTime lastMemoryLogTime = DateTime.MinValue;
        private const int LOG_INTERVAL_SECONDS = 10;
        private const int MEMORY_LOG_INTERVAL_SECONDS = 30;
        private readonly bool enabled;

        public DiagnosticLogger(bool enabled)
        {
            this.enabled = enabled;
            if (enabled)
            {
                // Initialize memory baseline
                lastMemoryBytes = GC.GetTotalMemory(false);
                lastMemoryLogTime = DateTime.Now;
                lastLogTime = DateTime.Now;
            }
        }

        /// <summary>
        /// Increments the session access counter for tracking session enumeration
        /// </summary>
        public void LogSessionAccess()
        {
            if (!enabled) return;
            Interlocked.Increment(ref sessionAccessCount);
        }

        /// <summary>
        /// Increments the HTTP request counter for tracking HTTP calls
        /// </summary>
        public void LogHttpRequest()
        {
            if (!enabled) return;
            Interlocked.Increment(ref httpRequestCount);
        }

        /// <summary>
        /// Logs HTTP errors only when diagnostic mode is enabled
        /// </summary>
        /// <param name="message">Error message describing the context</param>
        /// <param name="ex">The exception that occurred</param>
        public void LogHttpError(string message, Exception ex)
        {
            if (!enabled) return;
            Console.WriteLine($"[DIAG] {message}: {ex.GetType().Name} - {ex.Message}");
        }

        /// <summary>
        /// Outputs diagnostic statistics every 10 seconds if diagnostic mode is enabled
        /// Also logs memory usage delta every 30 seconds
        /// </summary>
        public void LogPeriodic()
        {
            if (!enabled) return;

            var now = DateTime.Now;
            var elapsed = (now - lastLogTime).TotalSeconds;

            // Log counters every 10 seconds
            if (elapsed >= LOG_INTERVAL_SECONDS)
            {
                var memoryElapsed = (now - lastMemoryLogTime).TotalSeconds;
                
                // Calculate memory delta if 30 seconds have passed
                string memoryInfo = "";
                if (memoryElapsed >= MEMORY_LOG_INTERVAL_SECONDS)
                {
                    long currentMemory = GC.GetTotalMemory(false);
                    long memoryDelta = currentMemory - lastMemoryBytes;
                    double memoryDeltaMB = memoryDelta / (1024.0 * 1024.0);
                    memoryInfo = $", Memory delta: {memoryDeltaMB:+0.0;-0.0} MB";
                    
                    lastMemoryBytes = currentMemory;
                    lastMemoryLogTime = now;
                }

                // Calculate requests per minute
                int requestsPerMinute = (int)(httpRequestCount * (60.0 / elapsed));

                Console.WriteLine($"[DIAG] Sessions accessed: {sessionAccessCount}, HTTP requests/min: {requestsPerMinute}{memoryInfo}");

                // Reset counters
                sessionAccessCount = 0;
                httpRequestCount = 0;
                lastLogTime = now;
            }
        }
    }
}
