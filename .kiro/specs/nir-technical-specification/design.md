# Design Document: Техническое Задание для проекта NowPlay

## Overview

Данный документ описывает детальный дизайн системы для создания технического задания (ТЗ) по проекту **"Разработка кроссплатформенной системы управления и визуализации мультимедийного контента для стриминговых сервисов"** (NowPlay).

Система представляет собой комплексное решение для автоматического отображения информации о текущем воспроизводимом мультимедийном контенте в стриминговых приложениях (OBS Studio, Streamlabs). Проект включает desktop-приложение с графическим интерфейсом, веб-сервер с API и WebSocket, а также настраиваемые веб-виджеты для визуализации.

**Ключевые особенности:**
- Трёхуровневая кроссплатформенная архитектура
- Автоматическое определение текущего трека через системные API
- Получение метаданных и обложек из множественных источников
- 4 настраиваемых шаблона визуализации
- Алгоритм автоматического извлечения цветовой палитры из обложек
- Оптимизированная производительность (CPU < 2%)
- Интеграция C# и Python компонентов

## Architecture

### Общая архитектура системы

Система построена на основе трёхуровневой архитектуры, обеспечивающей разделение ответственности и кроссплатформенность:

```
┌─────────────────────────────────────────────────────────────────────┐
│                    Уровень 1: Desktop Application                    │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │  GUI (CustomTkinter)                                           │ │
│  │  - Главное окно с навигацией                                   │ │
│  │  - Страница Start (запуск/остановка сервера)                   │ │
│  │  - Страница Settings (настройка параметров)                    │ │
│  │  - Страница Info (информация о приложении)                     │ │
│  │  - Управление конфигурацией (config_manager.py)                │ │
│  └────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    Уровень 2: Web Server                             │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │  aiohttp Server (now.py)                                       │ │
│  │  - HTTP API endpoints                                          │ │
│  │  - WebSocket для real-time обновлений                          │ │
│  │  - Управление состоянием (current_data)                        │ │
│  │  - Интеграция с C# MediaMonitor                                │ │
│  │                                                                 │ │
│  │  Cover Fetcher (cover_fetcher.py)                              │ │
│  │  - Получение обложек из Last.fm, iTunes, Yandex, VK           │ │
│  │  - Кэширование и оптимизация запросов                          │ │
│  └────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                  Уровень 3: Frontend Widgets                         │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │  HTML/CSS/JavaScript Widgets                                   │ │
│  │  - visualisation.html (вертикальный)                           │ │
│  │  - visualisation_var2.html (альтернативный)                    │ │
│  │  - visualisation_var3.html (минималистичный)                   │ │
│  │  - visualisation_horizontal.html (горизонтальный)              │ │
│  │  - common.js (общая логика)                                    │ │
│  │  - WebSocket клиент для получения обновлений                   │ │
│  │  - Canvas API для извлечения цветов                            │ │
│  └────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
```

### Интеграция C# MediaMonitor

Для оптимальной производительности и быстрой реакции на смену треков используется C# компонент:

```
┌─────────────────────────────────────────────────────────────────────┐
│                    C# MediaMonitor Component                         │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │  MediaMonitor.cs                                               │ │
│  │  - Tick() каждую секунду                                       │ │
│  │  - Отслеживание смены треков (artist/title)                    │ │
│  │  - Получение метаданных (position, duration, is_playing)       │ │
│  │  - Управление состоянием                                       │ │
│  │                                                                 │ │
│  │  CoverFetcher.cs                                               │ │
│  │  - Загрузка обложек из Thumbnail                               │ │
│  │  - Сохранение в songinfo/cover.png                             │ │
│  │                                                                 │ │
│  │  CurrentMediaState.cs                                          │ │
│  │  - Модель данных о треке                                       │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                              │                                       │
│                              ▼ HTTP POST                             │
│                    Python Server (now.py)                            │
└─────────────────────────────────────────────────────────────────────┘
```

### Поток данных

1. **Обнаружение трека:**
   - Windows Media API → C# MediaMonitor.Tick()
   - Сравнение artist/title с предыдущим состоянием
   - При изменении: параллельная загрузка обложки и получение длительности

2. **Передача данных:**
   - C# → HTTP POST /update_from_cs → Python Server
   - JSON payload: {artist, title, position, duration, is_playing, cover_version, status}

3. **Распространение обновлений:**
   - Python Server → WebSocket → Все подключенные клиенты
   - Троттлинг: минимум 100ms между обновлениями

4. **Визуализация:**
   - Веб-виджет получает данные через WebSocket
   - Загружает обложку: GET /cover?v={cover_version}
   - Извлекает цвета из обложки (если включено)
   - Обновляет UI с анимациями

