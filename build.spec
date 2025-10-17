# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['run.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('ui/pages/*.py', 'ui/pages'),
        ('now_server/*.py', 'now_server'),
        ('now_server/vusialisation.html', 'now_server'),
        ('songinfo', 'songinfo')
    ],
    hiddenimports=[
        'customtkinter',
        'tkinter',
        'tkinter.messagebox',
        'tkinter.colorchooser',
        'sys',
        'aiohttp',
        'aiohttp.web',
        'winsdk',
        'winsdk.windows.media.control',
        'winsdk.windows.storage.streams',
        'multiprocessing',
        'multiprocessing.freeze_support',
        'asyncio',
        'socket',
        'pathlib'
        'pathlib.Path',
        'import sys',
        'os',

    ],
    hookspath=[],
    hooksconfig={},
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
    name='NowPlayServer',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # Измени на True если нужна консоль для отладки
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='icon.ico',  # Добавь иконку если есть
)