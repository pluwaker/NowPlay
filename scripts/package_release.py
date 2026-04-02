"""
Скрипт для упаковки релиза NowPlay
Создает ZIP архив из папки dist/NowPlay/ для загрузки на GitHub
"""

import os
import shutil
import zipfile
from pathlib import Path
from datetime import datetime

def get_version():
    """Получает версию из config.json или использует текущую дату"""
    try:
        import json
        with open('config.json', 'r', encoding='utf-8') as f:
            config = json.load(f)
            return config.get('version', '1.0.0')
    except:
        return datetime.now().strftime('%Y.%m.%d')

def create_release():
    """Создает ZIP архив для релиза"""
    dist_dir = Path('dist')
    release_dir = Path('release')
    release_dir.mkdir(exist_ok=True)
    
    # Проверяем наличие папки с собранным приложением
    app_dir = dist_dir / 'NowPlay'
    if not app_dir.exists():
        print("❌ Ошибка: Папка dist/NowPlay/ не найдена!")
        print("   Сначала соберите приложение: pyinstaller build.spec")
        return False
    
    version = get_version()
    zip_name = f"NowPlay-v{version}-Windows.zip"
    zip_path = release_dir / zip_name
    
    print(f"📦 Создание релиза: {zip_name}")
    print(f"   Из папки: {app_dir}")
    print(f"   В файл: {zip_path}")
    
    # Создаем ZIP архив
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        # Добавляем все файлы из папки приложения
        for root, dirs, files in os.walk(app_dir):
            # Пропускаем ненужные файлы
            dirs[:] = [d for d in dirs if d not in ['__pycache__', '.git']]
            
            for file in files:
                if file.endswith(('.pyc', '.pyo', '.pyd')):
                    continue
                
                file_path = Path(root) / file
                # Относительный путь внутри архива
                arcname = file_path.relative_to(app_dir.parent)
                zipf.write(file_path, arcname)
                print(f"   ✓ {arcname}")
    
    # Размер файла
    size_mb = zip_path.stat().st_size / (1024 * 1024)
    print(f"\n✅ Релиз создан: {zip_path}")
    print(f"   Размер: {size_mb:.2f} МБ")
    print(f"\n📤 Теперь можно загрузить на GitHub:")
    print(f"   1. Перейдите на https://github.com/ваш-username/NowPlay/releases/new")
    print(f"   2. Загрузите файл: release/{zip_name}")
    print(f"   3. Добавьте описание релиза")
    
    return True

if __name__ == '__main__':
    print("🚀 Создание релиза NowPlay\n")
    success = create_release()
    if not success:
        exit(1)