## Components and Interfaces

### 1. Desktop Application (Python)

**Модуль: main.py**
- Точка входа приложения
- Инициализация GUI
- Запуск event loop

**Модуль: ui/app.py**
```python
class App(ctk.CTk):
    def __init__(self):
        # Инициализация главного окна
        # Создание боковой панели навигации
        # Загрузка страниц
        
    def show_page(self, page_name: str):
        # Переключение между страницами
        
    def on_closing(self):
        # Корректное завершение приложения
```

**Модуль: ui/pages/start_page.py**
```python
class StartPage(ctk.CTkFrame):
    def __init__(self, parent, server_manager):
        # UI элементы: кнопка START/STOP, статус, ссылка
        
    def toggle_server(self):
        # Запуск/остановка веб-сервера
        
    def update_status(self):
        # Обновление индикаторов статуса
```

**Модуль: ui/pages/settings_page.py**
```python
class SettingsPage(ctk.CTkFrame):
    def __init__(self, parent, config_manager):
        # UI элементы: выбор шаблона, цвета, позиционирование
        
    def save_settings(self):
        # Сохранение настроек в config.json
        
    def load_settings(self):
        # Загрузка текущих настроек
```

**Модуль: src/config/config_manager.py**
```python
class ConfigManager:
    def __init__(self, config_path: str):
        # Инициализация с путем к config.json
        
    def load_config(self) -> dict:
        # Загрузка конфигурации из файла
        
    def save_config(self, config: dict):
        # Сохранение конфигурации в файл
        
    def get(self, key: str, default=None):
        # Получение значения параметра
        
    def set(self, key: str, value):
        # Установка значения параметра
```

### 2. Web Server (Python)

**Модуль: now_server/now.py**
```python
# Глобальное состояние
current_data = {
    "artist": "",
    "title": "",
    "position": 0.0,
    "duration": 0.0,
    "is_playing": False,
    "cover_version": 0,
    "status": "inactive"
}

listeners = set()  # WebSocket соединения

# HTTP Endpoints
async def update_from_cs(request):
    """POST /update_from_cs - Получение данных от C# MediaMonitor"""
    # Парсинг JSON
    # Обновление current_data
    # Вызов send_to_listeners()
    
async def get_cover(request):
    """GET /cover?v={version} - Получение обложки"""
    # Чтение songinfo/cover.png
    # Возврат с кэшированием
    
async def websocket_handler(request):
    """GET /ws - WebSocket соединение"""
    # Добавление в listeners
    # Отправка начального состояния
    # Ожидание сообщений
    # Удаление при отключении
    
async def update_config(request):
    """POST /update_config - Обновление конфигурации"""
    # Парсинг JSON
    # Сохранение в config.json
    # Уведомление клиентов
    
async def send_to_listeners():
    """Рассылка обновлений по WebSocket"""
    # Проверка троттлинга (100ms)
    # Формирование JSON сообщения
    # Отправка всем активным listeners
    # Очистка мертвых соединений
```

**Модуль: now_server/cover_fetcher.py**
```python
class CoverFetcher:
    def __init__(self):
        self.sources = [
            LastFmSource(),
            ITunesSource(),
            YandexMusicSource(),
            VKMusicSource()
        ]
        
    async def fetch_cover(self, artist: str, title: str) -> bytes:
        """Получение обложки из источников с приоритизацией"""
        for source in self.sources:
            try:
                cover_data = await source.get_cover(artist, title)
                if cover_data:
                    return cover_data
            except Exception as e:
                # Логирование и переход к следующему источнику
                continue
        return self.get_default_cover()
        
    def get_default_cover(self) -> bytes:
        """Возврат дефолтной обложки"""
        # Чтение songinfo/NoCover.png
```

### 3. C# MediaMonitor

