# Диагностика проблемы: "Один раз отправляет, потом нет"

## Проблема

MediaMonitor отправляет данные один раз при старте, затем перестает отправлять обновления.

## Возможные причины

### 1. События WinRT не срабатывают
- Windows Media API может "отвалиться" после первого обновления
- Подписки на события могут быть потеряны
- Это именно та проблема, для которой создана система восстановления

### 2. HealthMonitor не запускается
- Если HealthMonitor не работает, восстановление не сработает
- Нужно проверить, что HealthMonitor.Start() вызывается

### 3. UpdateQueue блокируется
- Debounce таймер может не срабатывать
- Блокировка может не освобождаться

## Диагностика

### Шаг 1: Запустите MediaMonitor в диагностическом режиме

```bash
cd MediaMonitor\bin\Release\net6.0-windows10.0.19041.0
.\MediaMonitor.exe --diagnostic
```

### Шаг 2: Проверьте вывод консоли

**При старте вы должны увидеть:**
```
✅ MediaMonitor запущен!
🔗 Подключение к серверу: http://localhost:58080
📥 EventSubscriptionManager: Subscribing to session: Spotify
  ✅ Subscribed to MediaPropertiesChanged
  ✅ Subscribed to PlaybackInfoChanged
  ✅ Subscribed to TimelinePropertiesChanged
✅ EventSubscriptionManager: All subscriptions established
🎵 Мониторинг медиа активен
```

**При изменении трека вы должны увидеть:**
```
🎵 Event: MediaPropertiesChanged at 19:30:45.123
  - Artist - Title
  ⏱ Handler execution time: 15ms
✅ Update sent to Python server
```

**Если события НЕ срабатывают:**
```
[HEALTH] Heartbeat check: Last update 5 seconds ago (healthy)
[HEALTH] Heartbeat check: Last update 10 seconds ago (healthy)
[HEALTH] Heartbeat check: Last update 15 seconds ago (healthy)
...
[HEALTH] Timeout detected: No updates for 30 seconds
🔄 Запуск процедуры восстановления...
[RECOVERY] Initiating recovery procedure (attempt 1/3)
```

### Шаг 3: Проверьте логи

Если запущен диагностический режим, проверьте файл лога в папке `logs/`:
```
logs/mediamonitor_YYYYMMDD_HHMMSS.log
```

## Быстрое исправление

### Вариант 1: Перезапустите MediaMonitor

Просто перезапустите MediaMonitor - это должно восстановить подписки.

### Вариант 2: Используйте диагностический режим

```bash
MediaMonitor.exe --diagnostic
```

Это покажет, что именно происходит.

### Вариант 3: Проверьте медиа-плеер

1. Закройте медиа-плеер (Spotify, iTunes и т.д.)
2. Перезапустите MediaMonitor
3. Запустите медиа-плеер
4. Включите музыку

### Вариант 4: Проверьте, что Python сервер работает

```bash
# В браузере откройте:
http://localhost:58080/

# Должна открыться страница выбора виджета
```

## Проверка компонентов

### HealthMonitor

Проверьте, что HealthMonitor запускается:
```csharp
// В MediaMonitor.cs должно быть:
healthMonitor = new HealthMonitor();
healthMonitor.RecoveryNeeded += OnRecoveryNeeded;
healthMonitor.Start();  // ← Это должно вызываться!
```

### EventSubscriptionManager

Проверьте, что подписки устанавливаются:
```csharp
// В MediaMonitor.cs должно быть:
await eventSubscriptionManager!.Subscribe(currentSession);
```

### UpdateQueue

Проверьте, что обновления ставятся в очередь:
```csharp
// В MediaMonitor.cs должно быть:
updateQueue?.QueueUpdate(State);
```

## Временное решение

Если автоматическое восстановление не работает, можно вручную перезапускать MediaMonitor каждые несколько минут.

Создайте bat-файл `restart_mediamonitor.bat`:
```batch
@echo off
:loop
start /wait MediaMonitor.exe
timeout /t 5
goto loop
```

## Следующие шаги

1. ✅ Запустите MediaMonitor с флагом `--diagnostic`
2. ✅ Включите музыку и смените трек
3. ✅ Проверьте консоль на наличие событий
4. ✅ Если событий нет, подождите 30 секунд - должно сработать восстановление
5. ✅ Если восстановление не срабатывает, сообщите об этом

## Дополнительная информация

- [MediaMonitor/README.md](MediaMonitor/README.md) - полная документация
- [DIAGNOSTIC_MODE.md](MediaMonitor/DIAGNOSTIC_MODE.md) - диагностический режим
- [.kiro/specs/media-source-refresh/design.md](.kiro/specs/media-source-refresh/design.md) - дизайн системы восстановления

---

**Дата:** 8 декабря 2024
