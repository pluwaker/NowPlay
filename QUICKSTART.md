# 🚀 Быстрый старт MediaMonitor

## За 3 шага к работающей системе

### ✅ Шаг 1: Проверка требований

- [ ] Windows 10/11
- [ ] Python 3.8+ установлен
- [ ] .NET 6.0+ установлен
- [ ] Порт 80 свободен

### ✅ Шаг 2: Запуск

**Вариант А: Автоматический (рекомендуется)**
```
Двойной клик на: start_media_monitor.bat
```

**Вариант Б: Ручной**
```bash
# Терминал 1
python main.py

# Терминал 2
cd MediaMonitor
dotnet run
```

### ✅ Шаг 3: Проверка

1. Откройте браузер: http://localhost:80
2. Включите музыку в любом плеере
3. Наблюдайте обновления!

---

## 🧪 Тестирование

```bash
python test_integration.py
```

Должно показать:
- ✅ Сервер доступен
- ✅ Endpoint работает
- ✅ Обновления отправляются

---

## 🎯 Что дальше?

### Для стримеров (OBS)
1. Добавьте Browser Source в OBS
2. URL: `http://localhost:80/visualisation.html`
3. Настройте размер и позицию

### Для разработчиков
- Читайте [API Examples](docs/API_EXAMPLES.md)
- Изучите [Architecture](docs/ARCHITECTURE.md)
- Смотрите [Integration Guide](INTEGRATION_GUIDE_RU.md)

### Настройка
Отключите встроенный Python мониторинг для лучшей производительности:
```json
{
  "use_builtin_monitor": false
}
```

---

## ❓ Проблемы?

### Сервер не запускается
```bash
# Проверьте порт
netstat -ano | findstr :80

# Измените порт в now.py и MediaMonitor.cs
```

### C# не подключается
```bash
# Убедитесь что Python сервер запущен
curl http://localhost:80
```

### Обложки не загружаются
```bash
# Проверьте папку
dir songinfo
```

---

## 📚 Документация

| Документ | Описание |
|----------|----------|
| [INTEGRATION_GUIDE_RU.md](INTEGRATION_GUIDE_RU.md) | Полное руководство |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | Архитектура системы |
| [docs/API_EXAMPLES.md](docs/API_EXAMPLES.md) | Примеры API |
| [docs/CS_PYTHON_INTEGRATION.md](docs/CS_PYTHON_INTEGRATION.md) | Техническая документация |

---

## 💡 Совет

Для использования в OBS или других инструментах стриминга:
- Используйте `visualisation.html` или другие шаблоны из `now_server/`
- Настройте стили под свой дизайн
- Обложки обновляются автоматически!

**Готово! Наслаждайтесь! 🎵**
