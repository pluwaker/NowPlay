# config_manager.py
import json
import os
from pathlib import Path


class ConfigManager:
    def __init__(self):
        # Используем APPDATA для хранения настроек
        self.app_data_path = Path(os.getenv('APPDATA')) / 'NowPlayServer'
        self.app_data_path.mkdir(exist_ok=True)
        self.config_path = self.app_data_path / "config.json"

        # Настройки по умолчанию
        self.defaults = {
            "main_color": "#7642ff",  # Цвет подложки
            "text_color": "#ffffff",  # Цвет текста
            "wave_color": "#59e8c8",  # Цвет волны
            "wave_enabled": True
        }

    def load_config(self):
        """Загружает конфигурацию"""
        if not self.config_path.exists():
            return self.defaults.copy()

        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                content = f.read()
                if not content:
                    return self.defaults.copy()

                user_config = json.loads(content)
                # Объединяем с настройками по умолчанию
                config = self.defaults.copy()
                config.update(user_config)
                return config

        except (json.JSONDecodeError, IOError) as e:
            print(f"Ошибка загрузки конфига: {e}")
            return self.defaults.copy()

    def save_config(self, config):
        """Сохраняет конфигурацию"""
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=4, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Ошибка сохранения конфига: {e}")
            return False


# Глобальный экземпляр менеджера конфигурации
config_manager = ConfigManager()