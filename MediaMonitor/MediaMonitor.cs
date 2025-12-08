using System;
using System.Collections.Generic;
using System.Linq;
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

        internal GlobalSystemMediaTransportControlsSessionManager? sessionManager;
        internal GlobalSystemMediaTransportControlsSession? currentSession;

        private readonly string pythonServerUrl;
        
        // Для отслеживания изменений
        private double lastPosition = 0;
        private bool lastIsPlaying = false;
        private string selectedSource = "";
        
        // Кеширование источников
        private DateTime lastSourceEnumeration = DateTime.MinValue;
        private const int SOURCE_CACHE_SECONDS = 5;
        private List<string> lastSentSources = new List<string>();
        
        // New component-based architecture
        private HealthMonitor? healthMonitor;
        private RecoveryManager? recoveryManager;
        private EventSubscriptionManager? eventSubscriptionManager;
        private UpdateQueue? updateQueue;
        private HttpClientPool? httpClientPool;
        private IsolatedConfigPoller? configPoller;
        
        // Recovery state
        private bool isRecovering = false;
        
        public MediaMonitor(int port = 58080)
        {
            pythonServerUrl = $"http://localhost:{port}";
            // Components will be initialized in Start()
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
            
            // Initialize new components
            httpClientPool = new HttpClientPool(pythonServerUrl);
            updateQueue = new UpdateQueue();
            eventSubscriptionManager = new EventSubscriptionManager();
            recoveryManager = new RecoveryManager(this);
            healthMonitor = new HealthMonitor();
            
            // Wire up event handlers
            healthMonitor.RecoveryNeeded += OnRecoveryNeeded;
            eventSubscriptionManager.MediaUpdated += OnMediaUpdated;
            updateQueue.UpdateReady += OnUpdateReady;
            updateQueue.RecoveryNeeded += OnRecoveryNeeded;
            
            // Загружаем выбранный источник из конфига
            await LoadSelectedSource();
            
            // Инициализируем SessionManager один раз
            await InitializeSessionManager();
            
            // Отправляем начальный список источников
            await SendAvailableSources(force: true);
            
            // Initialize ConfigPoller with isolated HTTP client
            configPoller = new IsolatedConfigPoller(pythonServerUrl);
            configPoller.SourceChanged += OnConfigSourceChanged;
            configPoller.Start();
            
            // Start health monitoring
            try
            {
                Console.WriteLine("🔄 Запуск HealthMonitor...");
                healthMonitor.Start();
                Console.WriteLine("✅ HealthMonitor запущен успешно");
            }
            catch (Exception ex)
            {
                Console.WriteLine($"❌ ОШИБКА запуска HealthMonitor: {ex.Message}");
                Console.WriteLine($"   Stack trace: {ex.StackTrace}");
            }
            
            Console.WriteLine("🎵 Мониторинг медиа активен (event-driven режим с компонентной архитектурой)");
            
            // Держим приложение запущенным
            await Task.Delay(Timeout.Infinite);
        }
        
        private async Task InitializeSessionManager()
        {
            try
            {
                sessionManager = await GlobalSystemMediaTransportControlsSessionManager.RequestAsync();
                
                // Подписываемся на изменения сессий
                sessionManager.SessionsChanged += OnSessionsChanged;
                
                // Получаем начальную сессию
                await UpdateCurrentSession();
                
                Console.WriteLine("✅ Event-driven мониторинг инициализирован");
            }
            catch (Exception ex)
            {
                Console.WriteLine($"❌ Ошибка инициализации: {ex.Message}");
                throw;
            }
        }
        
        private void OnConfigSourceChanged(object? sender, SourceChangedEventArgs e)
        {
            _ = Task.Run(async () =>
            {
                try
                {
                    Console.WriteLine($"🔄 Источник изменен: {selectedSource} → {e.NewSource}");
                    selectedSource = e.NewSource;
                    
                    // Переключаем сессию
                    await UpdateCurrentSession();
                }
                catch (Exception ex)
                {
                    Console.WriteLine($"⚠️ Ошибка при смене источника: {ex.Message}");
                }
            });
        }
        
        private void OnRecoveryNeeded(object? sender, EventArgs e)
        {
            _ = Task.Run(async () =>
            {
                try
                {
                    Console.WriteLine("🔄 Запуск процедуры восстановления...");
                    bool success = await recoveryManager!.AttemptRecovery();
                    
                    if (success)
                    {
                        Console.WriteLine("✅ Восстановление успешно");
                        healthMonitor?.RecordUpdate();
                    }
                    else
                    {
                        Console.WriteLine("❌ Восстановление не удалось");
                    }
                }
                catch (Exception ex)
                {
                    Console.WriteLine($"❌ Ошибка восстановления: {ex.Message}");
                }
            });
        }
        
        private void OnMediaUpdated(object? sender, MediaUpdateEventArgs e)
        {
            try
            {
                Console.WriteLine($"📥 MediaMonitor.OnMediaUpdated получил событие: {e.Artist} - {e.Title}");
                
                // Update state from event
                State.Artist = e.Artist;
                State.Title = e.Title;
                State.Position = e.Position;
                State.Duration = e.Duration;
                State.IsPlaying = e.IsPlaying;
                State.SourceId = e.SourceId;
                
                Console.WriteLine($"   State обновлен: Position={State.Position:F1}s, IsPlaying={State.IsPlaying}");
                
                // Record update for health monitoring
                healthMonitor?.RecordUpdate();
                
                // Queue update for sending to Python server
                Console.WriteLine($"   Вызываем updateQueue.QueueUpdate...");
                updateQueue?.QueueUpdate(State);
                Console.WriteLine($"   updateQueue.QueueUpdate завершен");
            }
            catch (Exception ex)
            {
                Console.WriteLine($"⚠️ Ошибка обработки обновления медиа: {ex.Message}");
            }
        }
        
        private void OnUpdateReady(object? sender, CurrentMediaState state)
        {
            Console.WriteLine($"📤 MediaMonitor.OnUpdateReady вызван для: {state.Artist} - {state.Title}");
            
            _ = Task.Run(async () =>
            {
                try
                {
                    var data = new
                    {
                        artist = state.Artist,
                        title = state.Title,
                        position = state.Position,
                        duration = state.Duration,
                        is_playing = state.IsPlaying,
                        cover_version = state.CoverVersion,
                        status = state.Status,
                        source_id = state.SourceId
                    };
                    
                    Console.WriteLine($"   Отправляем данные на {pythonServerUrl}/update_from_cs");
                    Console.WriteLine($"   Position: {state.Position:F1}s, IsPlaying: {state.IsPlaying}");
                    
                    bool success = await httpClientPool!.SendUpdate(data, "/update_from_cs");
                    
                    if (success)
                    {
                        Console.WriteLine($"✅ Update sent to Python server");
                    }
                    else
                    {
                        Console.WriteLine($"⚠️ Failed to send update to Python server");
                    }
                }
                catch (Exception ex)
                {
                    Console.WriteLine($"❌ Error sending update: {ex.Message}");
                }
            });
        }
        
        internal async void OnSessionsChanged(GlobalSystemMediaTransportControlsSessionManager sender, SessionsChangedEventArgs args)
        {
            try
            {
                // Отправляем обновленный список источников
                await SendAvailableSources(force: true);
                
                // Обновляем текущую сессию
                await UpdateCurrentSession();
            }
            catch (Exception ex)
            {
                Console.WriteLine($"⚠️ Ошибка при смене сессии: {ex.Message}");
            }
        }
        
        internal async Task UpdateCurrentSession(bool skipInitialUpdate = false)
        {
            Console.WriteLine($"🔄 UpdateCurrentSession вызван (selectedSource: {selectedSource}, skipInitialUpdate: {skipInitialUpdate})");
            
            // Unsubscribe from old session using EventSubscriptionManager
            eventSubscriptionManager?.Unsubscribe();
            
            // Получаем новую сессию
            currentSession = await GetSessionBySource(sessionManager!);
            
            if (currentSession == null)
            {
                Console.WriteLine($"❌ Новая сессия не найдена");
                SetNoPlayback();
                return;
            }
            
            // Subscribe to new session using EventSubscriptionManager
            try
            {
                var newAppId = currentSession.SourceAppUserModelId;
                Console.WriteLine($"📥 Подписываемся на новую сессию: {newAppId}");
                
                await eventSubscriptionManager!.Subscribe(currentSession);
                
                // Получаем начальное состояние только если не пропускаем
                if (!skipInitialUpdate)
                {
                    Console.WriteLine($"📊 Получаем начальное состояние новой сессии");
                    await UpdateMediaInfo();
                }
                else
                {
                    Console.WriteLine($"⏭️ Пропускаем начальное обновление (ждем естественных событий)");
                }
            }
            catch (Exception ex)
            {
                Console.WriteLine($"⚠️ Ошибка подписки на события: {ex.Message}");
            }
        }
        
        public async Task UpdateMediaInfo()
        {
            if (currentSession == null) return;
            
            try
            {
                var mediaInfo = await currentSession.TryGetMediaPropertiesAsync();
                var timeline = currentSession.GetTimelineProperties();
                var playback = currentSession.GetPlaybackInfo();

                string artist = mediaInfo.Artist ?? "Unknown Artist";
                string title = mediaInfo.Title ?? "Unknown Title";
                double position = timeline?.Position.TotalSeconds ?? 0;
                double duration = timeline?.EndTime.TotalSeconds ?? 0;
                bool isPlaying = playback.PlaybackStatus == GlobalSystemMediaTransportControlsSessionPlaybackStatus.Playing;
                
                // Получаем SourceAppUserModelId из currentSession
                string sourceId = currentSession.SourceAppUserModelId ?? "";

                bool trackChanged = artist != State.Artist || title != State.Title;

                if (trackChanged)
                {
                    Console.WriteLine($"🎵 {artist} — {title}");
                }
                
                // Update state
                State.Artist = artist;
                State.Title = title;
                State.Position = position;
                State.Duration = duration;
                State.IsPlaying = isPlaying;
                State.SourceId = sourceId;
                
                lastPosition = position;
                lastIsPlaying = isPlaying;
                
                // Record update for health monitoring
                healthMonitor?.RecordUpdate();
                
                // Queue update for sending to Python server
                updateQueue?.QueueUpdate(State);
            }
            catch (Exception ex)
            {
                Console.WriteLine($"⚠️ Ошибка получения медиа информации: {ex.Message}");
            }
        }
        
        private async Task LoadSelectedSource()
        {
            try
            {
                // Use HttpClientPool for initial config load
                using var tempClient = new HttpClient { Timeout = TimeSpan.FromSeconds(5) };
                using var response = await tempClient.GetAsync($"{pythonServerUrl}/get_config").ConfigureAwait(false);
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
            catch
            {
                // Игнорируем ошибки загрузки конфига
            }
        }
        
        private async Task SendAvailableSources(bool force = false)
        {
            // Кешируем источники на 5 секунд
            var timeSinceLastEnum = (DateTime.Now - lastSourceEnumeration).TotalSeconds;
            if (!force && timeSinceLastEnum < SOURCE_CACHE_SECONDS)
            {
                return;
            }
            
            try
            {
                var manager = await GlobalSystemMediaTransportControlsSessionManager.RequestAsync();
                var sessions = manager.GetSessions();
                
                var sources = new List<object>();
                var currentSourceIds = new List<string>();
                var seenIds = new HashSet<string>();
                
                // Обрабатываем сессии (WinRT объекты не требуют Dispose)
                foreach (var session in sessions)
                {
                    try
                    {
                        var appId = session.SourceAppUserModelId;
                        if (!string.IsNullOrEmpty(appId) && !seenIds.Contains(appId))
                        {
                            seenIds.Add(appId);
                            currentSourceIds.Add(appId);
                            
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
                }
                
                // Проверяем, изменился ли список источников
                bool sourcesChanged = !currentSourceIds.SequenceEqual(lastSentSources);
                
                if (sourcesChanged || force)
                {
                    // Обновляем время последнего перечисления
                    lastSourceEnumeration = DateTime.Now;
                    
                    // Use HttpClientPool for sending sources
                    var data = new { sources };
                    bool success = await httpClientPool!.SendUpdate(data, "/update_sources");
                    
                    if (success)
                    {
                        lastSentSources = currentSourceIds;
                        Console.WriteLine($"📻 Отправлено источников: {sources.Count}");
                    }
                }
            }
            catch
            {
                // Игнорируем ошибки отправки источников
            }
        }


        private Task<GlobalSystemMediaTransportControlsSession?> GetSessionBySource(
            GlobalSystemMediaTransportControlsSessionManager manager)
        {
            // Если источник не выбран, берем текущую сессию
            if (string.IsNullOrEmpty(selectedSource) || selectedSource == "auto")
            {
                Console.WriteLine($"🔍 Режим auto - используем текущую сессию");
                return Task.FromResult<GlobalSystemMediaTransportControlsSession?>(manager.GetCurrentSession());
            }

            Console.WriteLine($"🔍 Ищем сессию для источника: {selectedSource}");
            var sessions = manager.GetSessions();
            
            // Ищем сессию по выбранному источнику (WinRT объекты не требуют Dispose)
            foreach (var session in sessions)
            {
                try
                {
                    var appId = session.SourceAppUserModelId;
                    Console.WriteLine($"  - Проверяем сессию: {appId}");
                    if (appId == selectedSource)
                    {
                        Console.WriteLine($"✅ Найдена сессия для {selectedSource}");
                        return Task.FromResult<GlobalSystemMediaTransportControlsSession?>(session);
                    }
                }
                catch { }
            }

            // Если не нашли, возвращаем текущую
            Console.WriteLine($"⚠️ Сессия для {selectedSource} не найдена, используем текущую");
            return Task.FromResult<GlobalSystemMediaTransportControlsSession?>(manager.GetCurrentSession());
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
                
                // Queue update using UpdateQueue
                updateQueue?.QueueUpdate(State);
            }
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
                    // Dispose managed resources
                    try
                    {
                        // Unsubscribe from events
                        if (sessionManager != null)
                        {
                            sessionManager.SessionsChanged -= OnSessionsChanged;
                        }

                        // Dispose new components
                        healthMonitor?.Stop();
                        healthMonitor?.Dispose();
                        
                        configPoller?.Stop();
                        configPoller?.Dispose();
                        
                        eventSubscriptionManager?.Unsubscribe();
                        eventSubscriptionManager?.Dispose();
                        
                        updateQueue?.Dispose();
                        httpClientPool?.Dispose();
                        
                        recoveryManager?.Dispose();

                        Console.WriteLine("🧹 MediaMonitor resources cleaned up");
                    }
                    catch (Exception ex)
                    {
                        Console.WriteLine($"⚠️ Error during cleanup: {ex.Message}");
                    }
                }

                disposed = true;
            }
        }
    }
}
