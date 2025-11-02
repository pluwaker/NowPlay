// ============================================
// Общие функции для всех шаблонов визуализации
// ============================================

// Глобальные переменные (должны быть определены в каждом HTML файле)
// Доступ через window.visualizer и window.currentConfig

// ============================================
// Функции визуализатора
// ============================================

/**
 * Создаёт 14 полосок визуализатора с хаотичными параметрами анимации
 */
function createVisualizer() {
    // Проверяем, есть ли элемент визуализатора
    if (!window.visualizer) {
        // Пытаемся найти элемент напрямую, если window.visualizer еще не установлен
        const visualizerEl = document.getElementById('visualizer');
        if (visualizerEl) {
            window.visualizer = visualizerEl;
        } else {
            console.error('visualizer element not found');
            return;
        }
    }
    
    window.visualizer.innerHTML = '';
    for (let i = 0; i < 14; i++) {
        const bar = document.createElement('div');
        bar.className = 'visualizer-bar';
        
        // Случайная задержка от 0 до 2 секунд для хаотичности
        const randomDelay = Math.random() * 2;
        // Случайная длительность от 0.8 до 2 секунд для разной скорости
        const randomDuration = 0.8 + Math.random() * 1.2;
        
        // Случайные максимальные высоты для каждой точки анимации (0.3 - 1.0)
        const max1 = 0.3 + Math.random() * 0.7;
        const max2 = 0.3 + Math.random() * 0.7;
        const max3 = 0.3 + Math.random() * 0.7;
        const max4 = 0.3 + Math.random() * 0.7;
        
        // Случайная прозрачность для каждой точки
        const opacity1 = 0.5 + Math.random() * 0.5;
        const opacity2 = 0.4 + Math.random() * 0.4;
        const opacity3 = 0.6 + Math.random() * 0.4;
        const opacity4 = 0.5 + Math.random() * 0.3;
        
        bar.style.animationDelay = `${randomDelay.toFixed(2)}s`;
        bar.style.animationDuration = `${randomDuration.toFixed(2)}s`;
        bar.style.setProperty('--bar-max-1', max1.toFixed(3));
        bar.style.setProperty('--bar-max-2', max2.toFixed(3));
        bar.style.setProperty('--bar-max-3', max3.toFixed(3));
        bar.style.setProperty('--bar-max-4', max4.toFixed(3));
        bar.style.setProperty('--bar-opacity-1', opacity1.toFixed(2));
        bar.style.setProperty('--bar-opacity-2', opacity2.toFixed(2));
        bar.style.setProperty('--bar-opacity-3', opacity3.toFixed(2));
        bar.style.setProperty('--bar-opacity-4', opacity4.toFixed(2));
        
        window.visualizer.appendChild(bar);
    }
}

/**
 * Запуск/остановка CSS анимации визуализатора (0% CPU нагрузка!)
 */
function animateVisualizer() {
    // Пытаемся найти элемент напрямую, если window.visualizer еще не установлен
    if (!window.visualizer) {
        const visualizerEl = document.getElementById('visualizer');
        if (visualizerEl) {
            window.visualizer = visualizerEl;
        } else {
            console.warn('visualizer element not found in animateVisualizer');
            return;
        }
    }
    
    // Проверяем currentConfig с fallback на true по умолчанию (визуализатор включен, если не выключен явно)
    if (!window.currentConfig || window.currentConfig.wave_enabled !== false) {
        window.visualizer.classList.add('enabled');
    } else {
        stopVisualizer();
    }
}

/**
 * Остановка анимации (CSS анимация управляется через класс)
 */
function stopVisualizer() {
    if (!window.visualizer) {
        // Пытаемся найти элемент напрямую
        const visualizerEl = document.getElementById('visualizer');
        if (visualizerEl) {
            window.visualizer = visualizerEl;
        } else {
            return;
        }
    }
    window.visualizer.classList.remove('enabled');
}

// ============================================
// Утилиты для работы с цветами
// ============================================

