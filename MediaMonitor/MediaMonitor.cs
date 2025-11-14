using System;
using System.Collections.Generic;
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
    public class MediaMonitor
    {
        public CurrentMediaState State = new();

        private GlobalSystemMediaTransportControlsSessionManager? sessionManager;
        private GlobalSystemMediaTransportControlsSession? currentSession;

        private readonly HttpClient httpClient = new HttpClient();
        private readonly string pythonServerUrl = "http://localhost:8080";
        
        // Для отслеживания изменений
        private double lastPosition = 0;
        private bool lastIsPlaying = false;
        private string selectedSource = "";
        
        // Для debouncing обновлений
        private System.Threading.Timer? debounceTimer;
        private bool pendingUpdate = false;
        private readonly SemaphoreSlim updateLock = new SemaphoreSlim(1, 1);

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
        
        private async void OnSessionsChanged(GlobalSystemMediaTransportControlsSessionManager sender, SessionsChangedEventArgs args)
        {
            try
            {
                await UpdateCurrentSession();
            }
            catch (Exception ex)
            {
                Console.WriteLine($"⚠️ Ошибка при смене сессии: {ex.Message}");
            }
        }
        
        private async Task UpdateCurrentSession()
        {
            // Отписываемся от старой сессии
            if (currentSession != null)
            {
                try
                {
                    currentSession.MediaPropertiesChanged -= OnMediaPropertiesChanged;
                    currentSession.PlaybackInfoChanged -= OnPlaybackInfoChanged;
                    currentSession.TimelinePropertiesChanged -= OnTimelinePropertiesChanged;
                }
                catch { }
            }
            
            // Получаем новую сессию
            currentSession = await GetSessionBySource(sessionManager!);
            
            if (currentSession == null)
            {
                SetNoPlayback();
                return;
            }
            
            // Подписываемся на события новой сессии
            try
            {
                currentSession.MediaPropertiesChanged += OnMediaPropertiesChanged;
                currentSession.PlaybackInfoChanged += OnPlaybackInfoChanged;
                currentSession.TimelinePropertiesChanged += OnTimelinePropertiesChanged;
                
                // Получаем начальное состояние
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

                bool trackChanged = artist != State.Artist || title != State.Title;

                if (trackChanged)
                {
                    Console.WriteLine($"🎵 {artist} — {title}");
                    
                    State.Artist = artist;
                    State.Title = title;
                    State.Position = position;
                    State.Duration = duration;
                    State.IsPlaying = isPlaying;
                    
                    lastPosition = position;
                    lastIsPlaying = isPlaying;
                    
                    TriggerDebouncedUpdate();
                }
                else
                {
                    State.Position = position;
                    State.Duration = duration;
                    State.IsPlaying = isPlaying;
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
            debounceTimer?.Change(100, Timeout.Infinite); // Ждем 100мс перед отправкой
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
            try
            {
                var response = await httpClient.GetAsync($"{pythonServerUrl}/get_config");
                if (response.IsSuccessStatusCode)
                {
                    var json = await response.Content.ReadAsStringAsync();
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
                
                // Отправляем список доступных источников на сервер
                await SendAvailableSources();
            }
            catch
            {
                // Игнорируем ошибки загрузки конфига
            }
        }
        
        private async Task SendAvailableSources()
        {
            try
            {
                var manager = await GlobalSystemMediaTransportControlsSessionManager.RequestAsync();
                var sessions = manager.GetSessions();
                
                var sources = new List<object>();
                var seenIds = new HashSet<string>();
                
                foreach (var session in sessions)
                {
                    try
                    {
                        var appId = session.SourceAppUserModelId;
                        if (!string.IsNullOrEmpty(appId) && !seenIds.Contains(appId))
                        {
                            seenIds.Add(appId);
                            
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
                
                var data = new { sources };
                var json = JsonSerializer.Serialize(data);
                var content = new StringContent(json, Encoding.UTF8, "application/json");
                
                await httpClient.PostAsync($"{pythonServerUrl}/update_sources", content);
                Console.WriteLine($"📻 Найдено источников: {sources.Count}");
            }
            catch
            {
                // Игнорируем ошибки отправки источников
            }
        }


        private Task<GlobalSystemMediaTransportControlsSession?> GetSessionBySource(
            GlobalSystemMediaTransportControlsSessionManager manager)
        {
            var sessions = manager.GetSessions();
            
            // Если источник не выбран, берем текущую сессию
            if (string.IsNullOrEmpty(selectedSource) || selectedSource == "auto")
            {
                return Task.FromResult<GlobalSystemMediaTransportControlsSession?>(manager.GetCurrentSession());
            }

            // Ищем сессию по выбранному источнику
            foreach (var session in sessions)
            {
                try
                {
                    var appId = session.SourceAppUserModelId;
                    if (appId == selectedSource)
                    {
                        return Task.FromResult<GlobalSystemMediaTransportControlsSession?>(session);
                    }
                }
                catch { }
            }

            // Если не нашли, возвращаем текущую
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

                // Правильно ждем ответ с таймаутом
                using var cts = new CancellationTokenSource(TimeSpan.FromSeconds(2));
                var response = await httpClient.PostAsync($"{pythonServerUrl}/update_from_cs", content, cts.Token);
                response.EnsureSuccessStatusCode();
            }
            catch (Exception ex)
            {
                // Логируем только тип ошибки без деталей
                Console.WriteLine($"⚠️ HTTP: {ex.GetType().Name}");
            }
        }
    }
}