**Класс: MediaMonitor.cs**
```csharp
public class MediaMonitor
{
    private GlobalSystemMediaTransportControlsSessionManager sessionManager;
    private CurrentMediaState currentState;
    private string pythonServerUrl = "http://localhost:80";
    
    public async Task Tick()
    {
        // Получение текущей сессии
        var session = sessionManager.GetCurrentSession();
        if (session == null) {
            await SendInactiveStatus();
            return;
        }
        
        // Получение метаданных
        var mediaProperties = await session.TryGetMediaPropertiesAsync();
        string artist = mediaProperties.Artist;
        string title = mediaProperties.Title;
        
        // Проверка смены трека
        if (artist != currentState.Artist || title != currentState.Title) {
            await OnTrackChanged(artist, title, session);
        }
        
        // Обновление позиции
        var timeline = session.GetTimelineProperties();
        if (Math.Abs(timeline.Position.TotalSeconds - currentState.Position) > 2) {
            currentState.Position = timeline.Position.TotalSeconds;
            await SendToPythonServer();
        }
    }
    
    private async Task OnTrackChanged(string artist, string title, session)
    {
        currentState.Artist = artist;
        currentState.Title = title;
        currentState.CoverVersion++;
        
        // Параллельные задачи
        var coverTask = CoverFetcher.SaveCover(session);
        var durationTask = WaitForDuration(session);
        
        await Task.WhenAll(coverTask, durationTask);
        await SendToPythonServer();
    }
    
    private async Task SendToPythonServer()
    {
        var json = JsonSerializer.Serialize(currentState);
        var content = new StringContent(json, Encoding.UTF8, "application/json");
        await httpClient.PostAsync($"{pythonServerUrl}/update_from_cs", content);
    }
}
```

**Класс: CoverFetcher.cs**
```csharp
public static class CoverFetcher
{
    public static async Task SaveCover(session)
    {
        var thumbnail = await session.TryGetMediaPropertiesAsync()
                                     .Thumbnail;
        if (thumbnail != null) {
            using var stream = await thumbnail.OpenReadAsync();
            // Сохранение в songinfo/cover.png
        }
    }
}
```

### 4. Frontend Widgets (JavaScript)

**Файл: now_server/common.js**
```javascript
class NowPlayWidget {
    constructor() {
        this.ws = null;
        this.config = {};
        this.colorCache = new Map();
    }
    
    connect() {
        // Подключение к WebSocket
        this.ws = new WebSocket('ws://localhost:80/ws');
        
        this.ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            if (data.type === 'update') {
                this.updateUI(data.data);
            } else if (data.type === 'config_update') {
                this.updateConfig(data.data);
            }
        };
    }
    
    updateUI(data) {
        // Обновление текста (artist, title)
        // Обновление прогресс-бара (position/duration)
        // Загрузка обложки
        // Извлечение и применение цветов (если включено)
    }
    
    async extractColors(imageUrl) {
        // Проверка кэша
        if (this.colorCache.has(imageUrl)) {
            return this.colorCache.get(imageUrl);
        }
        
        // Загрузка изображения в canvas
        const canvas = document.createElement('canvas');
        canvas.width = 80;
        canvas.height = 80;
        const ctx = canvas.getContext('2d');
        
        const img = new Image();
        img.crossOrigin = 'anonymous';
        await new Promise((resolve) => {
            img.onload = resolve;
            img.src = imageUrl;
        });
        
        ctx.drawImage(img, 0, 0, 80, 80);
        
        // Выборка пикселей с шагом 128 байт
        const imageData = ctx.getImageData(0, 0, 80, 80);
        const pixels = imageData.data;
        const colors = [];
        
        for (let i = 0; i < pixels.length; i += 128) {
            const r = pixels[i];
            const g = pixels[i + 1];
            const b = pixels[i + 2];
            colors.push({r, g, b});
        }
        
        // Группировка и фильтрация цветов
        const dominantColors = this.findDominantColors(colors);
        
        // Кэширование результата
        this.colorCache.set(imageUrl, dominantColors);
        
        return dominantColors;
    }
    
    findDominantColors(colors) {
        // Фильтрация серых и темных цветов
        const filtered = colors.filter(c => {
            const brightness = (c.r + c.g + c.b) / 3;
            const saturation = Math.max(c.r, c.g, c.b) - Math.min(c.r, c.g, c.b);
            return brightness > 50 && saturation > 30;
        });
        
        // Группировка похожих цветов
        // Выбор наиболее частых
        // Возврат контрастных цветов
    }
}
```

## Data Models

### CurrentMediaState (C#)
```csharp
public class CurrentMediaState
{
    public string Artist { get; set; }
    public string Title { get; set; }
    public double Position { get; set; }  // секунды
    public double Duration { get; set; }  // секунды
    public bool IsPlaying { get; set; }
    public int CoverVersion { get; set; }
    public string Status { get; set; }  // "active" | "inactive"
}
```

### Configuration (JSON)
```json
{
    "bg_color": "rgba(30, 30, 30, 1)",
    "accent_color": "#1db954",
    "main_color": "rgba(30, 30, 30, 1)",
    "wave_color": "#1db954",
    "text_color": "#ffffff",
    "progress_color": "#1db954",
    "wave_enabled": true,
    "ambient_light_enabled": true,
    "auto_colors": false,
    "align_items": "flex-end",
    "justify_content": "flex-end",
    "position": "Справа-снизу",
    "selected_template": "visualisation.html",
    "use_builtin_monitor": false,
    "selected_media_source": null
}
```

