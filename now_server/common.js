/**
 * Common JavaScript Module for Media Player Visualizations
 * Contains shared functions used across all visualization HTML files
 */

// ============================================================================
// PERFORMANCE MONITORING
// ============================================================================

/**
 * Глобальный кеш для результатов извлечения цветов
 * @type {Map<string, Object>}
 */
window.colorCache = new Map();

/**
 * Статистика производительности
 * @type {Object}
 */
window.performanceStats = {
    colorExtractions: 0,
    totalTime: 0,
    maxTime: 0,
    minTime: Infinity,
    cacheHits: 0
};

/**
 * Логирование производительности операции
 * @param {string} operation - Название операции
 * @param {number} duration - Длительность в миллисекундах
 */
function logPerformance(operation, duration) {
    if (window.DEBUG_PERFORMANCE) {
        console.log(`[PERF] ${operation}: ${duration.toFixed(2)}ms`);
    }
}

// ============================================================================
// COLOR EXTRACTION
// ============================================================================

/**
 * Извлечение цвета из конкретной точки изображения
 * @param {ImageData} imageData - Данные изображения
 * @param {number} x - X координата
 * @param {number} y - Y координата
 * @param {number} width - Ширина изображения
 * @returns {Object} Объект с r, g, b, a компонентами
 */
function getColorAtPoint(imageData, x, y, width) {
    const index = (y * width + x) * 4;
    return {
        r: imageData.data[index],
        g: imageData.data[index + 1],
        b: imageData.data[index + 2],
        a: imageData.data[index + 3]
    };
}

/**
 * Извлечение цветов с краев изображения для ambient light
 * @param {HTMLImageElement} image - Элемент изображения
 * @param {string|null} trackTitle - Название трека (для кеширования)
 * @param {string|null} trackArtist - Исполнитель (для кеширования)
 * @returns {Promise<Object>} Объект с цветами для каждой стороны
 */
function getEdgeColors(image, trackTitle = null, trackArtist = null) {
    return new Promise((resolve, reject) => {
        const startTime = performance.now();
        
        try {
            if (!image || !image.complete || image.naturalWidth === 0) {
                reject(new Error('Изображение не загружено'));
                return;
            }

            const fullUrl = image.src;
            const cacheKey = trackTitle && trackArtist 
                ? `edges_${fullUrl}|${trackTitle}|${trackArtist}` 
                : `edges_${fullUrl}`;
            
            if (window.colorCache.has(cacheKey)) {
                window.performanceStats.cacheHits++;
                const cachedResult = window.colorCache.get(cacheKey);
                logPerformance('getEdgeColors (CACHED)', performance.now() - startTime);
                resolve(cachedResult);
                return;
            }
            
            window.performanceStats.colorExtractions++;

            const canvas = document.createElement('canvas');
            const ctx = canvas.getContext('2d');
            const size = 100;
            canvas.width = size;
            canvas.height = size;
            
            ctx.drawImage(image, 0, 0, size, size);
            const imageData = ctx.getImageData(0, 0, size, size);
            
            const edges = {
                left: [
                    getColorAtPoint(imageData, 0, 0, size),
                    getColorAtPoint(imageData, 0, Math.floor(size / 2), size),
                    getColorAtPoint(imageData, 0, size - 1, size)
                ],
                bottom: [
                    getColorAtPoint(imageData, 0, size - 1, size),
                    getColorAtPoint(imageData, Math.floor(size / 2), size - 1, size),
                    getColorAtPoint(imageData, size - 1, size - 1, size)
                ],
                right: [
                    getColorAtPoint(imageData, size - 1, size - 1, size),
                    getColorAtPoint(imageData, size - 1, Math.floor(size / 2), size),
                    getColorAtPoint(imageData, size - 1, 0, size)
                ],
                top: [
                    getColorAtPoint(imageData, size - 1, 0, size),
                    getColorAtPoint(imageData, Math.floor(size / 2), 0, size),
                    getColorAtPoint(imageData, 0, 0, size)
                ]
            };
            
            const result = {
                top: edges.top.map(c => `rgba(${c.r}, ${c.g}, ${c.b}, 0.85)`),
                right: edges.right.map(c => `rgba(${c.r}, ${c.g}, ${c.b}, 0.85)`),
                bottom: edges.bottom.map(c => `rgba(${c.r}, ${c.g}, ${c.b}, 0.85)`),
                left: edges.left.map(c => `rgba(${c.r}, ${c.g}, ${c.b}, 0.85)`)
            };
            
            if (window.colorCache.size >= 50) {
                const firstKey = window.colorCache.keys().next().value;
                window.colorCache.delete(firstKey);
            }
            window.colorCache.set(cacheKey, result);
            
            const duration = performance.now() - startTime;
            window.performanceStats.totalTime += duration;
            window.performanceStats.maxTime = Math.max(window.performanceStats.maxTime, duration);
            window.performanceStats.minTime = Math.min(window.performanceStats.minTime, duration);
            
            logPerformance('getEdgeColors', duration);
            
            resolve(result);
        } catch (error) {
            console.error('Ошибка в getEdgeColors:', error);
            reject(error);
        }
    });
}

/**
 * Получение доминирующих цветов из изображения
 * @param {HTMLImageElement} image - Элемент изображения
 * @param {string|null} trackTitle - Название трека (для кеширования)
 * @param {string|null} trackArtist - Исполнитель (для кеширования)
 * @returns {Promise<Object>} Объект с first и second цветами
 */
