# Design Document

## Overview

Данный документ описывает дизайн решения для рефакторинга HTML файлов визуализации медиа-плеера. Решение предполагает извлечение дублирующихся JavaScript функций в общий модуль `common.js`, который будет подключаться ко всем HTML файлам.

## Architecture

### High-Level Architecture

```
now_server/
├── common.js (NEW)           # Общий модуль с переиспользуемыми функциями
├── visualisation.html        # Использует common.js
├── visualisation_horizontal.html  # Использует common.js
├── visualisation_var2.html   # Использует common.js
├── visualisation_var3.html   # Использует common.js
└── visualisation_var3_horizontal.html  # Использует common.js
```

### Module Structure

Файл `common.js` будет организован в следующие секции:

1. **Performance Monitoring** - функции для мониторинга производительности
2. **Color Extraction** - функции для извлечения цветов из изображений
3. **Color Manipulation** - функции для манипуляции цветами
4. **Color Utilities** - вспомогательные функции для работы с цветами
5. **Progress Management** - функции для управления прогресс-баром
6. **Visualizer Management** - функции для управления визуализатором
7. **UI Updates** - функции для обновления UI элементов

## Components and Interfaces

### 1. Performance Monitoring Functions

```javascript
/**
 * Логирование производительности операции
 * @param {string} operation - Название операции
 * @param {number} duration - Длительность в миллисекундах
 */
function logPerformance(operation, duration)
```

### 2. Color Extraction Functions

```javascript
/**
 * Извлечение цвета из конкретной точки изображения
 * @param {ImageData} imageData - Данные изображения
 * @param {number} x - X координата
 * @param {number} y - Y координата
 * @param {number} width - Ширина изображения
 * @returns {Object} Объект с r, g, b, a компонентами
 */
function getColorAtPoint(imageData, x, y, width)

/**
 * Извлечение цветов с краев изображения для ambient light
 * @param {HTMLImageElement} image - Элемент изображения
 * @param {string|null} trackTitle - Название трека (для кеширования)
 * @param {string|null} trackArtist - Исполнитель (для кеширования)
 * @returns {Promise<Object>} Объект с цветами для каждой стороны
 */
function getEdgeColors(image, trackTitle = null, trackArtist = null)

/**
 * Получение доминирующих цветов из изображения
 * @param {HTMLImageElement} image - Элемент изображения
 * @param {string|null} trackTitle - Название трека (для кеширования)
 * @param {string|null} trackArtist - Исполнитель (для кеширования)
 * @returns {Promise<Object>} Объект с first и second цветами
 */
function getDominantColors(image, trackTitle = null, trackArtist = null)

/**
 * Получение доминирующего цвета (для обратной совместимости)
 * @param {HTMLImageElement} image - Элемент изображения
 * @returns {Promise<string>} Доминирующий цвет в формате rgba
 */
function getDominantColor(image)
```

### 3. Color Manipulation Functions

```javascript
/**
 * Осветление цвета
 * @param {string} color - Цвет в формате rgba или hex
 * @param {number} amount - Величина осветления (по умолчанию 30)
 * @returns {string} Осветленный цвет в формате rgba
 */
function lightenColor(color, amount = 30)

/**
 * Затемнение цвета
 * @param {string} color - Цвет в формате rgba или hex
 * @param {number} amount - Величина затемнения (по умолчанию 30)
 * @returns {string} Затемненный цвет в формате rgba
 */
function darkenColor(color, amount = 30)

/**
 * Снижение насыщенности цвета
 * @param {string} color - Цвет в формате rgba или hex
 * @param {number} factor - Фактор десатурации (0.0 - 1.0)
 * @returns {string} Десатурированный цвет в формате rgba
 */
function desaturateColor(color, factor = 0.5)

/**
 * Обеспечение светлого цвета
 * @param {string} color - Цвет в формате rgba или hex
 * @param {number} minLuminance - Минимальная яркость (по умолчанию 180)
 * @returns {string} Светлый цвет в формате rgba
 */
function ensureLightColor(color, minLuminance = 180)
```

