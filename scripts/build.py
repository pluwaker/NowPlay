import os
import subprocess
import sys


def build_app():
    # Run PyInstaller
    result = subprocess.run([
        sys.executable, '-m', 'PyInstaller',
        'NowPlayServer.spec',
        '--clean',  # Clean PyInstaller cache
        '--noconfirm'  # Replace output directory without confirmation
    ])

    return result.returncode


if __name__ == '__main__':
    exit_code = build_app()
    sys.exit(exit_code)