function getDominantColors(image, trackTitle = null, trackArtist = null) {
    return new Promise((resolve, reject) => {
        const startTime = performance.now();
        
        try {
            if (!image || !image.complete || image.naturalWidth === 0) {
                reject(new Error('Изображение не загружено'));
                return;
            }

            const fullUrl = image.src;
            const cacheKey = trackTitle && trackArtist 
                ? `${fullUrl}|${trackTitle}|${trackArtist}` 
                : fullUrl;
            
            if (window.colorCache.has(cacheKey)) {
                window.performanceStats.cacheHits++;
                const cachedResult = window.colorCache.get(cacheKey);
                logPerformance('getDominantColors (CACHED)', performance.now() - startTime);
                resolve(cachedResult);
                return;
            }
            
            window.performanceStats.colorExtractions++;

            const canvas = document.createElement('canvas');
            const ctx = canvas.getContext('2d');
            const size = 80;
            canvas.width = size;
            canvas.height = size;
            
            ctx.drawImage(image, 0, 0, size, size);
            const imageData = ctx.getImageData(0, 0, size, size);
            const data = imageData.data;
            
            // Группируем похожие цвета для определения доминирующих
            const colorMap = new Map();
            
            // Берем каждый 8-й пиксель для оптимизации
            for (let i = 0; i < data.length; i += 32) {
                const alpha = data[i + 3];
                if (alpha > 10) {
                    const r = data[i];
                    const g = data[i + 1];
                    const b = data[i + 2];
                    
                    // Округляем цвета для группировки похожих оттенков
                    const roundedR = Math.round(r / 16) * 16;
                    const roundedG = Math.round(g / 16) * 16;
                    const roundedB = Math.round(b / 16) * 16;
                    const key = `${roundedR},${roundedG},${roundedB}`;
                    
                    if (!colorMap.has(key)) {
                        colorMap.set(key, { r: 0, g: 0, b: 0, count: 0 });
                    }
                    const color = colorMap.get(key);
                    color.r += r;
                    color.g += g;
                    color.b += b;
                    color.count++;
                }
            }
            
            if (colorMap.size === 0) {
                reject(new Error('Не удалось извлечь данные (нет видимых пикселей)'));
                return;
            }
            
            // Преобразуем карту в массив, вычисляем яркость, оттенок и фильтруем темные и серые цвета
            const colors = Array.from(colorMap.entries()).map(([key, value]) => {
                const r = Math.round(value.r / value.count);
                const g = Math.round(value.g / value.count);
                const b = Math.round(value.b / value.count);
                const luminance = (0.299 * r + 0.587 * g + 0.114 * b);
                const hue = getHue(r, g, b);
                return {
                    r, g, b,
                    count: value.count,
                    luminance: luminance,
                    hue: hue
                };
            });
            
            // Фильтруем серые цвета (разница между max и min каналами < 30)
            const nonGrayColors = colors.filter(c => !isColorGray(c.r, c.g, c.b, 30));
            
            // Используем несерые цвета, если их достаточно, иначе все
            const colorsToFilter = nonGrayColors.length >= 2 ? nonGrayColors : colors;
            
            // Фильтруем только светлые цвета (яркость >= 100) для акцентных цветов
            const lightColors = colorsToFilter.filter(c => c.luminance >= 100);
            
            // Если светлых цветов недостаточно, используем цвета с яркостью >= 70 (но не серые)
            let filteredColors = lightColors.length >= 2 ? lightColors : colorsToFilter.filter(c => c.luminance >= 70 && !isColorGray(c.r, c.g, c.b, 30));
            
            // Если все равно недостаточно, используем цвета с яркостью >= 50 (но не серые)
            if (filteredColors.length < 2) {
                filteredColors = colorsToFilter.filter(c => c.luminance >= 50 && !isColorGray(c.r, c.g, c.b, 30));
            }
            
            // Если и их мало, используем все не черные и не серые
            if (filteredColors.length < 2) {
                filteredColors = colorsToFilter.filter(c => c.luminance >= 30 && !isColorGray(c.r, c.g, c.b, 30));
            }
            
            // Если совсем нет подходящих, используем несерые цвета
            if (filteredColors.length === 0) {
                filteredColors = colorsToFilter.length > 0 ? colorsToFilter : colors;
            }
            
            // Сортируем по количеству пикселей (убывание)
            filteredColors.sort((a, b) => b.count - a.count);
            
            // Берем первый доминирующий СВЕТЛЫЙ цвет
            let firstColor = filteredColors[0];
            
            // Предпочитаем светлые цвета (яркость >= 100)
            const veryLightColors = filteredColors.filter(c => c.luminance >= 100);
            if (veryLightColors.length > 0) {
                firstColor = veryLightColors[0];
            }
            
            // Для второго цвета ищем СВЕТЛЫЙ цвет с ДРУГИМ оттенком
            let secondColor = filteredColors[1] || filteredColors[0];
            
            if (filteredColors.length > 1) {
                const firstHue = firstColor.hue;
                const minHueDifference = 30; // Минимальная разница в оттенке (градусы)
                const minContrast = 120; // Минимальное общее расстояние для хорошего контраста
                
                // Если первый цвет красный/розовый, второй должен быть из другой части спектра
                const isFirstRedPink = isRedOrPink(firstHue);
                
                // Ищем светлые цвета с другим оттенком
                // Если первый цвет красный/розовый, второй НЕ должен быть красным/розовым
                let lightColorsWithDifferentHue = filteredColors.filter(c => {
                    if (c === firstColor) return false;
                    
                    // СТРОГО запрещаем сочетание красного/розового с красным/розовым
                    if (isFirstRedPink && isRedOrPink(c.hue)) {
                        return false;
                    }
                    
                    // Если первый красный/розовый, второй должен быть из противоположной части спектра
                    if (isFirstRedPink) {
                        // Требуем минимум 90 градусов разницы для второго цвета
                        const hueDiff = Math.abs(c.hue - firstHue);
                        const actualHueDiff = hueDiff > 180 ? 360 - hueDiff : hueDiff;
                        if (actualHueDiff < 90) {
                            return false; // Слишком близко к красному/розовому
                        }
                    }
                    
                    const hueDiff = Math.abs(c.hue - firstHue);
                    const actualHueDiff = hueDiff > 180 ? 360 - hueDiff : hueDiff;
                    
                    return c.luminance >= 100 && actualHueDiff >= minHueDifference;
                });
                
                if (lightColorsWithDifferentHue.length > 0) {
                    // Выбираем наиболее контрастный из светлых цветов с другим оттенком
                    lightColorsWithDifferentHue.sort((a, b) => {
                        return colorDistance(firstColor, b) - colorDistance(firstColor, a);
                    });
                    secondColor = lightColorsWithDifferentHue[0];
                    console.log('Найден светлый цвет с другим оттенком:', { hue: secondColor.hue, firstHue: firstHue });
                } else {
                    // Если не нашли светлых с другим оттенком, ищем любой светлый цвет с хорошим контрастом
                    // СТРОГО запрещаем сочетание красного/розового с красным/розовым
                    const lightContrasting = filteredColors.filter(c => {
                        if (c === firstColor) return false;
                        
                        // СТРОГО запрещаем сочетание красного/розового с красным/розовым
                        if (isFirstRedPink && isRedOrPink(c.hue)) {
                            return false;
                        }
                        
                        // Если первый красный/розовый, второй должен быть из противоположной части спектра
                        if (isFirstRedPink) {
                            const hueDiff = Math.abs(c.hue - firstHue);
                            const actualHueDiff = hueDiff > 180 ? 360 - hueDiff : hueDiff;
                            if (actualHueDiff < 90) {
                                return false; // Слишком близко к красному/розовому
                            }
                        }
                        
                        const hueDiff = Math.abs(c.hue - firstHue);
                        const actualHueDiff = hueDiff > 180 ? 360 - hueDiff : hueDiff;
                        return c.luminance >= 100 && actualHueDiff >= 15 && colorDistance(firstColor, c) >= minContrast;
                    });
                    
                    if (lightContrasting.length > 0) {
                        lightContrasting.sort((a, b) => {
                            return colorDistance(firstColor, b) - colorDistance(firstColor, a);
                        });
                        secondColor = lightContrasting[0];
                        console.log('Найден светлый контрастный цвет');
                    } else {
                        // Ищем наиболее контрастный светлый цвет среди всех
                        // СТРОГО запрещаем сочетание красного/розового с красным/розовым
                        const allLight = filteredColors.filter(c => {
                            if (c.luminance < 100 || c === firstColor) return false;
                            // СТРОГО запрещаем сочетание красного/розового с красным/розовым
                            if (isFirstRedPink && isRedOrPink(c.hue)) {
                                return false;
                            }
                            // Если первый красный/розовый, второй должен быть из противоположной части спектра
                            if (isFirstRedPink) {
                                const hueDiff = Math.abs(c.hue - firstHue);
                                const actualHueDiff = hueDiff > 180 ? 360 - hueDiff : hueDiff;
                                if (actualHueDiff < 90) {
                                    return false; // Слишком близко к красному/розовому
                                }
                            }
                            return true;
                        });
                        if (allLight.length > 0) {
                            allLight.sort((a, b) => {
                                return colorDistance(firstColor, b) - colorDistance(firstColor, a);
                            });
                            secondColor = allLight[0];
                            console.log('Выбран наиболее контрастный светлый цвет');
                        } else {
                            // В крайнем случае ищем любой цвет с хорошим контрастом (но не красный/розовый если первый красный/розовый)
                            let bestContrast = 0;
                            let bestColor = filteredColors[1] || filteredColors[0];
                            
                            for (let i = 1; i < Math.min(filteredColors.length, 15); i++) {
                                const candidate = filteredColors[i];
                                
                                // СТРОГО запрещаем сочетание красного/розового с красным/розовым
                                if (isFirstRedPink && isRedOrPink(candidate.hue)) {
                                    continue;
                                }
                                
                                // Если первый красный/розовый, второй должен быть из противоположной части спектра
                                if (isFirstRedPink) {
                                    const hueDiff = Math.abs(candidate.hue - firstHue);
                                    const actualHueDiff = hueDiff > 180 ? 360 - hueDiff : hueDiff;
                                    if (actualHueDiff < 90) {
                                        continue; // Слишком близко к красному/розовому
                                    }
                                }
                                
                                const distance = colorDistance(firstColor, candidate);
                                
                                if (distance > bestContrast) {
                                    bestContrast = distance;
                                    bestColor = candidate;
                                }
                            }
                            
                            secondColor = bestColor;
                            console.log('Выбран наиболее контрастный цвет из доступных');
                        }
                    }
                }
                
                // Финальная проверка: убеждаемся, что цвета действительно разные
                const finalHueDiff = Math.abs(secondColor.hue - firstHue);
                const actualFinalHueDiff = finalHueDiff > 180 ? 360 - finalHueDiff : finalHueDiff;
                
                if (actualFinalHueDiff < 20 && filteredColors.length > 2) {
                    // Если оттенки слишком похожи, ищем цвет в другой части спектра
                    const oppositeHue = (firstHue + 180) % 360;
                    const colorsNearOpposite = filteredColors.filter(c => {
                        if (c === firstColor) return false;
                        
                        // СТРОГО запрещаем сочетание красного/розового с красным/розовым
                        if (isFirstRedPink && isRedOrPink(c.hue)) {
                            return false;
                        }
                        
                        // Если первый красный/розовый, второй должен быть из противоположной части спектра
                        if (isFirstRedPink) {
                            const hueDiff = Math.abs(c.hue - firstHue);
                            const actualHueDiff = hueDiff > 180 ? 360 - hueDiff : hueDiff;
                            if (actualHueDiff < 90) {
                                return false; // Слишком близко к красному/розовому
                            }
                        }
                        
                        const hueDiff = Math.abs(c.hue - oppositeHue);
                        const actualDiff = hueDiff > 180 ? 360 - hueDiff : hueDiff;
                        return actualDiff < 60 && c.luminance >= 70;
                    });
                    
                    if (colorsNearOpposite.length > 0) {
                        colorsNearOpposite.sort((a, b) => b.luminance - a.luminance);
                        secondColor = colorsNearOpposite[0];
                        console.log('Выбран цвет с противоположным оттенком для лучшего контраста');
                    }
                }
            }
            
            // Финальная проверка: запрещаем сочетание красного/розового с красным/розовым
            const isFirstRedPink = isRedOrPink(firstColor.hue);
            const isSecondRedPink = isRedOrPink(secondColor.hue);
            
            if (isFirstRedPink && isSecondRedPink) {
                // Если оба цвета красные/розовые, ищем альтернативный второй цвет
                const alternativeColors = filteredColors.filter(c => {
                    if (c === firstColor) return false;
                    return !isRedOrPink(c.hue);
                });
                
                if (alternativeColors.length > 0) {
                    // Выбираем наиболее контрастный из не красных/розовых
                    alternativeColors.sort((a, b) => {
                        return colorDistance(firstColor, b) - colorDistance(firstColor, a);
                    });
                    secondColor = alternativeColors[0];
                    console.log('Заменен второй цвет - запрещено сочетание красного/розового с красным/розовым');
                } else {
                    // Если нет альтернатив, выбираем цвет с максимальной разницей в оттенке
                    const nonRedPink = filteredColors.filter(c => {
                        if (c === firstColor) return false;
                        const hueDiff = Math.abs(c.hue - firstColor.hue);
                        const actualHueDiff = hueDiff > 180 ? 360 - hueDiff : hueDiff;
                        return actualHueDiff > 60; // Минимум 60 градусов разницы
                    });
                    
                    if (nonRedPink.length > 0) {
                        nonRedPink.sort((a, b) => {
                            return colorDistance(firstColor, b) - colorDistance(firstColor, a);
                        });
                        secondColor = nonRedPink[0];
                        console.log('Выбран цвет с максимальным отличием от красного/розового');
                    }
                }
            }
            
            const result = {
                first: `rgba(${firstColor.r}, ${firstColor.g}, ${firstColor.b}, 0.85)`,
                second: `rgba(${secondColor.r}, ${secondColor.g}, ${secondColor.b}, 0.85)`
            };
            
            if (window.colorCache.size >= 50) {
                const firstKey = window.colorCache.keys().next().value;
                window.colorCache.delete(firstKey);
            }
            window.colorCache.set(cacheKey, result);
            
            const duration = performance.now() - startTime;
            window.performanceStats.totalTime += duration;
            window.performanceStats.maxTime = Math.max(window.performanceStats.maxTime, duration);
            window.performanceStats.minTime = Math.min(window.performanceStats.minTime, duration);
            
            logPerformance('getDominantColors', duration);
            
            if (window.performanceStats.colorExtractions % 10 === 0) {
                const avgTime = window.performanceStats.totalTime / window.performanceStats.colorExtractions;
                console.log(`[PERF STATS] Извлечений: ${window.performanceStats.colorExtractions}, ` +
                          `Кеш попаданий: ${window.performanceStats.cacheHits}, ` +
                          `Среднее время: ${avgTime.toFixed(2)}ms, ` +
                          `Макс: ${window.performanceStats.maxTime.toFixed(2)}ms, ` +
                          `Мин: ${window.performanceStats.minTime.toFixed(2)}ms`);
            }
            
            resolve(result);
        } catch (error) {
            console.error('Ошибка в getDominantColors:', error);
            reject(error);
        }
    });
}