### 4. Color Utility Functions

```javascript
/**
 * Проверка, является ли цвет темным
 * @param {string} color - Цвет в формате rgba или hex
 * @param {number} threshold - Порог яркости (по умолчанию 128)
 * @returns {boolean} true если цвет темный
 */
function isColorDark(color, threshold = 128)

/**
 * Проверка, является ли цвет серым
 * @param {number} r - Красный компонент
 * @param {number} g - Зеленый компонент
 * @param {number} b - Синий компонент
 * @param {number} threshold - Порог различия (по умолчанию 30)
 * @returns {boolean} true если цвет серый
 */
function isColorGray(r, g, b, threshold = 30)

/**
 * Проверка, является ли цвет красным или розовым
 * @param {number} hue - Оттенок в градусах (0-360)
 * @returns {boolean} true если цвет красный или розовый
 */
function isRedOrPink(hue)

/**
 * Вычисление оттенка (hue) в градусах
 * @param {number} r - Красный компонент
 * @param {number} g - Зеленый компонент
 * @param {number} b - Синий компонент
 * @returns {number} Оттенок в градусах (0-360)
 */
function getHue(r, g, b)

/**
 * Вычисление цветового расстояния между двумя цветами
 * @param {Object|string} color1 - Первый цвет
 * @param {Object|string} color2 - Второй цвет
 * @returns {number} Расстояние между цветами
 */
function colorDistance(color1, color2)

/**
 * Конвертация hex в rgba
 * @param {string} hex - Цвет в формате hex
 * @param {number} alpha - Прозрачность (по умолчанию 0.5)
 * @returns {string} Цвет в формате rgba
 */
function hexToRgba(hex, alpha = 0.5)

/**
 * Парсинг цвета в RGB объект
 * @param {string} color - Цвет в формате rgba или hex
 * @returns {Object} Объект с r, g, b компонентами
 */
function parseColor(color)
```

### 5. Progress Management Functions

```javascript
/**
 * Форматирование времени в формат MM:SS
 * @param {number} seconds - Время в секундах
 * @returns {string} Отформатированное время
 */
function formatTime(seconds)

/**
 * Обновление прогресс-бара
 * @param {number} currentPosition - Текущая позиция в секундах
 * @param {number} totalDuration - Общая длительность в секундах
 * @param {HTMLElement} progress - Элемент прогресс-бара
 * @param {HTMLElement} currentTimeEl - Элемент текущего времени
 * @param {HTMLElement} durationEl - Элемент общей длительности
 */
function updateProgress(currentPosition, totalDuration, progress, currentTimeEl, durationEl)

/**
 * Запуск обновления прогресса в реальном времени
 * @param {Object} state - Объект состояния с currentPosition, totalDuration, isPlaying
 * @param {Function} updateCallback - Callback для обновления UI
 * @returns {number} ID интервала
 */
function startProgressUpdate(state, updateCallback)

/**
 * Остановка обновления прогресса
 * @param {number} intervalId - ID интервала
 */
function stopProgressUpdate(intervalId)
```

### 6. Visualizer Management Functions

```javascript
/**
 * Создание визуализатора с хаотичными параметрами анимации
 * @param {HTMLElement} visualizer - Контейнер визуализатора
 * @param {number} barCount - Количество полосок (по умолчанию 14)
 */
function createVisualizer(visualizer, barCount = 14)

/**
 * Запуск анимации визуализатора
 * @param {HTMLElement} visualizer - Контейнер визуализатора
 * @param {Object} config - Конфигурация с wave_enabled
 */
function animateVisualizer(visualizer, config)

/**
 * Остановка анимации визуализатора с плавным исчезновением
 * @param {HTMLElement} visualizer - Контейнер визуализатора
 */
function stopVisualizer(visualizer)
```

### 7. UI Update Functions

