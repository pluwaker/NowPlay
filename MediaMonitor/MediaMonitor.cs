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

        private GlobalSystemMediaTransportControlsSessionManager? sessionManager;
        private GlobalSystemMediaTransportControlsSession? currentSession;

        private readonly HttpClient httpClient;
        private readonly string pythonServerUrl = "http://localhost:8080";
        
        // Для отслеживания изменений
        private double lastPosition = 0;
        private bool lastIsPlaying = false;
        private string selectedSource = "";
        
        // Для debouncing обновлений с 2-секундным батчингом
        private System.Threading.Timer? debounceTimer;
        private bool pendingUpdate = false;
        private readonly SemaphoreSlim updateLock = new SemaphoreSlim(1, 1);
        
        // HTTP семафор для ограничения параллельных запросов
        private readonly SemaphoreSlim httpSemaphore = new SemaphoreSlim(1, 1);
        private DateTime lastHttpUpdate = DateTime.MinValue;
        private const double UPDATE_COOLDOWN_SECONDS = 2.0;
        
        // Кеширование источников
        private DateTime lastSourceEnumeration = DateTime.MinValue;
        private const int SOURCE_CACHE_SECONDS = 5;
        private List<string> lastSentSources = new List<string>();
        
        // ConfigPoller для отслеживания изменений конфигурации
        private System.Threading.Timer? configPollerTimer;
        private string lastSelectedSource = "";
        private const int CONFIG_POLL_INTERVAL_MS = 2000;
        
        public MediaMonitor()
        {
            // Настраиваем HttpClient с таймаутом
            httpClient = new HttpClient
            {
                Timeout = TimeSpan.FromSeconds(5)
            };
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
            await LoadSelectedSource();
            
            // Инициализируем SessionManager один раз
            await InitializeSessionManager();
            
            // Отправляем начальный список источников
            await SendAvailableSources(force: true);
            
            // Инициализируем ConfigPoller для отслеживания изменений конфигурации
            InitializeConfigPoller();
            
            // Создаем debounce timer
            debounceTimer = new System.Threading.Timer(OnDebounceTimerElapsed, null, Timeout.Infinite, Timeout.Infinite);
            
            Console.WriteLine("🎵 Мониторинг медиа активен (event-driven режим)");
            
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
        
        private void InitializeConfigPoller()
        {
            configPollerTimer = new System.Threading.Timer(
                OnConfigPollTimerElapsed,
                null,
                CONFIG_POLL_INTERVAL_MS,
                CONFIG_POLL_INTERVAL_MS
            );
            Console.WriteLine("✅ ConfigPoller инициализирован");
        }
        
        private async Task CheckConfigChanges()
        {
            try
            {
                using var response = await httpClient.GetAsync($"{pythonServerUrl}/get_config").ConfigureAwait(false);
                
                if (response.IsSuccessStatusCode)
                {
                    var json = await response.Content.ReadAsStringAsync().ConfigureAwait(false);
                    var config = JsonSerializer.Deserialize<JsonElement>(json);
                    
                    if (config.TryGetProperty("selected_media_source", out var source))
                    {
                        string newSource = source.GetString() ?? "auto";
                        
                        // Проверяем, изменился ли источник
                        if (newSource != lastSelectedSource)
                        {
                            Console.WriteLine($"🔄 Источник изменен: {lastSelectedSource} → {newSource}");
                            lastSelectedSource = newSource;
                            selectedSource = newSource;
                            
                            // Переключаем сессию
                            await UpdateCurrentSession();
                        }
                    }
                }
            }
            catch (HttpRequestException)
            {
                // Сервер недоступен - игнорируем
            }
        }
        
        private void OnConfigPollTimerElapsed(object? state)
        {
            _ = Task.Run(async () =>
            {
                try
                {
                    await CheckConfigChanges();
                }
                catch (Exception ex)
                {
                    Console.WriteLine($"⚠️ Ошибка проверки конфигурации: {ex.Message}");
                }
            });
        }
        
        private async void OnSessionsChanged(GlobalSystemMediaTransportControlsSessionManager sender, SessionsChangedEventArgs args)
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
        
        private async Task UpdateCurrentSession()
        {
            Console.WriteLine($"🔄 UpdateCurrentSession вызван (selectedSource: {selectedSource})");
            
            // Отписываемся от старой сессии (WinRT объекты не требуют Dispose)
            var oldSession = currentSession;
            if (oldSession != null)
            {
                try
                {
                    var oldAppId = oldSession.SourceAppUserModelId;
                    Console.WriteLine($"📤 Отписываемся от старой сессии: {oldAppId}");
                    oldSession.MediaPropertiesChanged -= OnMediaPropertiesChanged;
                    oldSession.PlaybackInfoChanged -= OnPlaybackInfoChanged;
                    oldSession.TimelinePropertiesChanged -= OnTimelinePropertiesChanged;
                }
                catch { }
            }
            
            // Получаем новую сессию
            currentSession = await GetSessionBySource(sessionManager!);
            
            if (currentSession == null)
            {
                Console.WriteLine($"❌ Новая сессия не найдена");
                SetNoPlayback();
                return;
            }
            
            // Подписываемся на события новой сессии
            try
            {
                var newAppId = currentSession.SourceAppUserModelId;
                Console.WriteLine($"📥 Подписываемся на новую сессию: {newAppId}");
                
                currentSession.MediaPropertiesChanged += OnMediaPropertiesChanged;
                currentSession.PlaybackInfoChanged += OnPlaybackInfoChanged;
                currentSession.TimelinePropertiesChanged += OnTimelinePropertiesChanged;
                
                // Получаем начальное состояние
                Console.WriteLine($"📊 Получаем начальное состояние новой сессии");
                await UpdateMediaInfo();
            }
            catch (Exception ex)
            {
                Console.WriteLine($"⚠️ Ошибка подписки на события: {ex.Message}");
            }
        }
        
        private void OnMediaPropertiesChanged(GlobalSystemMediaTransportControlsSession sender, MediaPropertiesChangedEventArgs args)
        {
            try
            {
                _ = UpdateMediaInfo();
            }
            catch (Exception ex)
            {
                Console.WriteLine($"⚠️ Ошибка обновления медиа: {ex.Message}");
            }
        }
        
        private void OnPlaybackInfoChanged(GlobalSystemMediaTransportControlsSession sender, PlaybackInfoChangedEventArgs args)
        {
            try
            {
                var playback = sender.GetPlaybackInfo();
                bool isPlaying = playback.PlaybackStatus == GlobalSystemMediaTransportControlsSessionPlaybackStatus.Playing;
                
                if (State.IsPlaying != isPlaying)
                {
                    State.IsPlaying = isPlaying;
                    TriggerDebouncedUpdate();
                }
            }
            catch (Exception ex)
            {
                Console.WriteLine($"⚠️ Ошибка обновления playback: {ex.Message}");
            }
        }
        
        private void OnTimelinePropertiesChanged(GlobalSystemMediaTransportControlsSession sender, TimelinePropertiesChangedEventArgs args)
        {
            try
            {
                var timeline = sender.GetTimelineProperties();
                if (timeline != null)
                {
                    double position = timeline.Position.TotalSeconds;
                    double duration = timeline.EndTime.TotalSeconds;
                    
                    bool positionJumped = Math.Abs(position - lastPosition) > 3;
                    
                    State.Position = position;
                    State.Duration = duration;
                    lastPosition = position;
                    
                    if (positionJumped || duration != State.Duration)
                    {
                        TriggerDebouncedUpdate();
                    }
                }
            }
            catch (Exception ex)
            {
                Console.WriteLine($"⚠️ Ошибка обновления timeline: {ex.Message}");
            }
        }
        
        private async Task UpdateMediaInfo()
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
                    
                    State.Artist = artist;
                    State.Title = title;
                    State.Position = position;
                    State.Duration = duration;
                    State.IsPlaying = isPlaying;
                    State.SourceId = sourceId;
                    
                    lastPosition = position;
                    lastIsPlaying = isPlaying;
                    
                    TriggerDebouncedUpdate();
                }
                else
                {
                    State.Position = position;
                    State.Duration = duration;
                    State.IsPlaying = isPlaying;
                    State.SourceId = sourceId;
                    lastPosition = position;
                }
            }
            catch (Exception ex)
            {
                Console.WriteLine($"⚠️ Ошибка получения медиа информации: {ex.Message}");
            }
        }
        
        private void TriggerDebouncedUpdate()
        {
            pendingUpdate = true;
            // Увеличиваем debounce до 500мс для снижения частоты HTTP-запросов
            debounceTimer?.Change(500, Timeout.Infinite);
        }
        
        private void OnDebounceTimerElapsed(object? state)
        {
            if (!pendingUpdate) return;
            
            _ = Task.Run(async () =>
            {
                await updateLock.WaitAsync();
                try
                {
                    pendingUpdate = false;
                    await SendToPythonServer();
                }
                finally
                {
                    updateLock.Release();
                }
            });
        }
        
        private async Task LoadSelectedSource()
        {
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
                        lastSelectedSource = selectedSource; // Синхронизируем оба поля
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
            finally
            {
                httpSemaphore.Release();
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
                    
                    await httpSemaphore.WaitAsync().ConfigureAwait(false);
                    try
                    {
                        var data = new { sources };
                        var json = JsonSerializer.Serialize(data);
                        using var content = new StringContent(json, Encoding.UTF8, "application/json");
                        
                        using var response = await httpClient.PostAsync($"{pythonServerUrl}/update_sources", content).ConfigureAwait(false);
                        
                        lastSentSources = currentSourceIds;
                        Console.WriteLine($"📻 Отправлено источников: {sources.Count}");
                    }
                    finally
                    {
                        httpSemaphore.Release();
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
                
                TriggerDebouncedUpdate();
            }
        }

        private async Task SendToPythonServer()
        {
            // Батчинг: не отправляем чаще чем раз в 2 секунды
            var timeSinceLastUpdate = (DateTime.Now - lastHttpUpdate).TotalSeconds;
            if (timeSinceLastUpdate < UPDATE_COOLDOWN_SECONDS)
            {
                return;
            }
            
            await httpSemaphore.WaitAsync().ConfigureAwait(false);
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
                    status = State.Status,
                    source_id = State.SourceId
                };

                var json = JsonSerializer.Serialize(data);
                using var content = new StringContent(json, Encoding.UTF8, "application/json");

                // Используем встроенный таймаут HttpClient (5 секунд)
                using var response = await httpClient.PostAsync($"{pythonServerUrl}/update_from_cs", content).ConfigureAwait(false);
                response.EnsureSuccessStatusCode();
                
                lastHttpUpdate = DateTime.Now;
            }
            catch (TaskCanceledException)
            {
                // Таймаут - игнорируем
            }
            catch (HttpRequestException)
            {
                // Сетевая ошибка - игнорируем
            }
            finally
            {
                httpSemaphore.Release();
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

                        if (currentSession != null)
                        {
                            currentSession.MediaPropertiesChanged -= OnMediaPropertiesChanged;
                            currentSession.PlaybackInfoChanged -= OnPlaybackInfoChanged;
                            currentSession.TimelinePropertiesChanged -= OnTimelinePropertiesChanged;
                        }

                        // Dispose timers and locks
                        debounceTimer?.Dispose();
                        configPollerTimer?.Dispose();
                        updateLock?.Dispose();
                        httpSemaphore?.Dispose();
                        httpClient?.Dispose();

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