/**
 * Получение доминирующего цвета (для обратной совместимости)
 * @param {HTMLImageElement} image - Элемент изображения
 * @returns {Promise<string>} Доминирующий цвет в формате rgba
 */
function getDominantColor(image) {
    return getDominantColors(image).then(colors => colors.first);
}

// ============================================================================
// COLOR MANIPULATION
// ============================================================================

/**
 * Осветление цвета
 * @param {string} color - Цвет в формате rgba или hex
 * @param {number} amount - Величина осветления (по умолчанию 30)
 * @returns {string} Осветленный цвет в формате rgba
 */
function lightenColor(color, amount = 30) {
    const rgb = parseColor(color);
    const r = Math.min(255, rgb.r + amount);
    const g = Math.min(255, rgb.g + amount);
    const b = Math.min(255, rgb.b + amount);
    return `rgba(${r}, ${g}, ${b}, 0.85)`;
}

/**
 * Затемнение цвета
 * @param {string} color - Цвет в формате rgba или hex
 * @param {number} amount - Величина затемнения (по умолчанию 30)
 * @returns {string} Затемненный цвет в формате rgba
 */
function darkenColor(color, amount = 30) {
    const rgb = parseColor(color);
    const r = Math.max(0, rgb.r - amount);
    const g = Math.max(0, rgb.g - amount);
    const b = Math.max(0, rgb.b - amount);
    return `rgba(${r}, ${g}, ${b}, 1)`;
}

