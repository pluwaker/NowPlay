# Как увидеть логи MediaMonitor

## Проблема

MediaMonitor запускается через Python приложение с флагом `CREATE_NO_WINDOW`, поэтому консоль скрыта и логи не видны.

## Решение: Запустить MediaMonitor вручную

### Вариант 1: Использовать bat-файл (РЕКОМЕНДУЕТСЯ)

1. **Пересоберите MediaMonitor:**
   ```bash
   cd MediaMonitor
   dotnet build -c Release
   cd ..
   ```

2. **Запустите Python приложение** (оно запустит сервер на порту 58080)

3. **В отдельном терминале запустите:**
   ```bash
   run_mediamonitor_debug.bat
   ```

4. **Откроется консоль MediaMonitor** с детальными логами

5. **Дождитесь автоматического переключения трека** и посмотрите логи

### Вариант 2: Запустить MediaMonitor.exe напрямую

1. **Пересоберите MediaMonitor:**
   ```bash
   cd MediaMonitor
   dotnet build -c Release
   ```

2. **Запустите Python приложение** (оно запустит сервер на порту 58080)

3. **В отдельном терминале:**
   ```bash
   cd MediaMonitor\bin\Release\net6.0-windows10.0.19041.0
   MediaMonitor.exe --port 58080
   ```

4. **Дождитесь автоматического переключения трека** и посмотрите логи

### Вариант 3: Изменить тип проекта C# (для постоянной консоли)

Откройте `MediaMonitor/MediaMonitor.csproj` и измените:

```xml
<OutputType>WinExe</OutputType>
```

на:

```xml
<OutputType>Exe</OutputType>
```

Затем пересоберите проект. Теперь консоль будет всегда видна.

## Что искать в логах

### При старте:
```
✅ MediaMonitor запущен!
🔗 Подключение к серверу: http://localhost:58080
✅ Event-driven мониторинг инициализирован
🔍 Поиск источников... Найдено сессий: 1
  📱 Сессия: Spotify.exe
  ✅ Добавлен источник: Spotify
📊 Итого найдено источников: 1, изменились: true, force: true
📤 Отправка данных на сервер: {"sources":[...]}
📻 Отправлено источников: 1 (статус: 200)
```

### При автоматическом переключении трека:
```
🔔 Событие SessionsChanged сработало
⏳ Ожидание 300ms для обновления сессий...
📡 Отправка обновленного списка источников...
🔍 Поиск источников... Найдено сессий: ???
  📱 Сессия: ???
📊 Итого найдено источников: ???
```

## Важно!

- **Не запускайте два экземпляра MediaMonitor одновременно!**
- Если Python приложение уже запустило MediaMonitor, остановите его перед ручным запуском
- Или просто не запускайте Python приложение, а запустите только сервер вручную

## После отладки

Чтобы вернуть скрытую консоль, верните изменения в `ui/mediamonitor_manager.py`:

```python
# Вернуть CREATE_NO_WINDOW вместо CREATE_NEW_CONSOLE
self.process = subprocess.Popen(
    command,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    stdin=subprocess.PIPE,
    creationflags=CREATE_NO_WINDOW
)
```

---

**Дата:** 7 декабря 2024
