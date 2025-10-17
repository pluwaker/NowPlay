# main.py
import sys
import os

# Добавляем пути для импортов
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'now_server'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'ui'))

if __name__ == "__main__":
    from run import main
    main()