# Исправление утечки дескрипторов - Краткая сводка

## 🔴 Проблема
MediaMonitor накапливал дескрипторы Windows, что приводило к росту CPU со временем.

## ✅ Решение
1. Переиспользование SessionManager вместо создания нового
2. Контроль параллельных Task.Run через семафоры

## 📝 Изменения

### 1. MediaMonitor.cs
- **SendAvailableSources()**: Переиспользование `sessionManager` вместо создания нового
- **GetSessionBySource()**: Упрощение логики

### 2. EventSubscriptionManager.cs
- Добавлен **SemaphoreSlim** для контроля параллельных обработчиков событий
- Ограничение: максимум 1 обработчик одновременно
- Таймаут: 2 секунды на обработку события

### 3. DiagnosticLogger.cs
- Добавлен метод `LogHandleCount()` для мониторинга дескрипторов

### 4. HealthMonitor.cs
- Добавлен вызов `LogHandleCount()` каждые 10 секунд

## 🧪 Как проверить

```powershell
# Запусти MediaMonitor
cd MediaMonitor
dotnet run

# В другом окне - мониторинг
.\MediaMonitor\check_threadpool_advanced.ps1 -Interval 10
```

Наблюдай за колонкой **Handles** - должна быть стабильной (~450-470).

## 📊 Ожидаемый результат

**До:**
- Handles: 450 → 520 → 610 → 720 (растет постоянно) ❌

**После:**
- Handles: 450 → 455 → 452 → 458 (стабильно ±20) ✅

## 📚 Документация

- `MediaMonitor/HANDLE_LEAK_FIX.md` - детальное описание
- `MediaMonitor/TEST_HANDLE_LEAK_FIX.md` - инструкции по тестированию
- `MediaMonitor/HOW_TO_CHECK_THREADS.md` - инструменты диагностики

## 🚀 Следующие шаги

1. Скомпилируй: `dotnet build MediaMonitor`
2. Запусти: `dotnet run --project MediaMonitor`
3. Протестируй 10-30 минут с музыкой
4. Проверь стабильность дескрипторов

Если дескрипторы стабильны - проблема решена! 🎉