/**
 * Снижение насыщенности цвета
 * @param {string} color - Цвет в формате rgba или hex
 * @param {number} factor - Фактор десатурации (0.0 - 1.0)
 * @returns {string} Десатурированный цвет в формате rgba
 */
function desaturateColor(color, factor = 0.5) {
    const rgb = parseColor(color);
    // Вычисляем яркость для серого компонента
    const luminance = Math.round(0.299 * rgb.r + 0.587 * rgb.g + 0.114 * rgb.b);
    // Смешиваем исходный цвет с серым цветом той же яркости
    const r = Math.round(rgb.r * factor + luminance * (1 - factor));
    const g = Math.round(rgb.g * factor + luminance * (1 - factor));
    const b = Math.round(rgb.b * factor + luminance * (1 - factor));
    return `rgba(${r}, ${g}, ${b}, 1)`;
}

/**
 * Обеспечение светлого цвета
 * @param {string} color - Цвет в формате rgba или hex
 * @param {number} minLuminance - Минимальная яркость (по умолчанию 180)
 * @returns {string} Светлый цвет в формате rgba
 */
function ensureLightColor(color, minLuminance = 180) {
    const rgb = parseColor(color);
    const currentLuminance = (0.299 * rgb.r + 0.587 * rgb.g + 0.114 * rgb.b);
    
    if (currentLuminance < minLuminance) {
        // Если цвет темный, осветляем его до минимальной яркости
        const scale = minLuminance / (currentLuminance || 1);
        const r = Math.min(255, Math.round(rgb.r * scale));
        const g = Math.min(255, Math.round(rgb.g * scale));
        const b = Math.min(255, Math.round(rgb.b * scale));
        return `rgba(${r}, ${g}, ${b}, 0.85)`;
    }
    
    return color;
}

