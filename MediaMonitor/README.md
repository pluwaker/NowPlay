# MediaMonitor - C# интеграция с Python сервером

## Описание

MediaMonitor - это C# приложение, которое отслеживает текущее воспроизведение медиа в Windows (через Windows Media Control API) и отправляет данные на Python сервер now.py.

## Функциональность

- ✅ Отслеживание текущего трека (исполнитель, название)
- ✅ Получение обложки альбома
- ✅ Отслеживание позиции воспроизведения и длительности
- ✅ Определение статуса воспроизведения (играет/пауза)
- ✅ Автоматическая отправка данных на Python сервер через HTTP API

## Как это работает

1. **MediaMonitor.cs** - основной класс, который:
   - Подключается к Windows Media Control API
   - Отслеживает изменения треков
   - Отправляет данные на Python сервер через HTTP POST запросы

2. **CoverFetcher.cs** - загружает и сохраняет обложки альбомов в папку `songinfo/`

3. **CurrentMediaState.cs** - модель данных о текущем треке

4. **Python сервер (now.py)** - принимает данные через endpoint `/update_from_cs` и рассылает их всем подключенным WebSocket клиентам

## Запуск

### 1. Запустите Python сервер

```bash
python main.py
```

Сервер запустится на `http://localhost:80`

### 2. Соберите и запустите C# приложение

```bash
cd MediaMonitor
dotnet build
dotnet run
```

Или откройте `MediaMonitor.sln` в Visual Studio и запустите проект.

## Конфигурация

По умолчанию MediaMonitor подключается к Python серверу на `http://localhost:80`. 

Чтобы изменить адрес сервера, отредактируйте в `MediaMonitor.cs`:

```csharp
private readonly string pythonServerUrl = "http://localhost:80";
```

## Структура данных

MediaMonitor отправляет следующие данные на Python сервер:

```json
{
  "artist": "Имя исполнителя",
  "title": "Название трека",
  "position": 45.5,
  "duration": 180.0,
  "is_playing": true,
  "cover_version": 1,
  "status": "active"
}
```

## Обложки

Обложки сохраняются в папку `songinfo/cover.png` относительно корня проекта.

## Требования

- .NET 6.0 или выше
- Windows 10/11 (для Windows Media Control API)
- Python сервер now.py должен быть запущен
