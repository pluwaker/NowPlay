# ui/app.py
import customtkinter as ctk
import multiprocessing
from tkinter import messagebox
import socket
import os
import tkinter
from now_server.now import run_server
import requests

def find_free_port(start_port=8080, max_port=9000):
    for port in range(start_port, max_port):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("localhost", port))
                return port
            except OSError:
                continue
    raise OSError("Не удалось найти свободный порт в диапазоне 8080–9000")


def start_server_process(port):
    run_server(port=port)


class NowPlayApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("NowPlay Server")
        self.geometry("1000x700")
        self.minsize(800, 600)  # Минимальный размер окна

        self.port = None
        self.obs_url = ""
        self.server_process = None
        self.obs_link = tkinter.StringVar()

        # ====== Боковое меню ======
        self.sidebar = ctk.CTkFrame(self, width=160, corner_radius=0)
        self.sidebar.pack(side="left", fill="y", padx=(0, 5))

        self.start_btn = ctk.CTkButton(
            self.sidebar, 
            text="🚀 START", 
            command=self.show_start,
            height=40,
            font=ctk.CTkFont(size=13, weight="bold")
        )
        self.settings_btn = ctk.CTkButton(
            self.sidebar, 
            text="⚙️ SETTINGS", 
            command=self.show_settings,
            height=40,
            font=ctk.CTkFont(size=13, weight="bold")
        )
        self.info_btn = ctk.CTkButton(
            self.sidebar, 
            text="ℹ️ INFO", 
            command=self.show_info,
            height=40,
            font=ctk.CTkFont(size=13, weight="bold")
        )
        self.exit_btn = ctk.CTkButton(
            self.sidebar, 
            text="❌ EXIT", 
            fg_color="#d9534f", 
            command=self.exit_app,
            height=40,
            font=ctk.CTkFont(size=13, weight="bold")
        )

        self.start_btn.pack(pady=(20, 10), fill="x", padx=15)
        self.settings_btn.pack(pady=10, fill="x", padx=15)
        self.info_btn.pack(pady=10, fill="x", padx=15)
        self.exit_btn.pack(side="bottom", pady=(10, 20), fill="x", padx=15)

        # ====== Основное содержимое ======
        self.content = ctk.CTkFrame(self, fg_color="#1e1e1e")
        self.content.pack(side="right", fill="both", expand=True, padx=(0, 5), pady=5)

        # Словарь для хранения страниц
        self.pages = {}
        self.current_page = None

        # Отображаем первую вкладку
        self.show_start()

    def config_updated(self, new_config):
        """Отправляет новые настройки на сервер"""
        if self.is_server_running():
            try:
                response = requests.post(
                    f"http://localhost:{self.port}/update_config",
                    json=new_config,
                    timeout=2
                )
                if response.status_code == 200:
                    print("✅ Настройки применены на сервере")
                else:
                    print("⚠️ Не удалось применить настройки на сервере")
            except Exception as e:
                print(f"❌ Ошибка отправки настроек: {e}")

    # --------------------- ВКЛАДКИ ---------------------
    def clear_content(self):
        if self.current_page:
            self.current_page.pack_forget()

    def show_start(self):
        self.clear_content()

        if "start" not in self.pages:
            from ui.pages.start_page import StartPage
            self.pages["start"] = StartPage(self.content, self)

        self.current_page = self.pages["start"]
        self.current_page.pack(fill="both", expand=True, padx=0, pady=0)

        # Обновляем кнопки меню
        self.update_menu_buttons("start")

    def show_settings(self):
        self.clear_content()

        if "settings" not in self.pages:
            from ui.pages.settings_page import SettingsPage
            self.pages["settings"] = SettingsPage(self.content, self)

        self.current_page = self.pages["settings"]
        self.current_page.pack(fill="both", expand=True, padx=0, pady=0)

        # Обновляем кнопки меню
        self.update_menu_buttons("settings")

    def show_info(self):
        self.clear_content()

        if "info" not in self.pages:
            from ui.pages.info_page import InfoPage
            self.pages["info"] = InfoPage(self.content, self)

        self.current_page = self.pages["info"]
        self.current_page.pack(fill="both", expand=True, padx=0, pady=0)

        # Обновляем кнопки меню
        self.update_menu_buttons("info")

    def update_menu_buttons(self, active_page):
        """Обновляет внешний вид кнопок меню"""
        buttons = {
            "start": self.start_btn,
            "settings": self.settings_btn,
            "info": self.info_btn
        }

        for page, button in buttons.items():
            if page == active_page:
                button.configure(fg_color="#2b2b2b", hover_color="#3b3b3b")
            else:
                button.configure(fg_color=["#3b8ed0", "#1f6aa5"], hover_color=["#36719f", "#144870"])

    # --------------------- СЕРВЕРНЫЕ ФУНКЦИИ ---------------------
    def start_server(self):
        """Запускает сервер (вызывается из StartPage)"""
        try:
            self.port = find_free_port()
            self.obs_url = f"http://localhost:{self.port}/index.html"

            self.server_process = multiprocessing.Process(
                target=start_server_process,
                args=(self.port,),
                daemon=True
            )
            self.server_process.start()

            self.obs_link.set(self.obs_url)
            print(f"✅ Сервер запущен на {self.obs_url}")
            return True

        except Exception as e:
            messagebox.showerror("Ошибка", str(e))
            return False

    def stop_server(self):
        """Останавливает сервер (вызывается из StartPage)"""
        if self.server_process and self.server_process.is_alive():
            self.server_process.terminate()
            self.server_process.join()
            self.server_process = None
            self.obs_url = ""
            self.obs_link.set("")
            print("🛑 Сервер остановлен")
            return True
        return False

    def is_server_running(self):
        """Проверяет запущен ли сервер"""
        return self.server_process and self.server_process.is_alive()

    def exit_app(self):
        self.stop_server()
        self.destroy()


if __name__ == "__main__":
    app = NowPlayApp()
    app.mainloop()