// ============================================================================
// COLOR UTILITIES
// ============================================================================

/**
 * Проверка, является ли цвет темным
 * @param {string} color - Цвет в формате rgba или hex
 * @param {number} threshold - Порог яркости (по умолчанию 128)
 * @returns {boolean} true если цвет темный
 */
function isColorDark(color, threshold = 128) {
    const rgb = parseColor(color);
    // Формула относительной яркости (luminance)
    const luminance = (0.299 * rgb.r + 0.587 * rgb.g + 0.114 * rgb.b);
    return luminance < threshold;
}

/**
 * Проверка, является ли цвет серым
 * @param {number} r - Красный компонент
 * @param {number} g - Зеленый компонент
 * @param {number} b - Синий компонент
 * @param {number} threshold - Порог различия (по умолчанию 30)
 * @returns {boolean} true если цвет серый
 */
function isColorGray(r, g, b, threshold = 30) {
    const max = Math.max(r, g, b);
    const min = Math.min(r, g, b);
    const delta = max - min;
    return delta < threshold;
}

/**
 * Проверка, является ли цвет красным или розовым
 * @param {number} hue - Оттенок в градусах (0-360)
 * @returns {boolean} true если цвет красный или розовый
 */
function isRedOrPink(hue) {
    // Красный: 0° - 50° и 320° - 360°
    // Розовый: 280° - 320°
    // Итого: 280° - 50° (включая переход через 360°) - расширенный диапазон
    return (hue >= 280 && hue <= 360) || (hue >= 0 && hue <= 50);
}

/**
 * Вычисление оттенка (hue) в градусах
 * @param {number} r - Красный компонент
 * @param {number} g - Зеленый компонент
 * @param {number} b - Синий компонент
 * @returns {number} Оттенок в градусах (0-360)
 */
function getHue(r, g, b) {
    const max = Math.max(r, g, b);
    const min = Math.min(r, g, b);
    const delta = max - min;
    
    if (delta === 0) return 0; // Серый цвет
    
    let hue = 0;
    if (max === r) {
        hue = ((g - b) / delta) % 6;
    } else if (max === g) {
        hue = (b - r) / delta + 2;
    } else {
        hue = (r - g) / delta + 4;
    }
    
    hue = Math.round(hue * 60);
    if (hue < 0) hue += 360;
    return hue;
}

/**
 * Вычисление цветового расстояния между двумя цветами
 * @param {Object|string} color1 - Первый цвет
 * @param {Object|string} color2 - Второй цвет
 * @returns {number} Расстояние между цветами
 */
function colorDistance(color1, color2) {
    const rgb1 = typeof color1 === 'object' ? color1 : parseColor(color1);
    const rgb2 = typeof color2 === 'object' ? color2 : parseColor(color2);
    
    // Используем евклидово расстояние в RGB пространстве
    const dr = rgb1.r - rgb2.r;
    const dg = rgb1.g - rgb2.g;
    const db = rgb1.b - rgb2.b;
    
    // Также учитываем разницу в яркости для лучшего контраста
    const lum1 = 0.299 * rgb1.r + 0.587 * rgb1.g + 0.114 * rgb1.b;
    const lum2 = 0.299 * rgb2.r + 0.587 * rgb2.g + 0.114 * rgb2.b;
    const dlum = Math.abs(lum1 - lum2);
    
    // Вычисляем разницу в оттенке (hue difference)
    const hue1 = getHue(rgb1.r, rgb1.g, rgb1.b);
    const hue2 = getHue(rgb2.r, rgb2.g, rgb2.b);
    let hueDiff = Math.abs(hue1 - hue2);
    if (hueDiff > 180) hueDiff = 360 - hueDiff; // Берем меньшую дугу
    
    // Комбинированное расстояние с большим весом для разницы в оттенке
    return Math.sqrt(dr * dr + dg * dg + db * db) + dlum * 2 + hueDiff * 3;
}