function parseColor(colorStr) {
    if (colorStr.startsWith('rgba')) {
        const match = colorStr.match(/rgba?\((\d+),\s*(\d+),\s*(\d+)/);
        if (match) {
            return { r: parseInt(match[1]), g: parseInt(match[2]), b: parseInt(match[3]) };
        }
    } else if (colorStr.startsWith('#')) {
        const hex = colorStr.slice(1);
        return {
            r: parseInt(hex.slice(0, 2), 16),
            g: parseInt(hex.slice(2, 4), 16),
            b: parseInt(hex.slice(4, 6), 16)
        };
    }
    return { r: 0, g: 0, b: 0 };
}

function getHue(r, g, b) {
    r /= 255;
    g /= 255;
    b /= 255;
    const max = Math.max(r, g, b);
    const min = Math.min(r, g, b);
    let h = 0;
    
    if (max !== min) {
        const delta = max - min;
        if (max === r) {
            h = ((g - b) / delta) % 6;
        } else if (max === g) {
            h = (b - r) / delta + 2;
        } else {
            h = (r - g) / delta + 4;
        }
    }
    h = Math.round(h * 60);
    return h < 0 ? h + 360 : h;
}

function isColorGray(r, g, b, threshold = 30) {
    const max = Math.max(r, g, b);
    const min = Math.min(r, g, b);
    return (max - min) < threshold;
}

function isRedOrPink(hue) {
    return (hue >= 0 && hue <= 50) || (hue >= 320 && hue <= 360);
}

function colorDistance(c1, c2) {
    const dr = c1.r - c2.r;
    const dg = c1.g - c2.g;
    const db = c1.b - c2.b;
    return Math.sqrt(dr * dr + dg * dg + db * db);
}

function lightenColor(colorStr, amount = 50) {
    const rgb = parseColor(colorStr);
    return `rgb(${Math.min(255, rgb.r + amount)}, ${Math.min(255, rgb.g + amount)}, ${Math.min(255, rgb.b + amount)})`;
}

function darkenColor(colorStr, amount = 50) {
    const rgb = parseColor(colorStr);
    return `rgb(${Math.max(0, rgb.r - amount)}, ${Math.max(0, rgb.g - amount)}, ${Math.max(0, rgb.b - amount)})`;
}

function desaturateColor(colorStr, factor = 0.5) {
    const rgb = parseColor(colorStr);
    const gray = Math.round(rgb.r * 0.299 + rgb.g * 0.587 + rgb.b * 0.114);
    const r = Math.round(rgb.r + (gray - rgb.r) * factor);
    const g = Math.round(rgb.g + (gray - rgb.g) * factor);
    const b = Math.round(rgb.b + (gray - rgb.b) * factor);
    return `rgb(${r}, ${g}, ${b})`;
}

function ensureLightColor(colorStr, minLuminance = 180) {
    const rgb = parseColor(colorStr);
    let luminance = 0.299 * rgb.r + 0.587 * rgb.g + 0.114 * rgb.b;
    
    if (luminance < minLuminance) {
        const factor = minLuminance / luminance;
        rgb.r = Math.min(255, Math.round(rgb.r * factor));
        rgb.g = Math.min(255, Math.round(rgb.g * factor));
        rgb.b = Math.min(255, Math.round(rgb.b * factor));
    }
    
    return `rgb(${rgb.r}, ${rgb.g}, ${rgb.b})`;
}

// ============================================
// Функции работы с временем и прогрессом
// ============================================

function formatTime(seconds) {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
}

// ============================================
// Функции работы с текстом
// ============================================

function checkTextOverflow(element, container) {
    if (!element || !container) return false;
    
    const isOverflowing = element.scrollWidth > container.clientWidth;

    if (isOverflowing) {
        element.classList.add('marquee');
        container.classList.add('marquee-active');
        element.style.transform = '';
        element.style.paddingLeft = '100%';
        element.style.animation = 'marquee 15s linear infinite';
    } else {
        element.classList.remove('marquee');
        container.classList.remove('marquee-active');
        element.style.animation = '';
        element.style.paddingLeft = '';
        element.style.transform = '';
    }

    return isOverflowing;
}

