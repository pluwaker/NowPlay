# Build Scripts

Эта папка содержит скрипты и конфигурационные файлы для сборки проекта.

## Использование

Все скрипты должны запускаться из корневой директории проекта:

```bash
# Запуск сборки
python scripts/build.py

# Запуск PyInstaller с spec файлом
pyinstaller scripts/build.spec

# Создание релизного пакета
python scripts/package_release.py

# Минификация HTML
python scripts/minify_html.py
```

## Файлы

- `build.py` - основной скрипт сборки
- `build.spec` - конфигурация PyInstaller для стандартной сборки
- `build_optimized.spec` - конфигурация PyInstaller для оптимизированной сборки
- `main.spec` - конфигурация PyInstaller для сборки main.exe
- `setup_inno.iss` - конфигурация Inno Setup для создания установщика
- `package_release.py` - скрипт для создания релизного пакета
- `minify_html.py` - скрипт для минификации HTML файлов

