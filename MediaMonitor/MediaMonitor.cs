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

        private GlobalSystemMediaTransportControlsSession? currentSession;
        private CancellationTokenSource? trackTaskCTS;

        private DateTime lastUpdate = DateTime.MinValue;
        private readonly double UPDATE_COOLDOWN = 0.1;

        private readonly HttpClient httpClient = new HttpClient();
        private readonly string pythonServerUrl = "http://localhost:8080";
        
        // Для отслеживания изменений
        private double lastPosition = 0;
        private bool lastIsPlaying = false;
        private string selectedSource = "";
        private bool hasLoggedNoSession = false; // Чтобы не спамить логами

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
            
            Console.WriteLine("🎵 Начинаем мониторинг медиа...");

            while (true)
            {
                try
                {
                    await Tick();
                }
                catch (Exception ex)
                {
                    Console.WriteLine($"Ошибка monitor: {ex.Message}");
                }

                // Увеличиваем интервал до 2 секунд для снижения нагрузки
                await Task.Delay(2000);
            }
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

        private async Task Tick()
        {
            try
            {
                var manager = await GlobalSystemMediaTransportControlsSessionManager.RequestAsync();
                
                // Получаем сессию с учетом выбранного источника
                currentSession = await GetSessionBySource(manager);

                if (currentSession == null)
                {
                    // Выводим отладочную информацию только один раз
                    if (!hasLoggedNoSession)
                    {
                        var allSessions = manager.GetSessions();
                        Console.WriteLine($"⚠️ Сессия не найдена. Всего сессий: {allSessions.Count}");
                        
                        if (allSessions.Count > 0)
                        {
                            Console.WriteLine($"   Выбранный источник: '{selectedSource}'");
                            Console.WriteLine("   Доступные сессии:");
                            foreach (var session in allSessions)
                            {
                                try
                                {
                                    var appId = session.SourceAppUserModelId;
                                    var props = await session.TryGetMediaPropertiesAsync();
                                    Console.WriteLine($"   - {appId}");
                                    Console.WriteLine($"     Трек: {props.Artist} - {props.Title}");
                                }
                                catch (Exception ex)
                                {
                                    Console.WriteLine($"   - Ошибка получения информации: {ex.Message}");
                                }
                            }
                        }
                        
                        hasLoggedNoSession = true;
                    }
                    
                    SetNoPlayback();
                    return;
                }
                
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

            var mediaInfo = await currentSession.TryGetMediaPropertiesAsync();
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

                trackTaskCTS?.Cancel();
                trackTaskCTS = new CancellationTokenSource();

                State.Artist = artist;
                State.Title = title;
                State.Position = position;
                State.Duration = duration;
                State.IsPlaying = isPlaying;

                lastPosition = position;
                lastIsPlaying = isPlaying;

                await SendUpdate(force: true);

                _ = Task.Run(() => ProcessTrackChange(mediaInfo, trackTaskCTS.Token));
            }
            else if (positionJumped || playbackChanged)
            {
                // Отправляем только при перемотке или смене статуса воспроизведения
                State.Position = position;
                State.Duration = duration;
                State.IsPlaying = isPlaying;

                lastPosition = position;
                lastIsPlaying = isPlaying;

                await SendUpdate(force: true);
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
            var sessions = manager.GetSessions();
            
            // Если источник не выбран, берем текущую сессию
            if (string.IsNullOrEmpty(selectedSource) || selectedSource == "auto")
            {
                return manager.GetCurrentSession();
            }

            // Ищем сессию по выбранному источнику
            foreach (var session in sessions)
            {
                try
                {
                    var appId = session.SourceAppUserModelId;
                    if (appId == selectedSource)
                    {
                        return session;
                    }
                }
                catch { }
            }

            // Если не нашли, возвращаем текущую
            return manager.GetCurrentSession();
        }

        private async Task ProcessTrackChange(
            GlobalSystemMediaTransportControlsSessionMediaProperties mediaInfo,
            CancellationToken token)
        {
            try
            {
                // Получаем длительность
                double duration = await WaitForDuration(currentSession);

                if (token.IsCancellationRequested)
                    return;

                State.Duration = duration;

                await SendUpdate(force: true);
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

                await Task.Delay(300);
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
            await SendToPythonServer();
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

                // Отправляем без ожидания ответа для снижения нагрузки
                _ = httpClient.PostAsync($"{pythonServerUrl}/update_from_cs", content);
            }
            catch
            {
                // Игнорируем ошибки отправки чтобы не нагружать CPU логами
            }
        }
    }
}
