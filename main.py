# main.py
import multiprocessing
import sys
import os

# Добавляем пути для импортов
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)
sys.path.insert(0, os.path.join(current_dir, 'ui'))

try:
    from ui.app import NowPlayApp
except ImportError as e:
    print(f"Import error: {e}")
    print("Current sys.path:", sys.path)
    # Пробуем прямой импорт
    try:
        from app import NowPlayApp
    except ImportError:
        raise

def main():
    multiprocessing.freeze_support()
    app = NowPlayApp()
    app.mainloop()

if __name__ == "__main__":
    main()