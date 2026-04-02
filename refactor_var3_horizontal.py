#!/usr/bin/env python3
"""
Script to refactor visualisation_var3_horizontal.html to use common.js
"""

import re

# Read the file
with open('now_server/visualisation_var3_horizontal.html', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Add script tag for common.js
content = content.replace(
    '    </div>\n\n    <script>\n    // Элементы DOM',
    '    </div>\n\n    <script src="common.js"></script>\n    <script>\n    // Элементы DOM'
)

# 2. Remove logPerformance, getColorAtPoint, getEdgeColors functions
pattern1 = r'    const performanceStats = window\.performanceStats;\s+function logPerformance.*?(?=\n    // Создаём)'
content = re.sub(pattern1, '    const performanceStats = window.performanceStats;\n    \n', content, flags=re.DOTALL)

# 3. Remove createVisualizer function
pattern2 = r'    // Создаём \d+ полосок визуализатора.*?function createVisualizer\(\).*?}\n\n'
content = re.sub(pattern2, '', content, flags=re.DOTALL)

# 4. Update createVisualizer call
content = content.replace(
    '        createVisualizer();',
    '        createVisualizer(visualizer, 30);'
)

# 5. Remove formatTime, updateProgress, startProgressUpdate, stopProgressUpdate
pattern3 = r'    // Форматирование времени\s+function formatTime.*?}\n\n    // Обновление статуса подключения'
content = re.sub(pattern3, '    // Обновление статуса подключения', content, flags=re.DOTALL)

# 6. Update updateProgress calls
content = content.replace(
    'updateProgress();',
    'updateProgress(currentPosition, totalDuration, progress, currentTimeEl, durationEl);'
)

# 7. Update startProgressUpdate calls
old_start = '''            if (isPlaying) {
                startProgressUpdate();
            } else {
                stopProgressUpdate();
            }'''
new_start = '''            if (isPlaying) {
                const state = { currentPosition, totalDuration, isPlaying };
                progressInterval = startProgressUpdate(state, () => {
                    currentPosition = state.currentPosition;
                    updateProgress(currentPosition, totalDuration, progress, currentTimeEl, durationEl);
                });
            } else {
                stopProgressUpdate(progressInterval);
                progressInterval = null;
            }'''
content = content.replace(old_start, new_start)

# Another startProgressUpdate pattern
old_start2 = '''                if (isPlaying) {
                    startProgressUpdate();
                }'''
new_start2 = '''                if (isPlaying) {
                    const state = { currentPosition, totalDuration, isPlaying };
                    progressInterval = startProgressUpdate(state, () => {
                        currentPosition = state.currentPosition;
                        updateProgress(currentPosition, totalDuration, progress, currentTimeEl, durationEl);
                    });
                }'''
content = content.replace(old_start2, new_start2)

# 8. Update stopProgressUpdate calls
content = content.replace(
    'stopProgressUpdate();',
    'stopProgressUpdate(progressInterval);\n                progressInterval = null;'
)

# 9. Remove all color utility functions (getDominantColors through applyAutoColors)
# This is the big one - remove from getDominantColors to just before the second applyConfig
pattern4 = r'    // Получение двух доминирующих цветов из изображения\s+function getDominantColors.*?(?=\n    // Применение конфигурации\s+function applyConfig\(config\) \{\s+if \(config\))'
content = re.sub(pattern4, '', content, flags=re.DOTALL)

# Write the result
with open('now_server/visualisation_var3_horizontal.html', 'w', encoding='utf-8') as f:
    f.write(content)

print("Refactoring complete!")