```javascript
/**
 * Плавный переход между двумя цветами для ambient light
 * @param {string} fromColor - Начальный цвет
 * @param {string} toColor - Конечный цвет
 * @param {HTMLElement} ambientLight - Элемент ambient light
 * @param {number} duration - Длительность перехода в мс (по умолчанию 800)
 * @returns {Object} Объект анимации с методом cancel()
 */
function transitionAmbientLight(fromColor, toColor, ambientLight, duration = 800)

/**
 * Обновление ambient light с градиентами по краям
 * @param {Object} edgeColors - Объект с цветами для каждой стороны
 * @param {HTMLElement} ambientLight - Элемент ambient light
 * @param {Object} config - Конфигурация с ambient_light_enabled
 * @param {boolean} useTransition - Использовать плавный переход
 */
function updateAmbientLight(edgeColors, ambientLight, config, useTransition = true)

/**
 * Применение автоматических цветов из изображения
 * @param {Object} colors - Объект с first и second цветами
 * @param {Object} edgeColors - Объект с цветами краев
 * @param {Object} config - Конфигурация
 */
function applyAutoColors(colors, edgeColors, config)
```

## Data Models

### Color Cache Structure

```javascript
{
  // Кеш для результатов извлечения цветов
  colorCache: Map<string, Object>,
  
  // Статистика производительности
  performanceStats: {
    colorExtractions: number,
    totalTime: number,
    maxTime: number,
    minTime: number,
    cacheHits: number
  }
}
```

### Edge Colors Structure

```javascript
{
  top: [string, string, string],    // 3 цвета для верхней стороны
  right: [string, string, string],  // 3 цвета для правой стороны
  bottom: [string, string, string], // 3 цвета для нижней стороны
  left: [string, string, string]    // 3 цвета для левой стороны
}
```

### Dominant Colors Structure

```javascript
{
  first: string,   // Первый доминирующий цвет в формате rgba
  second: string   // Второй доминирующий цвет в формате rgba
}
```

## Error Handling

1. **Image Loading Errors**: Функции извлечения цветов должны проверять, что изображение загружено и имеет ненулевые размеры
2. **Color Parsing Errors**: Функции парсинга цветов должны обрабатывать некорректные форматы и возвращать значения по умолчанию
3. **Cache Overflow**: Кеш должен автоматически очищать старые записи при достижении лимита (50 записей)
4. **Animation Cancellation**: Анимации должны корректно отменяться при запуске новых анимаций

## Testing Strategy

### Unit Tests (Optional)

1. **Color Extraction Tests**
   - Тест извлечения цветов из валидного изображения
   - Тест обработки невалидного изображения
   - Тест кеширования результатов

2. **Color Manipulation Tests**
   - Тест осветления/затемнения цветов
   - Тест десатурации цветов
   - Тест парсинга различных форматов цветов

3. **Progress Tests**
   - Тест форматирования времени
   - Тест обновления прогресс-бара

### Integration Tests

1. **HTML File Tests**
   - Проверка, что все HTML файлы корректно загружают common.js
   - Проверка, что все функции доступны в глобальной области видимости
   - Проверка, что визуальное поведение не изменилось

### Manual Testing

1. Открыть каждый HTML файл в браузере
2. Проверить, что визуализация работает корректно
3. Проверить, что ambient light обновляется при смене трека
4. Проверить, что прогресс-бар работает корректно
5. Проверить, что визуализатор анимируется корректно

## Implementation Notes

1. **Global Variables**: Некоторые функции используют глобальные переменные (colorCache, performanceStats). Эти переменные должны быть объявлены в common.js и доступны всем HTML файлам
2. **Backward Compatibility**: Функция `getDominantColor()` сохранена для обратной совместимости, хотя рекомендуется использовать `getDominantColors()`
3. **Performance**: Кеширование результатов извлечения цветов критично для производительности. Кеш должен использовать полный URL изображения с параметрами версионирования
4. **CSS Animations**: Визуализатор использует CSS анимации вместо JavaScript для минимизации нагрузки на CPU
