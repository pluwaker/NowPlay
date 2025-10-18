# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=[],  # You might want to add the current directory here
    binaries=[],
    datas=[
        ('ui/pages/*.py', 'ui/pages'),
        ('ui/__init__.py', 'ui'),
        ('ui/pages/__init__.py', 'ui/pages'),
        ('now_server/*.py', 'now_server'),
        ('now_server/visualisation.html', 'now_server'),
        ('config.json', '.'),  # Add config files
        ('config.py', '.'),
        ('config_manager.py', '.'),
    ],
    hiddenimports=[
        'customtkinter',
        'tkinter',
        'tkinter.messagebox',
        'tkinter.colorchooser',
        'aiohttp',
        'aiohttp.web',
        'aiohttp.web_app',
        'aiohttp.web_urldispatcher',
        'aiohttp.websocket',
        'winsdk',
        'winsdk.windows.media.control',
        'winsdk.windows.storage.streams',
        'multiprocessing',
        'multiprocessing.context',
        'multiprocessing.managers',
        'multiprocessing.pool',
        'multiprocessing.process',
        'multiprocessing.reduction',
        'multiprocessing.shared_memory',
        'multiprocessing.util',
        'asyncio',
        'asyncio.windows_events',  # For Windows-specific asyncio
        'socket',
        'pathlib',
        'json',
        'os',
        'sys',
        'requests',
        'urllib3',
        'charset_normalizer',
        'idna',
        'certifi',
        'http',
        'http.client',
        'email',
        'email.mime',
        'email.parser',
        'base64',
        'hashlib',
        'ssl',
        'zlib',
        'collections',
        'concurrent.futures',
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

# Additional binaries might be needed for aiohttp
# a.binaries = a.binaries + [('some.dll', 'path/to/some.dll', 'BINARY')]

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
    upx=True,  # Consider setting to False if you encounter issues
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # Set to True for debugging, then back to False for final build
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='icon.ico',  # Make sure this file exists
)