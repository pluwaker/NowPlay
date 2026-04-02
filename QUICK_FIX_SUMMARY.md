# Исправления для обновления позиции при перемотке

## Проблемы и решения

### 1. ❌ События перемотки не передавались в виджет
**Причина:** `EventSubscriptionManager.cs` не вызывал `OnMediaUpdated()` в обработчиках `OnTimelinePropertiesChanged` и `OnPlaybackInfoChanged`

**Решение:** ✅ Добавлены вызовы `OnMediaUpdated()` в оба обработчика

**Файл:** `MediaMonitor/EventSubscriptionManager.cs`

---

### 2. ❌ MediaMonitor блокировался при запуске через приложение
**Причина:** `mediamonitor_manager.py` использовал `subprocess.PIPE` для stdout/stderr, что создавало буфер ограниченного размера (~65KB). При большом количестве логов буфер заполнялся и процесс блокировался.

**Решение:** ✅ Заменено на `subprocess.DEVNULL` для отбрасывания вывода без буферизации

**Файл:** `ui/mediamonitor_manager.py`

---

## Как применить

### Вариант 1: Через приложение (рекомендуется)
1. Запустите `main.py` или скомпилированное приложение
2. Нажмите START
3. Перемотайте трек - позиция должна обновляться

### Вариант 2: Вручную
1. Остановите все процессы MediaMonitor
2. Пересоберите: `cd MediaMonitor && dotnet build`
3. Запустите MediaMonitor и сервер
4. Проверьте перемотку

---

### 3. ❌ Время сбрасывалось при перемотке (29-34 секунды)
**Причина 1:** `UpdateQueue.cs` использовал debounce 500ms  
**Причина 2:** `now.py` использовал троттлинг UPDATE_COOLDOWN 100ms  

При частых событиях перемотки обновления блокировались обоими механизмами.

**Решение:** ✅ Отключен debounce в UpdateQueue.cs и троттлинг в now.py

**Файлы:** `MediaMonitor/UpdateQueue.cs`, `now_server/now.py`

---

## Что теперь работает

✅ События перемотки (TimelinePropertiesChanged) передаются в виджет  
✅ События play/pause (PlaybackInfoChanged) передаются в виджет  
✅ MediaMonitor не блокируется при запуске через приложение  
✅ Позиция обновляется в реальном времени при перемотке  
✅ Debounce не блокирует частые обновления позиции  

---

## Технические детали

**Цепочка обновлений:**
```
Windows Media API
  ↓ TimelinePropertiesChanged
EventSubscriptionManager.OnTimelinePropertiesChanged()
  ↓ OnMediaUpdated()
MediaMonitor.OnMediaUpdated()
  ↓ QueueUpdate()
UpdateQueue
  ↓ OnUpdateReady()
HttpClientPool.SendUpdate()
  ↓ HTTP POST /update_from_cs
Python Server (now.py)
  ↓ WebSocket
JavaScript Widget
  ↓ updatePlayer()
UI обновляется ✅
```