/**
 * Конвертация hex в rgba
 * @param {string} hex - Цвет в формате hex
 * @param {number} alpha - Прозрачность (по умолчанию 0.5)
 * @returns {string} Цвет в формате rgba
 */
function hexToRgba(hex, alpha = 0.5) {
    const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
    if (result) {
        const r = parseInt(result[1], 16);
        const g = parseInt(result[2], 16);
        const b = parseInt(result[3], 16);
        return `rgba(${r}, ${g}, ${b}, ${alpha})`;
    }
    return `rgba(29, 185, 84, ${alpha})`; // Значение по умолчанию
}

/**
 * Парсинг цвета в RGB объект
 * @param {string} color - Цвет в формате rgba или hex
 * @returns {Object} Объект с r, g, b компонентами
 */
function parseColor(color) {
    let r, g, b;
    
    if (color.startsWith('rgba(')) {
        const rgb = color.replace('rgba(', '').replace(')', '').split(',');
        r = parseInt(rgb[0].trim());
        g = parseInt(rgb[1].trim());
        b = parseInt(rgb[2].trim());
    } else if (color.startsWith('#')) {
        const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(color);
        if (result) {
            r = parseInt(result[1], 16);
            g = parseInt(result[2], 16);
            b = parseInt(result[3], 16);
        } else {
            r = 29; g = 185; b = 84;
        }
    } else {
        r = 29; g = 185; b = 84;
    }
    
    return { r, g, b };
}

// ============================================================================
// PROGRESS MANAGEMENT
// ============================================================================

/**
 * Форматирование времени в формат MM:SS
 * @param {number} seconds - Время в секундах
 * @returns {string} Отформатированное время
 */
function formatTime(seconds) {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
}

/**
 * Обновление прогресс-бара
 * @param {number} currentPosition - Текущая позиция в секундах
 * @param {number} totalDuration - Общая длительность в секундах
 * @param {HTMLElement} progress - Элемент прогресс-бара
 * @param {HTMLElement} currentTimeEl - Элемент текущего времени
 * @param {HTMLElement} durationEl - Элемент общей длительности
 */
function updateProgress(currentPosition, totalDuration, progress, currentTimeEl, durationEl) {
    if (totalDuration > 0) {
        const progressPercent = (currentPosition / totalDuration) * 100;
        progress.style.width = `${progressPercent}%`;

        // Форматируем время
        currentTimeEl.textContent = formatTime(currentPosition);
        durationEl.textContent = formatTime(totalDuration);
    } else {
        progress.style.width = '0%';
        currentTimeEl.textContent = '0:00';
        durationEl.textContent = '0:00';
    }
}

/**
 * Запуск обновления прогресса в реальном времени
 * @param {Object} state - Объект состояния с currentPosition, totalDuration, isPlaying
 * @param {Function} updateCallback - Callback для обновления UI
 * @returns {number} ID интервала
 */
function startProgressUpdate(state, updateCallback) {
    // Используем более эффективный метод обновления
    const intervalId = setInterval(() => {
        if (state.isPlaying && state.currentPosition < state.totalDuration) {
            state.currentPosition += 1;
            // Оптимизация: обновляем только если видно окно
            if (!document.hidden) {
                updateCallback();
            }
        }
    }, 1000);
    
    return intervalId;
}

/**
 * Остановка обновления прогресса
 * @param {number} intervalId - ID интервала
 */
function stopProgressUpdate(intervalId) {
    if (intervalId) {
        clearInterval(intervalId);
    }
}

// ============================================================================
// VISUALIZER MANAGEMENT
// ============================================================================

/**
 * Создание визуализатора с хаотичными параметрами анимации
 * @param {HTMLElement} visualizer - Контейнер визуализатора
 * @param {number} barCount - Количество полосок (по умолчанию 14)
 */
function createVisualizer(visualizer, barCount = 14) {
    visualizer.innerHTML = '';
    for (let i = 0; i < barCount; i++) {
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
        
        visualizer.appendChild(bar);
    }
}

/**
 * Запуск анимации визуализатора
 * @param {HTMLElement} visualizer - Контейнер визуализатора
 * @param {Object} config - Конфигурация с wave_enabled
 */
function animateVisualizer(visualizer, config) {
    // Проверяем настройки первым делом
    if (config && config.wave_enabled === false) {
        stopVisualizer(visualizer);
        return;
    }
    
    // Убираем класс fade-out
    visualizer.classList.remove('fade-out');
    
    // Показываем визуализатор, если он скрыт
    const wasHidden = visualizer.style.display === 'none';
    if (wasHidden) {
        visualizer.style.display = '';
        // Используем requestAnimationFrame для гарантии применения display
        requestAnimationFrame(() => {
            visualizer.classList.add('enabled');
        });
    } else {
        // Если уже видим, сразу добавляем класс
        visualizer.classList.add('enabled');
    }
}

/**
 * Остановка анимации визуализатора с плавным исчезновением
 * @param {HTMLElement} visualizer - Контейнер визуализатора
 */
