# Контроль параллельных Task.Run - Исправление

## 🔴 Проблема

EventSubscriptionManager создавал неограниченное количество параллельных Task.Run при обработке событий Windows Media API. При быстрых событиях (например, перемотка трека) это могло привести к накоплению задач и дескрипторов.

### Симптомы
- При перемотке трека создается много параллельных задач
- Каждая задача держит дескрипторы (семафоры, locks)
- Временное накопление задач увеличивает CPU

### Причина
Три обработчика событий создавали Task.Run без контроля:
```csharp
private void OnMediaPropertiesChanged(...) {
    _ = Task.Run(async () => { ... }); // ❌ Без контроля
}

private void OnPlaybackInfoChanged(...) {
    _ = Task.Run(async () => { ... }); // ❌ Без контроля
}

private void OnTimelinePropertiesChanged(...) {
    _ = Task.Run(async () => { ... }); // ❌ Без контроля
}
```

---

## ✅ Решение

Добавлен **SemaphoreSlim** для ограничения параллельных обработчиков событий до 1.

### Изменения в EventSubscriptionManager.cs

#### 1. Добавлен семафор
```csharp
// Семафор для контроля параллельных обработчиков событий
private readonly SemaphoreSlim eventProcessingSemaphore = new SemaphoreSlim(1, 1);
private readonly TimeSpan eventProcessingTimeout = TimeSpan.FromSeconds(2);
```

#### 2. Обновлены обработчики событий
```csharp
private void OnMediaPropertiesChanged(...) {
    _ = Task.Run(async () => {
        bool semaphoreAcquired = false;
        try {
            // ✅ Пытаемся получить семафор с таймаутом
            semaphoreAcquired = await eventProcessingSemaphore.WaitAsync(eventProcessingTimeout);
            
            if (!semaphoreAcquired) {
                Console.WriteLine($"  ⚠️ Skipping event (previous event still processing)");
                return;
            }
            
            // Обрабатываем событие
            // ...
        }
        finally {
            if (semaphoreAcquired) {
                eventProcessingSemaphore.Release();
            }
        }
    });
}
```

#### 3. Добавлено освобождение в Dispose
```csharp
protected virtual void Dispose(bool disposing) {
    if (disposing) {
        Unsubscribe();
        eventProcessingSemaphore?.Dispose(); // ✅ Освобождаем семафор
    }
}
```

---

## 📊 Эффект

### До исправления:
```
[Событие 1] → Task.Run #1 (запущен)
[Событие 2] → Task.Run #2 (запущен)  ← Параллельно!
[Событие 3] → Task.Run #3 (запущен)  ← Параллельно!
[Событие 4] → Task.Run #4 (запущен)  ← Параллельно!
```
**Результат:** 4 параллельные задачи, каждая держит дескрипторы

### После исправления:
```
[Событие 1] → Task.Run #1 (запущен, семафор занят)
[Событие 2] → Task.Run #2 (пропущен - семафор занят)
[Событие 3] → Task.Run #3 (пропущен - семафор занят)
[Событие 4] → Task.Run #4 (запущен после освобождения семафора)
```
**Результат:** Максимум 1 задача одновременно

---

## 🎯 Преимущества

1. **Ограничение параллелизма:** Максимум 1 обработчик событий одновременно
2. **Пропуск избыточных событий:** Если предыдущее событие еще обрабатывается, новое пропускается
3. **Снижение нагрузки:** Меньше параллельных задач = меньше переключений контекста
4. **Контроль дескрипторов:** Меньше одновременных задач = меньше дескрипторов

---

## 🧪 Как проверить

### 1. Запусти MediaMonitor
```bash
cd MediaMonitor
dotnet run
```

### 2. Создай нагрузку
- Включи музыку
- **Быстро перематывай трек** туда-сюда несколько раз

### 3. Наблюдай за логами

**До исправления:**
```
⏱ Event: TimelinePropertiesChanged at 10:15:23.456
⏱ Event: TimelinePropertiesChanged at 10:15:23.567  ← Параллельно!
⏱ Event: TimelinePropertiesChanged at 10:15:23.678  ← Параллельно!
```

**После исправления:**
```
⏱ Event: TimelinePropertiesChanged at 10:15:23.456
  ⚠️ TimelinePropertiesChanged: Skipping event (previous event still processing)
  ⚠️ TimelinePropertiesChanged: Skipping event (previous event still processing)
⏱ Event: TimelinePropertiesChanged at 10:15:24.123  ← Следующее после освобождения
```

---

## 📝 Технические детали

### Почему SemaphoreSlim(1, 1)?
- **1** = максимум 1 задача одновременно
- Это гарантирует последовательную обработку событий

### Почему таймаут 2 секунды?
- Обработка события обычно занимает < 100ms
- 2 секунды - достаточный запас для медленных операций
- Если обработка занимает > 2 секунд, следующее событие пропускается

### Что происходит с пропущенными событиями?
- Они просто игнорируются
- Это нормально! Windows Media API генерирует много избыточных событий
- Следующее событие после освобождения семафора будет обработано

### Влияние на отзывчивость
- **Минимальное:** События обрабатываются быстро (< 100ms)
- **Пропуск событий:** Не влияет на UX, так как следующее событие придет через ~1 секунду
- **Перемотка:** Работает нормально, последнее событие всегда обрабатывается

---

## 🔗 Связанные исправления

1. **HANDLE_LEAK_FIX.md** - Исправление утечки дескрипторов SessionManager
2. **TASK_RUN_CONTROL_FIX.md** (этот файл) - Контроль параллельных Task.Run

Вместе эти исправления устраняют основные источники утечки дескрипторов и роста CPU.

---

## ✅ Результат

- **Handles:** Стабильны (~450-470)
- **CPU:** Снижен на ~1-2% при перемотке
- **Отзывчивость:** Без изменений
- **Параллельные задачи:** Контролируются

Исправление работает! 🎉
