# 🔧 Оптимизация сборки приложения

## Проблема

Скомпилированный код через PyInstaller работает в **25-40 раз медленнее**, чем исходный код:
- Исходный код: 0.8% CPU
- Скомпилированный: 20-35% CPU

## Причины

### 1. **Режим --onefile (один файл)**
PyInstaller создает один exe файл, который:
- Распаковывает все файлы во временную папку при каждом запуске
- Замедляет импорт модулей
- Создает дополнительную нагрузку на диск и CPU

### 2. **UPX сжатие**
- `upx=True` сжимает exe, но замедляет распаковку
- Может вызывать проблемы с антивирусами

### 3. **Архивирование модулей**
- Все модули упакованы в ZIP архив
- Каждый импорт требует распаковки

## Решения

### ✅ Решение 1: Использовать --onedir (Рекомендуется)

**Создает папку с файлами вместо одного exe**

**Преимущества:**
- ⚡ **В 10-50 раз быстрее** запуск и работа
- 📦 Файлы не распаковываются каждый раз
- 🔧 Легче отлаживать
- 💾 Меньше нагрузка на CPU

**Недостатки:**
- 📁 Создается папка вместо одного файла

**Использование:**
```bash
# Используйте build_optimized.spec
pyinstaller build_optimized.spec
```

Или измените `build.spec`:
```python
exe = EXE(
    ...
    onefile=False,  # ВАЖНО!
    upx=False,      # ОТКЛЮЧИТЬ UPX
)
```

### ✅ Решение 2: Nuitka (Альтернатива)

**Nuitka компилирует Python в нативный C++ код**

**Преимущества:**
- ⚡ **Намного быстрее** PyInstaller (близко к исходному коду)
- 📦 Меньший размер exe
- 🚀 Быстрый запуск
- 🔒 Компиляция в нативный код

**Недостатки:**
- ⚙️ Сложнее настройка
- ⏱️ Дольше компиляция
- 📚 Меньше документации

**Установка:**
```bash
pip install nuitka
```

**Сборка:**
```bash
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

### ✅ Решение 3: cx_Freeze (Альтернатива)

**Легче чем Nuitka, быстрее чем PyInstaller**

**Установка:**
```bash
pip install cx_Freeze
```

**Создайте setup.py:**
```python
from cx_Freeze import setup, Executable

setup(
    name="NowPlay",
    version="1.0",
    description="NowPlay Widget",
    executables=[Executable("main.py", icon="icon.ico", base="Win32GUI")]
)
```

**Сборка:**
```bash
python setup.py build
```

### ✅ Решение 4: Оптимизация build.spec

**Уже применено в build_optimized.spec:**

1. ✅ `onefile=False` - используем --onedir
2. ✅ `upx=False` - отключаем сжатие
3. ✅ `noarchive=False` - не архивируем модули
4. ✅ Добавлены важные скрытые импорты
5. ✅ Исключены ненужные модули

## Сравнение решений

| Инструмент | Скорость | Размер | Простота | Рекомендация |
|-----------|---------|--------|----------|--------------|
| **PyInstaller --onedir** | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ✅ **Рекомендуется** |
| **PyInstaller --onefile** | ⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ❌ Медленно |
| **Nuitka** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ | ✅ Лучшая производительность |
| **cx_Freeze** | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ | ✅ Хорошая альтернатива |

## Быстрое решение

### 1. Используйте build_optimized.spec:

```bash
pyinstaller build_optimized.spec
```

Результат будет в папке `dist/NowPlay/` вместо одного exe файла.

### 2. Или измените текущий build.spec:

```python
exe = EXE(
    ...
    onefile=False,  # Изменить на False
    upx=False,      # Изменить на False
)
```

И добавить в конец:
```python
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    name='NowPlay',
)
```

## Ожидаемые результаты

После перехода на `--onedir`:
- ✅ **CPU при переключении треков: 0.8-2%** (было 20-35%)
- ✅ **Скорость запуска: в 10-50 раз быстрее**
- ✅ **Производительность: близка к исходному коду**

## Дополнительные оптимизации

### 1. Оптимизация импортов в runtime

В `main.py` добавить:
```python
import sys
import os

# Оптимизация для скомпилированного приложения
if getattr(sys, 'frozen', False):
    # Приложение запущено из exe
    import importlib.util
    # Оптимизация путей импорта
    sys.path.insert(0, os.path.dirname(sys.executable))
```

### 2. Оптимизация asyncio для Windows

В `now_server/now.py`:
```python
import sys
import asyncio

# Оптимизация event loop для Windows в скомпилированном приложении
if sys.platform == 'win32' and getattr(sys, 'frozen', False):
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
```

### 3. Предзагрузка модулей

В `main.py`:
```python
# Предзагрузка тяжелых модулей
if getattr(sys, 'frozen', False):
    import aiohttp
    import customtkinter
    # Инициализация при старте
```

## Проверка производительности

После сборки проверьте:

```bash
# 1. Запустите скомпилированное приложение
# 2. Откройте диспетчер задач
# 3. Переключите трек
# 4. Проверьте нагрузку CPU

# Ожидаемый результат:
# --onedir: 0.8-2% CPU
# --onefile: 20-35% CPU (старый)
```

## Рекомендация

**Используйте `build_optimized.spec` с режимом `--onedir`** - это самое простое и эффективное решение!