### WebSocket Message (JSON)
```json
{
    "type": "update" | "init" | "config_update",
    "data": {
        "artist": "string",
        "title": "string",
        "position": 0.0,
        "duration": 0.0,
        "is_playing": true,
        "cover_url": "/cover?v=1",
        "status": "active" | "inactive",
        "config": { /* конфигурация */ }
    }
}
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Важное замечание о тестируемости

После анализа всех acceptance criteria из requirements.md, было установлено, что все 140 критериев относятся к **содержанию документации** (ТЗ и ВКР), а не к функциональным требованиям программной системы NowPlay. 

Критерии описывают, что должно быть **написано** в документе (например, "система SHALL указать требование...", "система SHALL включить описание..."), а не как должна **работать** программа.

Поэтому традиционные correctness properties для автоматизированного тестирования кода (property-based testing) здесь не применимы. Вместо этого, мы определяем **свойства полноты и корректности документации**, которые могут быть проверены через review процесс.

### Свойства полноты документации

**Property 1: Структурная полнота ТЗ**
*Для любого* создаваемого технического задания, документ должен содержать все 9 обязательных разделов согласно ГОСТ 19.201-78: Введение, Основания для разработки, Назначение разработки, Требования к программе, Требования к документированию, Технико-экономические показатели, Стадии и этапы разработки, Порядок контроля и приёмки, Приложения.
**Validates: Requirements 1.1-1.7, 2.1-2.7, 3.1-3.7, 12.1-12.7, 13.1-13.7, 14.1-14.7, 15.1-15.8, 16.1-16.7**

**Property 2: Полнота функциональных требований**
*Для любого* раздела "Требования к программе", должны быть описаны все 9 подразделов: функциональные характеристики, надёжность, производительность, технические средства, совместимость, эргономика, эксплуатация, защита информации, с конкретными измеримыми критериями для каждого.
**Validates: Requirements 4.1-4.9, 5.1-5.7, 6.1-6.7, 7.1-7.7, 8.1-8.7, 9.1-9.7, 10.1-10.7, 11.1-11.7**

**Property 3: Соответствие ГОСТ стандартам**
*Для любого* создаваемого ТЗ, оформление документа должно соответствовать требованиям ГОСТ 19.201-78 и ГОСТ 34.602-89: структура разделов, нумерация, терминология, формат представления требований.
**Validates: Requirements 2.1, 20.5-20.7**

**Property 4: Полнота описания архитектуры**
*Для любого* раздела описания архитектуры в ВКР, должны быть представлены: общая схема системы, диаграммы компонентов, диаграммы взаимодействия, описание интерфейсов, протоколов обмена данными.
**Validates: Requirements 17.1-17.7, 18.1-18.7**

**Property 5: Наличие количественных метрик**
*Для любого* требования к производительности или результата оптимизации, должны быть указаны конкретные измеримые значения (например, "CPU < 2%", "время отклика < 2с", "память < 200 МБ").
**Validates: Requirements 6.1-6.7, 19.1-19.7**

**Property 6: Полнота сравнительного анализа**
*Для любого* обзора аналогов, должно быть проанализировано минимум 5 существующих решений с таблицей сравнения по критериям: функциональность, производительность, стоимость, кроссплатформенность.
**Validates: Requirements 17.2-17.3, 13.4**

**Property 7: Полнота описания алгоритмов**
*Для любого* ключевого алгоритма системы (извлечение цветов, получение обложек, мониторинг медиа), должно быть представлено: пошаговое описание, псевдокод или блок-схема, оценка сложности, обоснование выбора.
**Validates: Requirements 18.1-18.7**

**Property 8: Полнота результатов тестирования**
*Для любого* раздела с результатами испытаний, должны быть представлены: методология тестирования, тестовое окружение, конкретные метрики (до и после оптимизации), графики, статистический анализ, выводы.
**Validates: Requirements 15.1-15.8, 19.1-19.7**

**Property 9: Наличие визуальных материалов**
*Для любого* раздела описания интерфейса или результатов, должны быть включены визуальные материалы: скриншоты всех экранов приложения, диаграммы архитектуры, графики производительности, таблицы сравнения.
**Validates: Requirements 16.1, 16.4, 16.7, 19.5**

**Property 10: Полнота библиографии**
*Для любой* выпускной квалификационной работы, список литературы должен содержать минимум 20 источников, оформленных по ГОСТ 7.0.5-2008, включая: научные статьи, техническую документацию, книги, онлайн-ресурсы.
**Validates: Requirements 20.7**

### Процесс верификации документации

Поскольку correctness properties относятся к содержанию документации, их верификация выполняется через:

1. **Peer Review**: Проверка коллегами или научным руководителем
2. **Checklist Verification**: Использование чек-листов для проверки наличия всех обязательных разделов
3. **ГОСТ Compliance Check**: Проверка соответствия стандартам оформления
4. **Completeness Metrics**: Подсчет количества разделов, источников, диаграмм, таблиц
5. **Content Quality Review**: Оценка глубины анализа, обоснованности выводов, корректности данных

## Error Handling

### Обработка ошибок в процессе создания документации

**1. Отсутствие обязательных разделов**
- Проверка: Сравнение структуры документа с требованиями ГОСТ
- Действие: Добавление недостающих разделов с placeholder текстом
- Уведомление: Список отсутствующих разделов

**2. Несоответствие формату ГОСТ**
- Проверка: Валидация оформления (шрифты, отступы, нумерация)
- Действие: Автоматическое исправление форматирования (если возможно)
- Уведомление: Список несоответствий с рекомендациями по исправлению

**3. Недостаточная детализация требований**
- Проверка: Анализ наличия конкретных метрик и критериев
- Действие: Выделение требований без количественных показателей
- Уведомление: Рекомендации по добавлению измеримых критериев

**4. Отсутствие визуальных материалов**
- Проверка: Подсчет количества рисунков, таблиц, диаграмм
- Действие: Указание мест, где необходимы визуальные материалы
- Уведомление: Список рекомендуемых диаграмм и скриншотов

**5. Неполная библиография**
- Проверка: Подсчет количества источников и проверка оформления
- Действие: Выделение некорректно оформленных источников
- Уведомление: Требование добавить источники до минимального количества (20)

**6. Несоответствие содержания и структуры**
- Проверка: Сравнение оглавления с фактическим содержанием
- Действие: Обновление оглавления или добавление недостающих подразделов
- Уведомление: Список расхождений между оглавлением и содержанием

## Testing Strategy

### Подход к тестированию документации

Поскольку данный spec описывает создание документации (ТЗ и ВКР), а не программного кода, традиционные unit tests и property-based tests не применимы. Вместо этого используется следующая стратегия:

**1. Checklist-Based Verification**
- Создание детального чек-листа на основе requirements.md
- Проверка наличия каждого обязательного раздела
- Проверка наличия всех обязательных элементов (диаграммы, таблицы, графики)
- Проверка соответствия количественным требованиям (минимум 20 источников, 5-7 аналогов)

**2. ГОСТ Compliance Testing**
- Проверка структуры документа согласно ГОСТ 19.201-78 и ГОСТ 34.602-89
- Проверка оформления (шрифты, отступы, нумерация страниц)
- Проверка оформления библиографии согласно ГОСТ 7.0.5-2008
- Проверка оформления рисунков и таблиц

**3. Content Completeness Testing**
- Проверка наличия всех 9 разделов ТЗ
- Проверка наличия всех подразделов раздела 4 (Требования к программе)
- Проверка наличия дополнительных разделов для ВКР
- Проверка наличия приложений

**4. Quality Metrics**
- Количество страниц (целевое: 60-80 для ВКР)
- Количество источников (минимум: 20)
- Количество диаграмм (минимум: 5-7)
- Количество таблиц (минимум: 3-5)
- Количество скриншотов (минимум: 10)

**5. Peer Review Process**
- Проверка научным руководителем
- Проверка коллегами
- Проверка на соответствие требованиям учебного заведения
- Проверка на наличие плагиата

**6. Iterative Refinement**
- Первая итерация: Создание структуры и основного содержания
- Вторая итерация: Добавление деталей, диаграмм, таблиц
- Третья итерация: Оформление согласно ГОСТ, добавление библиографии
- Четвертая итерация: Финальная вычитка и исправление замечаний

### Критерии приемки документации

Документация считается завершенной, если:
- ✅ Присутствуют все обязательные разделы согласно ГОСТ
- ✅ Оформление соответствует требованиям ГОСТ
- ✅ Количество источников ≥ 20
- ✅ Количество проанализированных аналогов ≥ 5
- ✅ Присутствуют все обязательные диаграммы и таблицы
- ✅ Все требования содержат конкретные измеримые критерии
- ✅ Результаты тестирования подтверждены метриками
- ✅ Документ прошел peer review без критических замечаний
- ✅ Объем документа соответствует требованиям (60-80 страниц для ВКР)
- ✅ Презентация для защиты содержит 15-20 слайдов

