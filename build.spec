# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=['.'],  # добавили корень проекта
    binaries=[],
    datas=[
        ('ui/*.py', 'ui'),
        ('ui/pages/*.py', 'ui/pages'),
        ('now_server/*.py', 'now_server'),
        ('now_server/*.html', 'now_server'),
        ('config.json', '.'),
        ('config.py', '.'),
        ('config_manager.py', '.'),
        ('icon.ico', '.'),
    ],
    hiddenimports=[
        'ui.app',
        'ui.pages.start_page',
        'ui.pages.info_page',
        'ui.pages.settings_page',
        'now_server.server_main',
        'now_server.utils',
        'songinfo.song_info',
        'customtkinter',
        'tkinter',
        'aiohttp',
        'winsdk',
        'asyncio',
    ],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

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
    upx=True,
    console=False,  # включи True, если хочешь видеть ошибки в консоли
    icon='icon.ico',
)
