import sys
import os

# вычисляем путь к текущему файлу
current_dir = os.path.dirname(os.path.abspath(__file__))

# добавляем текущую папку в sys.path
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
