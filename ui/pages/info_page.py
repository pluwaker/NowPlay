# ui/pages/info_page.py
import customtkinter as ctk
import tkinter


class InfoPage(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="#1e1e1e")
        self.controller = controller

        self.create_widgets()

    def create_widgets(self):
        # Заголовок
        title_label = ctk.CTkLabel(
            self,
            text="INFO",
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color="#ffffff"
        )
        title_label.pack(pady=(30, 20))

        # Информация в рамке
        info_frame = ctk.CTkFrame(self, fg_color="#2b2b2b", corner_radius=10)
        info_frame.pack(pady=(0, 20), padx=40, fill="x")

        info_text = (
            "🎧 NowPlay Server v1.0\n\n"
            "🪄 Приложение для отображения текущего трека в OBS\n\n"
            "🔗 Работает через локальный веб-сервер\n\n"
            "🎨 Поддерживает изменение цветов и шаблонов\n\n"
            "💻 Windows 10+ | Python 3.12+\n\n"
            "Создано с любовью 💚 для стримеров"
        )

        info_label = ctk.CTkLabel(
            info_frame,
            text=info_text,
            font=ctk.CTkFont(size=13),
            text_color="#cccccc",
            justify="left"
        )
        info_label.pack(pady=25, padx=20)

        # Блок с ссылкой (только если сервер запущен)
        self.url_frame = ctk.CTkFrame(self, fg_color="#2b2b2b", corner_radius=8)

        # Следим за изменениями ссылки
        self.controller.obs_link.trace_add("write", self.on_url_changed)
        self.update_url_display()

    def on_url_changed(self, *args):
        """Обновляет отображение URL при изменении"""
        self.update_url_display()

    def update_url_display(self):
        """Обновляет отображение ссылки"""
        url = self.controller.obs_link.get()
        if url:
            # Создаем содержимое блока с ссылкой
            for widget in self.url_frame.winfo_children():
                widget.destroy()

            url_title = ctk.CTkLabel(
                self.url_frame,
                text="Ссылка для источника",
                font=ctk.CTkFont(size=14, weight="bold"),
                text_color="#ffffff"
            )
            url_title.pack(pady=(15, 10))

            url_content = ctk.CTkFrame(self.url_frame, fg_color="transparent")
            url_content.pack(fill="x", padx=15, pady=(0, 15))

            url_label = ctk.CTkLabel(
                url_content,
                text=url,
                font=ctk.CTkFont(family="Consolas", size=12),
                text_color="#00ff80",
                justify="left",
                anchor="w"
            )
            url_label.pack(side="left", fill="x", expand=True)

            copy_btn = ctk.CTkButton(
                url_content,
                text="Копировать",
                font=ctk.CTkFont(size=11),
                width=70,
                height=28,
                fg_color="#444444",
                hover_color="#555555",
                command=lambda: self.copy_url(url)
            )
            copy_btn.pack(side="right", padx=(10, 0))

            self.url_frame.pack(pady=(0, 30), padx=40, fill="x")
        else:
            self.url_frame.pack_forget()

    def copy_url(self, url):
        """Копирует URL в буфер обмена"""
        self.clipboard_clear()
        self.clipboard_append(url)
        ctk.CTkMessagebox.show_info("Успех", "Ссылка скопирована в буфер обмена!")