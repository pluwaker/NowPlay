# ui/app.py
import customtkinter as ctk
import threading
from tkinter import messagebox
import socket
import os
import tkinter
from pathlib import Path
import sys
import urllib.request
import urllib.error
import json

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
from now_server.now import (run_server)
from ui.mediamonitor_manager import MediaMonitorManager

def find_free_port(start_port=8080, max_port=9000):
    for port in range(start_port, max_port):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("localhost", port))
                return port
            except OSError:
                continue
    raise OSError("Не удалось найти свободный порт в диапазоне 8080–9000")


# Функция больше не нужна - сервер запускается напрямую в потоке


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
        self.mediamonitor_manager = MediaMonitorManager()

        # Register window close handler
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

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
                data = json.dumps(new_config).encode('utf-8')
                req = urllib.request.Request(
                    f"http://localhost:{self.port}/update_config",
                    data=data,
                    headers={'Content-Type': 'application/json'},
                    method='POST'
                )
                req.add_header('User-Agent', 'NowPlay/1.0')
                with urllib.request.urlopen(req, timeout=2) as response:
                    if response.status == 200:
                        print("✅ Настройки применены на сервере")
                    else:
                        print("⚠️ Не удалось применить настройки на сервере")
            except urllib.error.URLError:
                # Сервер не доступен - это нормально
                pass
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

            # Используем threading вместо multiprocessing для экономии памяти
            # Запускаем сервер в отдельном потоке с новым event loop
            import asyncio
            def run_server_thread():
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    run_server(port=self.port)
                except Exception as e:
                    print(f"Ошибка сервера: {e}")
                finally:
                    loop.close()
            
            self.server_thread = threading.Thread(target=run_server_thread, daemon=True)
            self.server_thread.start()
            self.server_process = self.server_thread  # Совместимость с существующим кодом

            self.obs_link.set(self.obs_url)
            print(f"✅ Сервер запущен на {self.obs_url}")
            
            # Start MediaMonitor after server is running
            if not self.mediamonitor_manager.start():
                messagebox.showwarning(
                    "Предупреждение", 
                    "Не удалось запустить MediaMonitor. Сервер работает, но данные о медиа не будут обновляться."
                )
            
            return True

        except Exception as e:
            messagebox.showerror("Ошибка", str(e))
            return False

    def stop_server(self):
        """Останавливает сервер (вызывается из StartPage)"""
        # Stop MediaMonitor first
        self.mediamonitor_manager.stop()
        
        # Для остановки asyncio сервера нужно закрыть event loop
        # Это сложно сделать безопасно, поэтому оставляем daemon=True
        # Сервер остановится автоматически при закрытии приложения
        if hasattr(self, 'server_thread') and self.server_thread and self.server_thread.is_alive():
            # Сервер остановится при закрытии приложения (daemon=True)
            self.server_thread = None
            self.server_process = None
            self.obs_url = ""
            self.obs_link.set("")
            print("🛑 Сервер будет остановлен при закрытии приложения")
            return True
        return False

    def is_server_running(self):
        """Проверяет запущен ли сервер"""
        return hasattr(self, 'server_thread') and self.server_thread and self.server_thread.is_alive()

    def on_closing(self):
        """Handle window close event"""
        self.exit_app()

    def exit_app(self):
        # Stop MediaMonitor if running with increased timeout
        if self.mediamonitor_manager.is_running():
            self.mediamonitor_manager.stop(timeout=3.0)
        
        self.stop_server()
        self.destroy()


if __name__ == "__main__":
    app = NowPlayApp()
    app.mainloop()