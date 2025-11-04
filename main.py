import sys
import os

# вычисляем путь к текущему файлу
current_dir = os.path.dirname(os.path.abspath(__file__))

# ОПТИМИЗАЦИЯ для скомпилированного приложения (PyInstaller)
if getattr(sys, 'frozen', False):
    # Приложение запущено из exe - используем путь к exe
    if hasattr(sys, '_MEIPASS'):
        # PyInstaller создает временную папку _MEIPASS
        current_dir = sys._MEIPASS
    else:
        # Для --onedir режима
        current_dir = os.path.dirname(sys.executable)
    
    # Оптимизация путей импорта для скомпилированного приложения
    sys.path.insert(0, current_dir)
    
    # Оптимизация asyncio для Windows в скомпилированном приложении
    if sys.platform == 'win32':
        import asyncio
        # Используем ProactorEventLoop для лучшей производительности на Windows
        if isinstance(asyncio.get_event_loop_policy(), asyncio.DefaultEventLoopPolicy):
            asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
else:
    # Исходный код - обычные пути
    if current_dir not in sys.path:
        sys.path.insert(0, current_dir)

# теперь импортируем корректно
from ui.app import NowPlayApp


def main():
    print("🚀 Starting NowPlayApp...")
    app = NowPlayApp()
    print("✅ NowPlayApp started successfully")
    app.mainloop()


if __name__ == "__main__":
    main()