function stopVisualizer(visualizer) {
    // Убираем класс enabled, чтобы остановить основную анимацию
    visualizer.classList.remove('enabled');
    
    // Если визуализатор видим, добавляем класс fade-out для плавного исчезновения
    if (visualizer.style.display !== 'none') {
        visualizer.classList.add('fade-out');
        
        // После завершения анимации скрываем визуализатор полностью
        setTimeout(() => {
            visualizer.style.display = 'none';
            visualizer.classList.remove('fade-out');
        }, 400); // Длительность анимации исчезновения
    }
}

// ============================================================================
// UI UPDATE FUNCTIONS
// ============================================================================

/**
 * Плавный переход между двумя цветами для ambient light
 * @param {string} fromColor - Начальный цвет
 * @param {string} toColor - Конечный цвет
 * @param {HTMLElement} ambientLight - Элемент ambient light
 * @param {number} duration - Длительность перехода в мс (по умолчанию 800)
 * @returns {Object} Объект с методом cancel() для отмены анимации
 */
function transitionAmbientLight(fromColor, toColor, ambientLight, duration = 800) {
    const fromRGB = parseColor(fromColor);
    const toRGB = parseColor(toColor);
    
    const startTime = performance.now();
    const deltaR = toRGB.r - fromRGB.r;
    const deltaG = toRGB.g - fromRGB.g;
    const deltaB = toRGB.b - fromRGB.b;
    
    let animationId = null;
    let cancelled = false;
    
    function animate(currentTime) {
        if (cancelled) return;
        
        const elapsed = currentTime - startTime;
        const progress = Math.min(elapsed / duration, 1);
        
        // Easing функция для плавного перехода
        const easeProgress = progress < 0.5 
            ? 2 * progress * progress 
            : 1 - Math.pow(-2 * progress + 2, 2) / 2;
        
        const currentR = Math.round(fromRGB.r + deltaR * easeProgress);
        const currentG = Math.round(fromRGB.g + deltaG * easeProgress);
        const currentB = Math.round(fromRGB.b + deltaB * easeProgress);
        
        const colorString = `rgba(${currentR}, ${currentG}, ${currentB}, 0.85)`;
        
        // Применяем цвет
        document.documentElement.style.setProperty('--ambient-color', colorString);
        
        // Применяем тень к обоим изображениям (оптимизированная версия)
        // Используем CSS переменные вместо прямого изменения box-shadow для экономии CPU
        const shadowColor = `rgba(${currentR}, ${currentG}, ${currentB}, 0.6)`;
        document.documentElement.style.setProperty('--cover-shadow', shadowColor);
        
        // Менее тяжелая версия box-shadow (меньше слоев)
        const boxShadow = `0 0 35px ${shadowColor}, 0 0 55px ${shadowColor}`;
        const cover1 = document.getElementById('cover1');
        const cover2 = document.getElementById('cover2');
        if (cover1) cover1.style.boxShadow = boxShadow;
        if (cover2) cover2.style.boxShadow = boxShadow;
        
        if (progress < 1) {
            animationId = requestAnimationFrame(animate);
        }
    }
    
    animationId = requestAnimationFrame(animate);
    
    return {
        cancel: function() {
            cancelled = true;
            if (animationId) {
                cancelAnimationFrame(animationId);
            }
        }
    };
}

/**
 * Обновление ambient light с градиентами по краям
 * @param {Object} edgeColors - Объект с цветами для каждой стороны
 * @param {HTMLElement} ambientLight - Элемент ambient light
 * @param {Object} config - Конфигурация с ambient_light_enabled
 * @param {boolean} useTransition - Использовать плавный переход
 */
function updateAmbientLight(edgeColors, ambientLight, config, useTransition = true) {
    if (config && config.ambient_light_enabled === false) {
        return;
    }
    
    if (edgeColors && edgeColors.top) {
        document.documentElement.style.setProperty('--ambient-top-1', edgeColors.top[0]);
        document.documentElement.style.setProperty('--ambient-top-2', edgeColors.top[1]);
        document.documentElement.style.setProperty('--ambient-top-3', edgeColors.top[2]);
        
        document.documentElement.style.setProperty('--ambient-right-1', edgeColors.right[0]);
        document.documentElement.style.setProperty('--ambient-right-2', edgeColors.right[1]);
        document.documentElement.style.setProperty('--ambient-right-3', edgeColors.right[2]);
        
        document.documentElement.style.setProperty('--ambient-bottom-1', edgeColors.bottom[0]);
        document.documentElement.style.setProperty('--ambient-bottom-2', edgeColors.bottom[1]);
        document.documentElement.style.setProperty('--ambient-bottom-3', edgeColors.bottom[2]);
        
        document.documentElement.style.setProperty('--ambient-left-1', edgeColors.left[0]);
        document.documentElement.style.setProperty('--ambient-left-2', edgeColors.left[1]);
        document.documentElement.style.setProperty('--ambient-left-3', edgeColors.left[2]);
        
        const cover1 = document.getElementById('cover1');
        const cover2 = document.getElementById('cover2');
        if (cover1) cover1.style.boxShadow = 'none';
        if (cover2) cover2.style.boxShadow = 'none';
    }
}

/**
 * Проверяет контраст между текстом и фоном (WCAG AA стандарт)
 * @param {string} textColor - Цвет текста
 * @param {string} bgColor - Цвет фона
 * @param {number} minRatio - Минимальное соотношение контраста (по умолчанию 4.5)
 * @returns {boolean} true если контраст достаточный
 */
