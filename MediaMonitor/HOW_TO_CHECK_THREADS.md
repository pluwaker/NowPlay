# Как проверить количество потоков MediaMonitor

## 🎯 Цель
Проверить, накапливаются ли потоки (Task.Run) в MediaMonitor со временем.

## 📊 Метод 1: Python скрипт (простой)

### Требования
```bash
pip install psutil
```

### Запуск
```bash
# Мониторинг каждые 5 секунд (бесконечно)
python MediaMonitor/check_threadpool.py

# Мониторинг каждые 2 секунды в течение 60 секунд
python MediaMonitor/check_threadpool.py 2 60
```

### Что смотреть
- **Потоков**: должно быть стабильно (~10-20 потоков)
- **CPU**: не должен расти со временем
- **Память (RSS)**: не должна расти со временем

### ⚠️ Признаки проблемы
- Количество потоков растет (20 → 50 → 100+)
- CPU растет (2% → 5% → 10%+)
- Память растет постоянно

---

## 🔬 Метод 2: PowerShell скрипт (продвинутый)

### Запуск
```powershell
# Мониторинг каждые 5 секунд (бесконечно)
.\MediaMonitor\check_threadpool_advanced.ps1

# Мониторинг каждые 2 секунды в течение 60 секунд
.\MediaMonitor\check_threadpool_advanced.ps1 -Interval 2 -Duration 60
```

### Что смотреть
- **Потоков**: стабильное количество
- **Handles**: не должно расти
- **Working Set**: стабильная память
- **Топ-5 потоков**: не должны накапливать CPU время

---

## 🪟 Метод 3: Task Manager (Windows)

### Шаги
1. Открой **Task Manager** (Ctrl+Shift+Esc)
2. Вкладка **Details**
3. Найди **MediaMonitor.exe**
4. Правый клик → **Select columns**
5. Включи:
   - **Threads** (количество потоков)
   - **Handles** (количество handles)
   - **CPU** (использование CPU)
   - **Memory (private working set)**

### Наблюдай за:
- **Threads**: должно быть ~10-20, не должно расти
- **CPU**: должно быть ~1-3%, не должно расти
- **Memory**: должна быть стабильной

---

## 📈 Метод 4: Performance Monitor (Windows)

### Шаги
1. Открой **Performance Monitor** (perfmon)
2. Добавь счетчики:
   - **Process → Thread Count → MediaMonitor**
   - **Process → Handle Count → MediaMonitor**
   - **Process → % Processor Time → MediaMonitor**
   - **Process → Private Bytes → MediaMonitor**

3. Наблюдай графики в реальном времени

### Что искать
- **Thread Count**: горизонтальная линия (хорошо) vs растущая линия (плохо)
- **Handle Count**: стабильный (хорошо) vs растущий (плохо)
- **CPU**: стабильный (хорошо) vs растущий (плохо)

---

## 🧪 Тестовый сценарий

Чтобы проверить накопление потоков:

1. **Запусти MediaMonitor**
2. **Запусти мониторинг** (любой из методов выше)
3. **Включи музыку** в плеере (Spotify, YouTube Music, и т.д.)
4. **Перематывай трек** туда-сюда несколько раз
   - Это генерирует много событий TimelinePropertiesChanged
5. **Наблюдай** за количеством потоков

### ✅ Нормальное поведение
- Потоки: 15 → 18 → 16 → 17 (колеблется, но не растет)
- CPU: 2% → 3% → 2% (стабильно)

### ❌ Проблемное поведение
- Потоки: 15 → 25 → 40 → 60 (постоянно растет)
- CPU: 2% → 5% → 10% → 15% (постоянно растет)

---

## 💡 Быстрая проверка (1 команда)

### PowerShell
```powershell
# Показать текущее количество потоков
(Get-Process | Where-Object { $_.ProcessName -like "*MediaMonitor*" }).Threads.Count
```

### CMD
```cmd
tasklist /FI "IMAGENAME eq MediaMonitor.exe" /V
```

---

## 📝 Логирование для анализа

Если хочешь сохранить данные для анализа:

### Python
```bash
python MediaMonitor/check_threadpool.py 5 300 > thread_log.txt
```

### PowerShell
```powershell
.\MediaMonitor\check_threadpool_advanced.ps1 -Interval 5 -Duration 300 | Tee-Object -FilePath thread_log.txt
```

Потом можешь проанализировать `thread_log.txt` и увидеть динамику.
