# Исправление сброса позиции при Recovery

## Проблема
При восстановлении (Recovery) позиция трека сбрасывалась на ~0 секунд, хотя трек продолжал играть на реальной позиции (например, 40 секунд).

## Причина
1. **HealthMonitor** запускал Recovery каждые 30 секунд без обновлений
2. **RecoveryManager** вызывал `UpdateMediaInfo()` для проверки восстановления
3. **Windows Media API** иногда возвращает некорректную позицию (0.1s вместо реальной)
4. Эта некорректная позиция отправлялась на сервер и сбрасывала прогресс в виджете

## Решение

### 1. Увеличен таймаут HealthMonitor (HealthMonitor.cs)

```csharp
// БЫЛО:
private readonly TimeSpan updateTimeout = TimeSpan.FromSeconds(30);
private readonly TimeSpan heartbeatInterval = TimeSpan.FromSeconds(5);

// СТАЛО:
private readonly TimeSpan updateTimeout = TimeSpan.FromSeconds(120); // 2 минуты
private readonly TimeSpan heartbeatInterval = TimeSpan.FromSeconds(10);
```

**Эффект**: Recovery запускается реже (только если нет обновлений 2 минуты вместо 30 секунд)

### 2. Убрана принудительная проверка в RecoveryManager (RecoveryManager.cs)

```csharp
// БЫЛО:
// Step 4: Force immediate update to verify recovery
await monitor.UpdateMediaInfo();

// СТАЛО:
// Step 4: Verify recovery (без принудительного обновления позиции)
// Ждем естественных событий от Windows Media API
```

**Эффект**: Recovery не запрашивает позицию принудительно

### 3. Добавлен параметр skipInitialUpdate в UpdateCurrentSession (MediaMonitor.cs)

```csharp
// БЫЛО:
internal async Task UpdateCurrentSession()
{
    // ...
    await UpdateMediaInfo(); // Всегда вызывался
}

// СТАЛО:
internal async Task UpdateCurrentSession(bool skipInitialUpdate = false)
{
    // ...
    if (!skipInitialUpdate)
    {
        await UpdateMediaInfo();
    }
    else
    {
        Console.WriteLine($"⏭️ Пропускаем начальное обновление (ждем естественных событий)");
    }
}
```

**Эффект**: Можно переподписаться на события без отправки данных

### 4. RecoveryManager использует skipInitialUpdate (RecoveryManager.cs)

```csharp
// БЫЛО:
await monitor.UpdateCurrentSession();

// СТАЛО:
await monitor.UpdateCurrentSession(skipInitialUpdate: true);
```

**Эффект**: При восстановлении переподписываемся на события, но не отправляем данные

## Результат

✅ Recovery запускается реже (каждые 2 минуты вместо 30 секунд)
✅ Recovery не запрашивает позицию из Windows Media API
✅ Recovery не отправляет данные на сервер
✅ Recovery просто переподписывается на события и ждет естественных обновлений
✅ Позиция больше не сбрасывается во время воспроизведения

## Измененные файлы

1. `MediaMonitor/HealthMonitor.cs` - увеличены таймауты
2. `MediaMonitor/RecoveryManager.cs` - убрана принудительная проверка, добавлен skipInitialUpdate
3. `MediaMonitor/MediaMonitor.cs` - добавлен параметр skipInitialUpdate в UpdateCurrentSession

## Тестирование

1. Запустите приложение
2. Включите музыку
3. Подождите 2+ минуты без взаимодействия
4. Если Recovery запустится, позиция НЕ должна сброситься
5. Трек должен продолжать играть с правильной позицией

## Дата завершения
8 декабря 2024
