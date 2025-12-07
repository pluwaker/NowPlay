# Интеграция C# MediaMonitor с Python сервером

## Обзор архитектуры

```
┌─────────────────────┐
│  Windows Media API  │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐      HTTP POST        ┌──────────────────┐
│  C# MediaMonitor    │ ──────────────────────▶│  Python Server   │
│  - Отслеживание     │   /update_from_cs     │  (now.py)        │
│  - Обложки          │                        │                  │
│  - Метаданные       │                        │  - WebSocket     │
└─────────────────────┘                        │  - HTTP API      │
                                               └────────┬─────────┘
                                                        │
                                                        ▼
                                               ┌──────────────────┐
                                               │  Web Clients     │
                                               │  (Браузеры, OBS) │
                                               └──────────────────┘
```

## Компоненты

### 1. C# MediaMonitor

**Файлы:**
- `MediaMonitor/MediaMonitor.cs` - основная логика мониторинга
- `MediaMonitor/CoverFetcher.cs` - загрузка обложек
- `MediaMonitor/CurrentMediaState.cs` - модель данных
- `MediaMonitor/Program.cs` - точка входа

**Функции:**
- Подключение к Windows Media Control API
- Отслеживание смены треков
- Загрузка обложек в `songinfo/cover.png`
- Отправка данных на Python сервер через HTTP POST

**Отправляемые данные:**
```json
{
  "artist": "string",
  "title": "string", 
  "position": 0.0,
  "duration": 0.0,
  "is_playing": true,
  "cover_version": 1,
  "status": "active"
}
```

### 2. Python Server (now.py)

**Новый endpoint:**
```python
POST /update_from_cs
Content-Type: application/json

{
  "artist": "...",
  "title": "...",
  ...
}
```

**Функции:**
- Прием данных от C# MediaMonitor
- Обновление глобального состояния `current_data`
- Рассылка обновлений всем WebSocket клиентам
- Троттлинг обновлений (100ms минимум между обновлениями)

## Режимы работы

### Режим 1: Только C# MediaMonitor (рекомендуется)

Отключите встроенный Python мониторинг в конфиге:

```json
{
  "use_builtin_monitor": false
}
```

**Преимущества:**
- Более быстрая реакция на смену треков
- Меньше нагрузки на CPU
- Нативная работа с Windows Media API

### Режим 2: Только Python мониторинг

Не запускайте C# MediaMonitor, используйте встроенный Python мониторинг:

```json
{
  "use_builtin_monitor": true
}
```

### Режим 3: Гибридный (не рекомендуется)

Оба мониторинга работают одновременно. Может привести к дублированию обновлений.

## Запуск

### Вариант 1: Автоматический запуск (Windows)

```batch
start_media_monitor.bat
```

Этот скрипт запустит:
1. Python сервер на порту 80
2. C# MediaMonitor

### Вариант 2: Ручной запуск

**Терминал 1 - Python сервер:**
```bash
python main.py
```

**Терминал 2 - C# MediaMonitor:**
```bash
cd MediaMonitor
dotnet run
```

## Настройка

### Изменение порта Python сервера

**В now.py:**
```python
def run_server(port=80):
    ...
```

**В MediaMonitor.cs:**
```csharp
private readonly string pythonServerUrl = "http://localhost:80";
```

### Путь к обложкам

Обложки сохраняются в `songinfo/cover.png` относительно корня проекта.

**В CoverFetcher.cs:**
```csharp
private static readonly string OutputDir = Path.Combine(
    Directory.GetParent(AppDomain.CurrentDomain.BaseDirectory).Parent.Parent.Parent.Parent.FullName,
    "songinfo"
);
```

## Отладка

### Проверка связи

1. Запустите Python сервер
2. Проверьте доступность: `http://localhost:80`
3. Запустите C# MediaMonitor
4. В консоли C# должны появиться сообщения о треках
5. В консоли Python должны появиться сообщения о получении данных

### Типичные проблемы

**Проблема:** C# не может подключиться к Python серверу
- **Решение:** Убедитесь, что Python сервер запущен и порт 80 свободен

**Проблема:** Обложки не сохраняются
- **Решение:** Проверьте права доступа к папке `songinfo/`

**Проблема:** Дублирование обновлений
- **Решение:** Отключите встроенный Python мониторинг (`use_builtin_monitor: false`)

## API Reference

### POST /update_from_cs

Принимает данные о текущем треке от C# MediaMonitor.

**Request:**
```json
{
  "artist": "Artist Name",
  "title": "Track Title",
  "position": 45.5,
  "duration": 180.0,
  "is_playing": true,
  "cover_version": 1,
  "status": "active"
}
```

**Response:**
```json
{
  "status": "success"
}
```

**Errors:**
```json
{
  "status": "error",
  "message": "Error description"
}
```

## Производительность

- **Интервал обновления:** 1 секунда (C# MediaMonitor)
- **Троттлинг:** 100ms минимум между отправками на клиенты
- **HTTP запросы:** Асинхронные, не блокируют основной поток
- **Обложки:** Загружаются только при смене трека

## Безопасность

- Сервер слушает только localhost по умолчанию
- Нет аутентификации (для локального использования)
- Для публичного доступа добавьте аутентификацию

## Будущие улучшения

- [ ] Поддержка HTTPS
- [ ] Аутентификация через токены
- [ ] Конфигурация через файл
- [ ] Автоматическое переподключение при разрыве связи
- [ ] Кэширование обложек
- [ ] Поддержка нескольких источников медиа
