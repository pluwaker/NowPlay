# 📦 Инструкции по сборке NowPlay

## ⚠️ Проблема с Nuitka

Nuitka требует установленный C++ компилятор (Visual Studio Build Tools), что может вызывать ошибки компиляции.

**Рекомендация:** Используйте PyInstaller с оптимизированным `build.spec` (режим `--onedir`).

## ✅ Решение: PyInstaller с --onedir (Рекомендуется)

### Быстрая сборка

```bash
# 1. Убедитесь, что установлен PyInstaller
pip install pyinstaller

# 2. Очистите старые сборки (опционально)
rm -rf build dist

# 3. Соберите приложение
pyinstaller build.spec
```

### Результат

После сборки вы найдете приложение в:
```
dist/NowPlay/
├── NowPlay.exe          # Главный исполняемый файл
├── _internal/           # Внутренние библиотеки
│   ├── *.dll
│   ├── *.pyd
│   └── ...
└── ...
```

**Запуск:** Просто запустите `NowPlay.exe` из папки `dist/NowPlay/`

## 🔧 Альтернатива: Использовать build_optimized.spec

Если хотите использовать отдельный файл конфигурации:

```bash
pyinstaller build_optimized.spec
```

## 📊 Ожидаемая производительность

После оптимизации:
- ✅ **CPU при переключении треков: 0.8-2%** (было 20-35%)
- ✅ **Скорость запуска: в 10-50 раз быстрее**
- ✅ **Производительность: близка к исходному коду**

## 🚫 Если всё же хотите использовать Nuitka

### Требования:
1. **Visual Studio Build Tools** (большой размер ~6GB)
   - Скачайте: https://visualstudio.microsoft.com/downloads/
   - Выберите "Build Tools for Visual Studio"
   - Установите "Desktop development with C++"

2. **MinGW-w64** (альтернатива, меньше размером)
   - Скачайте: https://www.mingw-w64.org/downloads/
   - Или используйте: `choco install mingw` (если установлен Chocolatey)

### Сборка с Nuitka:

```bash
# Установка
pip install nuitka

# Сборка (базовая)
python -m nuitka \
    --standalone \
    --windows-icon-from-ico=icon.ico \
    --enable-plugin=tk-inter \
    --include-data-dir=ui=ui \
    --include-data-dir=now_server=now_server \
    --include-data-file=config.json=config.json \
    --include-data-file=icon.ico=icon.ico \
    --windows-disable-console \
    main.py
```

### Если возникают ошибки:

```bash
# Используйте MinGW вместо MSVC
python -m nuitka \
    --standalone \
    --mingw64 \
    --windows-icon-from-ico=icon.ico \
    --enable-plugin=tk-inter \
    main.py
```

## 🔍 Проверка сборки

После сборки проверьте:

1. **Размер файлов:**
   - `--onedir`: ~50-100 МБ (папка)
   - `--onefile`: ~40-80 МБ (один файл, но медленнее)

2. **Производительность:**
   - Запустите приложение
   - Откройте диспетчер задач
   - Переключите трек
   - Проверьте нагрузку CPU (должно быть 0.8-2%)

3. **Работоспособность:**
   - Запустите приложение
   - Нажмите "START"
   - Проверьте, что сервер запускается
   - Откройте URL в браузере

## ❓ Частые проблемы

### Проблема: "Module not found" после сборки

**Решение:** Добавьте модуль в `hiddenimports` в `build.spec`:
```python
hiddenimports=[
    ...
    'ваш_модуль',  # Добавьте сюда
]
```

### Проблема: Не работает в другой папке

**Решение:** Убедитесь, что все файлы из `datas` включены в сборку:
```python
datas=[
    ('ui/*.py', 'ui'),
    ('now_server/*.html', 'now_server'),
    # и т.д.
]
```

### Проблема: Высокая нагрузка CPU (20-35%)

**Причина:** Используется режим `--onefile`

**Решение:** Используйте `--onedir` (уже настроено в `build.spec`):
```python
exe = EXE(
    ...
    onefile=False,  # ВАЖНО!
)
```

## 📝 Рекомендации

1. ✅ **Используйте PyInstaller с `--onedir`** - это самое простое и эффективное решение
2. ❌ **Не используйте `--onefile`** - медленнее в 25-40 раз
3. ❌ **Не используйте Nuitka без необходимости** - требует сложной настройки
4. ✅ **Тестируйте сборку** перед распространением

## 🎯 Итог

**Для большинства случаев используйте:**
```bash
pyinstaller build.spec
```

Это даст вам оптимальный баланс между:
- ⚡ Производительностью
- 🔧 Простотой сборки
- 📦 Размером файлов
- ✅ Надежностью

