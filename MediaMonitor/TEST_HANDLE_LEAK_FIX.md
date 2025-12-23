# Тестирование исправления утечки дескрипторов

## 🎯 Цель
Проверить, что количество дескрипторов остается стабильным после исправлений.

## 📋 Быстрый тест (5 минут)

### 1. Запусти MediaMonitor
```bash
cd MediaMonitor
dotnet run
```

### 2. В другом терминале запусти мониторинг
```powershell
# PowerShell
.\MediaMonitor\check_threadpool_advanced.ps1 -Interval 10 -Duration 300
```

### 3. Включи музыку
- Запусти любой плеер (Spotify, YouTube Music, и т.д.)
- Включи трек

### 4. Создай нагрузку
- Перематывай трек туда-сюда
- Переключай треки
- Ставь на паузу и снова play

### 5. Наблюдай за дескрипторами
```
[0s]   🔗 Handles: 450
[10s]  🔗 Handles: 455
[20s]  🔗 Handles: 452
[30s]  🔗 Handles: 458
...
```

## ✅ Критерии успеха

### Хорошо (исправление работает):
- Handles колеблется: 450 → 455 → 452 → 458
- Разброс в пределах ±20
- Нет постоянного роста

### Плохо (утечка осталась):
- Handles растет: 450 → 480 → 520 → 570
- Постоянный рост без стабилизации
- Разброс > 50

---

## 🔬 Детальный тест (30 минут)

### 1. Запусти с диагностикой
```bash
cd MediaMonitor
dotnet run -- --diagnostic
```

### 2. Мониторинг в отдельном окне
```powershell
.\MediaMonitor\check_threadpool_advanced.ps1 -Interval 30 -Duration 1800
```

### 3. Сценарий нагрузки
Выполни каждое действие по 5 раз:
- ✅ Переключение треков
- ✅ Перемотка вперед/назад
- ✅ Пауза/Play
- ✅ Смена источника (если есть несколько плееров)

### 4. Проверь логи
```bash
# Найди последний лог-файл
ls MediaMonitor/logs/

# Проверь количество дескрипторов
cat MediaMonitor/logs/mediamonitor_diagnostic_*.log | grep "Handles:"
```

Должно быть примерно так:
```
[10:15:23.456] [ResourceMonitor] Handles: 452, Memory: 45 MB
[10:15:33.789] [ResourceMonitor] Handles: 455, Memory: 45 MB
[10:15:43.123] [ResourceMonitor] Handles: 451, Memory: 46 MB
```

---

## 📊 Сравнение до/после

### До исправления:
```
Время  | Handles | CPU  | Memory
-------|---------|------|--------
0 мин  | 450     | 2%   | 40 MB
5 мин  | 520     | 3%   | 42 MB
10 мин | 610     | 5%   | 45 MB
15 мин | 720     | 8%   | 48 MB  ❌
```

### После исправления:
```
Время  | Handles | CPU  | Memory
-------|---------|------|--------
0 мин  | 450     | 2%   | 40 MB
5 мин  | 455     | 2%   | 41 MB
10 мин | 452     | 2%   | 41 MB
15 мин | 458     | 2%   | 42 MB  ✅
```

---

## 🐛 Если утечка осталась

### 1. Проверь версию кода
```bash
git log --oneline -1 MediaMonitor/MediaMonitor.cs
```

Должно быть последнее исправление с "Handle leak fix".

### 2. Проверь, что используется правильный SessionManager
В логах должно быть:
```
✅ MediaMonitor запущен!
✅ Event-driven мониторинг инициализирован
```

НЕ должно быть множественных:
```
❌ Requesting new SessionManager instance  (повторяется часто)
```

### 3. Проверь другие источники утечек
```powershell
# Проверь открытые файлы
Get-Process MediaMonitor | Select-Object -ExpandProperty Modules | Measure-Object

# Проверь потоки
(Get-Process MediaMonitor).Threads.Count
```

### 4. Собери диагностику
```bash
# Запусти с диагностикой на 10 минут
dotnet run -- --diagnostic

# Отправь лог-файл для анализа
cat MediaMonitor/logs/mediamonitor_diagnostic_*.log
```

---

## 💡 Полезные команды

### Текущее количество дескрипторов
```powershell
(Get-Process | Where-Object { $_.ProcessName -like "*MediaMonitor*" }).HandleCount
```

### График дескрипторов в реальном времени
```powershell
while ($true) {
    $handles = (Get-Process | Where-Object { $_.ProcessName -like "*MediaMonitor*" }).HandleCount
    Write-Host "$(Get-Date -Format 'HH:mm:ss') - Handles: $handles"
    Start-Sleep -Seconds 5
}
```

### Сравнение с другими процессами
```powershell
Get-Process | Sort-Object HandleCount -Descending | Select-Object -First 10 Name, HandleCount
```

---

## 📝 Отчет о тестировании

После тестирования заполни:

- [ ] Handles стабильны (±20)
- [ ] CPU стабилен (~2-3%)
- [ ] Memory стабильна (~40-50 MB)
- [ ] Нет ошибок в логах
- [ ] Программа работает > 30 минут без проблем

Если все пункты отмечены ✅ - исправление работает!
