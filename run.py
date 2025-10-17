# run.py
import multiprocessing
from ui.app import NowPlayApp

def main():
    multiprocessing.freeze_support()
    app = NowPlayApp()
    app.mainloop()

if __name__ == "__main__":
    main()