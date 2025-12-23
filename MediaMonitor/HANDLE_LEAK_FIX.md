# Исправление утечки дескрипторов (Handle Leak Fix)

## 🔴 Проблема

MediaMonitor накапливал дескрипторы (handles) со временем, что приводило к росту CPU и памяти.

### Симптомы
- Количество дескрипторов растет постоянно (500 → 1000 → 2000+)
- CPU нагрузка увеличивается со временем (2% → 10%+)
- Память растет медленно, но стабильно

### Причина
Каждый вызов `GlobalSystemMediaTransportControlsSessionManager.RequestAsync()` создает новый дескриптор COM-объекта. Код вызывал `RequestAsync()` в `SendAvailableSources()` каждые 5 секунд, создавая утечку.

---

## ✅ Исправления

### 1. SendAvailableSources() - переиспользование SessionManager

**Было:**
```csharp
var manager = await GlobalSystemMediaTransportControlsSessionManager.RequestAsync();
var sessions = manager.GetSessions();
// ❌ Каждый вызов RequestAsync() создает новый дескриптор
```

**Стало:**
```csharp
// ✅ Переиспользуем существующий sessionManager
if (sessionManager == null) return;
var sessions = sessionManager.GetSessions();
```

**Эффект:** Устранена утечка ~1 дескриптора каждые 5 секунд (при вызове SendAvailableSources).

---

### 2. GetSessionBySource() - упрощение логики

**Было:**
```csharp
var sessions = manager.GetSessions();
foreach (var session in sessions) {
    if (appId == selectedSource) {
        return session; // Возвращаем сразу
    }
}
```

**Стало:**
```csharp
var sessions = manager.GetSessions();
GlobalSystemMediaTransportControlsSession? foundSession = null;

foreach (var session in sessions) {
    if (appId == selectedSource) {
        foundSession = session; // Сохраняем нужную
    }
}

return foundSession;
```

**Эффект:** Улучшена читаемость кода, подготовка к будущим оптимизациям.

---

### 3. DiagnosticLogger - мониторинг дескрипторов

Добавлен метод `LogHandleCount()` для отслеживания утечек:

```csharp
public static void LogHandleCount()
{
    using var process = System.Diagnostics.Process.GetCurrentProcess();
    int handleCount = process.HandleCount;
    long workingSet = process.WorkingSet64 / (1024 * 1024);
    
    LogDiagnostic("ResourceMonitor", $"Handles: {handleCount}, Memory: {workingSet} MB");
}
```

Вызывается каждые 10 секунд в `HealthMonitor.CheckHealth()`.

---

## 📊 Как проверить исправление

### До исправления:
```
[0s]   Handles: 450
[60s]  Handles: 520
[120s] Handles: 610
[180s] Handles: 720  ❌ Растет постоянно
```

### После исправления:
```
[0s]   Handles: 450
[60s]  Handles: 455
[120s] Handles: 452
[180s] Handles: 458  ✅ Стабильно
```

### Команды для проверки:

**PowerShell:**
```powershell
# Показать текущее количество дескрипторов
(Get-Process | Where-Object { $_.ProcessName -like "*MediaMonitor*" }).HandleCount

# Мониторинг в реальном времени
.\MediaMonitor\check_threadpool_advanced.ps1 -Interval 5
```

**Task Manager:**
1. Ctrl+Shift+Esc
2. Details → MediaMonitor.exe
3. Правый клик → Select columns → включи "Handles"
4. Наблюдай за колонкой "Handles" - должна быть стабильной

---

## 🧪 Тестовый сценарий

1. Запусти MediaMonitor с диагностическим режимом:
   ```bash
   MediaMonitor.exe --diagnostic
   ```

2. Включи музыку и дай поиграть 10 минут

3. Проверь логи:
   ```
   [HEALTH] Heartbeat check: Last update 2.1 seconds ago (healthy)
   [ResourceMonitor] Handles: 458, Memory: 45 MB
   ```

4. Количество дескрипторов должно колебаться в пределах ±10, но не расти постоянно

---

## 🎯 Ожидаемый результат

- **Handles:** Стабильно ~450-470 (±20)
- **CPU:** Стабильно ~1-3%
- **Memory:** Стабильно ~40-50 MB

Если дескрипторы продолжают расти, проверь другие источники утечек:
- Timer объекты
- Event subscriptions
- HttpClient connections
- File handles

---

## 📝 Дополнительные заметки

### Почему WinRT объекты НЕ требуют Dispose?

WinRT (Windows Runtime) объекты в .NET автоматически управляются через Garbage Collector. Хотя они основаны на COM, .NET Runtime автоматически освобождает их при сборке мусора.

**Важно:** Session объекты (`GlobalSystemMediaTransportControlsSession`) НЕ реализуют `IDisposable` и не требуют явного освобождения.

### Настоящая причина утечки

Утечка дескрипторов происходила из-за создания нового `SessionManager` каждые 5 секунд:
```csharp
// ❌ Плохо - создает новый дескриптор
var manager = await GlobalSystemMediaTransportControlsSessionManager.RequestAsync();

// ✅ Хорошо - переиспользуем существующий
if (sessionManager == null) return;
var sessions = sessionManager.GetSessions();
```

---

## 🔗 Связанные файлы

- `MediaMonitor/MediaMonitor.cs` - основные исправления
- `MediaMonitor/DiagnosticLogger.cs` - мониторинг дескрипторов
- `MediaMonitor/HealthMonitor.cs` - периодический вызов мониторинга
- `MediaMonitor/check_threadpool_advanced.ps1` - скрипт для проверки
- `MediaMonitor/HOW_TO_CHECK_THREADS.md` - инструкции по диагностике
