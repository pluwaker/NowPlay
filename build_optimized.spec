# -*- mode: python ; coding: utf-8 -*-
# ОПТИМИЗИРОВАННАЯ сборка для лучшей производительности

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=['.'],
    binaries=[],
    datas=[
        ('ui/*.py', 'ui'),
        ('ui/pages/*.py', 'ui/pages'),
        ('now_server/*.py', 'now_server'),
        ('now_server/*.html', 'now_server'),
        ('config.json', '.'),
        ('now_server/cover_fetcher.py', 'now_server'),
        ('config.py', '.'),
        ('config_manager.py', '.'),
        ('icon.ico', '.'),
        ('songinfo', 'songinfo'),  # Добавляем папку с обложками
    ],
    hiddenimports=[
        'ui.app',
        'ui.pages.start_page',
        'ui.pages.info_page',
        'ui.pages.settings_page',
        'customtkinter',
        'tkinter',
        'aiohttp',
        'aiohttp.web',
        'aiohttp.web_runner',
        'aiohttp.websocket',
        'winsdk',
        'winsdk.windows.media.control',
        'winsdk.windows.storage.streams',
        'asyncio',
        'asyncio.windows_events',  # Важно для Windows
        'PIL',
        'PIL.Image',
        'PIL.ImageTk',
        'json',
        'urllib.request',
        'urllib.error',
        'urllib.parse',
        'threading',
        'colorsys',
    ],
    hookspath=[],
    runtime_hooks=[],
    excludes=[
        'requests',
        'multiprocessing',
        'pytest',
        'setuptools',
        'distutils',
        'matplotlib',
        'numpy',
        'scipy',
        'pandas',
        'IPython',
        'jupyter',
        'pdb',  # Отладчик
        'unittest',
        'email',
        'http',
        'xml',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,  # Важно: False для лучшей производительности
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# КРИТИЧНО: Используем --onedir вместо --onefile
# --onefile распаковывает все в временную папку при каждом запуске (очень медленно!)
# --onedir создает папку с файлами (быстрее в 10-50 раз)
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='NowPlay',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,  # ОТКЛЮЧЕНО: UPX замедляет распаковку
    console=False,
    icon='icon.ico',
)

# COLLECT создает папку с файлами (--onedir режим)
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='NowPlay',
)

