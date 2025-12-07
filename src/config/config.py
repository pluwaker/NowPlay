# config.py
import os
from pathlib import Path


class Config:
    # Основные пути
    PROJECT_ROOT = Path(__file__).parent.parent.parent  # Переходим из src/config/ в корень проекта
    OUTPUT_DIR = PROJECT_ROOT / "songinfo"

    # Настройки сервера
    DEFAULT_PORT = 58080
    CHECK_INTERVAL = 3  # секунды

    # Настройки по умолчанию
    DEFAULT_DATA = {
        "artist": "Не воспроизводится",
        "title": "Нет данных",
        "cover_version": 1
    }

    @classmethod
    def ensure_directories(cls):
        """Создает необходимые директории"""
        cls.OUTPUT_DIR.mkdir(exist_ok=True)