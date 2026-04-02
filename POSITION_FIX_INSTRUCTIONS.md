# Инструкция по применению фикса для перемотки

## Проблема
События перемотки (TimelinePropertiesChanged) и изменения статуса (PlaybackInfoChanged) получаются MediaMonitor, но не передаются дальше в виджет.

## Решение
Исправлен `EventSubscriptionManager.cs` - добавлены вызовы `OnMediaUpdated()` в обработчики событий.

## Как применить

### 1. Остановите MediaMonitor
Закройте процесс MediaMonitor.exe (если запущен)

### 2. Пересоберите проект
```bash
cd MediaMonitor
dotnet build MediaMonitor.csproj
```

### 3. Запустите MediaMonitor заново
```bash
cd MediaMonitor/bin/Debug/net6.0-windows10.0.19041.0
./MediaMonitor.exe
```

### 4. Проверьте работу
- Запустите медиа-плеер
- Перемотайте трек
- Проверьте, что позиция обновляется в виджете

## Что изменилось

### До:
- `OnTimelinePropertiesChanged` - только логировал события ❌
- `OnPlaybackInfoChanged` - только логировал события ❌

### После:
- `OnTimelinePropertiesChanged` - логирует И вызывает `OnMediaUpdated()` ✅
- `OnPlaybackInfoChanged` - логирует И вызывает `OnMediaUpdated()` ✅

Теперь все события передаются через UpdateQueue → HttpClientPool → Python сервер → WebSocket → Виджет