function hasGoodContrast(textColor, bgColor, minRatio = 4.5) {
    const textRGB = parseColor(textColor);
    const bgRGB = parseColor(bgColor);
    
    // Вычисляем относительную яркость
    const getLuminance = (rgb) => {
        const [r, g, b] = [rgb.r, rgb.g, rgb.b].map(val => {
            val = val / 255;
            return val <= 0.03928 ? val / 12.92 : Math.pow((val + 0.055) / 1.055, 2.4);
        });
        return 0.2126 * r + 0.7152 * g + 0.0722 * b;
    };
    
    const lum1 = getLuminance(textRGB);
    const lum2 = getLuminance(bgRGB);
    const ratio = (Math.max(lum1, lum2) + 0.05) / (Math.min(lum1, lum2) + 0.05);
    
    return ratio >= minRatio;
}

/**
 * Применение автоматических цветов из изображения
 * @param {Object} colors - Объект с first и second цветами
 * @param {Object} edgeColors - Объект с цветами краев
 * @param {Object} config - Конфигурация
 */
function applyAutoColors(colors, edgeColors, config) {
    if (!config || !config.auto_colors_enabled) {
        return;
    }

    if (edgeColors) {
        updateAmbientLight(edgeColors, null, config, false);
    }

    // Первый цвет для подложки
    // Проверяем яркость и затемняем, если слишком светлый
    const firstColorRGB = parseColor(colors.first);
    let firstLuminance = (0.299 * firstColorRGB.r + 0.587 * firstColorRGB.g + 0.114 * firstColorRGB.b);
    
    // Если первый цвет слишком темный для подложки, используем второй цвет
    let bgColorToUse = colors.first;
    if (firstLuminance < 50) {
        bgColorToUse = colors.second;
        const secondColorRGB = parseColor(colors.second);
        firstLuminance = (0.299 * secondColorRGB.r + 0.587 * secondColorRGB.g + 0.114 * secondColorRGB.b);
        console.log('Первый цвет слишком темный для подложки, используем второй цвет');
    }
    
    let bgColorRGB = parseColor(bgColorToUse);
    // Если цвет слишком светлый (яркость > 120), затемняем его
    if (firstLuminance > 120) {
        // Чем светлее, тем больше затемняем (до 100 единиц максимум)
        const darkenAmount = Math.min(100, Math.round((firstLuminance - 120) * 0.8));
        bgColorRGB = parseColor(darkenColor(bgColorToUse, darkenAmount));
        console.log(`Цвет подложки слишком светлый (${firstLuminance}), затемняем на ${darkenAmount}`);
    } else if (firstLuminance > 80) {
        // Если яркость 80-120, немного затемняем
        bgColorRGB = parseColor(darkenColor(bgColorToUse, 40));
    }
    // Если яркость <= 80, оставляем как есть или слегка затемняем
    else if (firstLuminance > 50) {
        bgColorRGB = parseColor(darkenColor(bgColorToUse, 20));
    }
    
    // Снижаем насыщенность цвета подложки, чтобы он был мягче (менее пестрым)
    // factor 0.5 делает цвет в два раза менее насыщенным (более мягким)
    const desaturatedBg = desaturateColor(`rgba(${bgColorRGB.r}, ${bgColorRGB.g}, ${bgColorRGB.b}, 1)`, 0.5);
    document.documentElement.style.setProperty('--bg-color', desaturatedBg);

    // Выбираем цвет для текста (второй доминантный)
    let textColor = colors.second;
    let textColorRGB = parseColor(textColor);
    
    // Обеспечиваем хороший контраст для читаемости (WCAG AA стандарт)
    if (!hasGoodContrast(textColor, desaturatedBg)) {
        // Если контраст недостаточный, осветляем текст
        textColor = ensureLightColor(textColor, 200);
        textColorRGB = parseColor(textColor);
        console.log('Контраст недостаточный, осветляем текст');
        
        // Если все еще недостаточно, используем белый
        if (!hasGoodContrast(textColor, desaturatedBg)) {
            textColor = 'rgba(255, 255, 255, 1)';
            textColorRGB = { r: 255, g: 255, b: 255 };
            console.log('Контраст все еще недостаточный, используем белый цвет');
        }
    }
    
    // Применяем цвет текста
    document.documentElement.style.setProperty('--text-color', `rgba(${textColorRGB.r}, ${textColorRGB.g}, ${textColorRGB.b}, 1)`);
    document.documentElement.style.setProperty('--wave-color', textColor);
    document.documentElement.style.setProperty('--accent-color', textColor);
    document.documentElement.style.setProperty('--progress-color2', textColor);
    
    const artistElement = document.getElementById('artist');
    if (artistElement) {
        artistElement.style.color = '';
    }
    
    // Цвет фона прогресс-бара - проверяем яркость текста
    const textLuminance = (0.299 * textColorRGB.r + 0.587 * textColorRGB.g + 0.114 * textColorRGB.b);
    let progressBgColor;
    
    if (textLuminance > 100) {
        // Если текст светлый, затемняем для фона прогресс-бара
        progressBgColor = darkenColor(textColor, 60);
    } else {
        // Если текст темный, осветляем или используем полупрозрачный вариант
        progressBgColor = `rgba(${textColorRGB.r}, ${textColorRGB.g}, ${textColorRGB.b}, 0.3)`;
    }
    
    document.documentElement.style.setProperty('--progress-color1', progressBgColor);
    document.documentElement.style.setProperty('--progress-bg', progressBgColor);
}
