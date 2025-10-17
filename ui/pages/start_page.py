# ui/pages/start_page.py
import customtkinter as ctk
from tkinter import messagebox
import tkinter


class StartPage(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="#1e1e1e")
        self.controller = controller

        self.create_widgets()
        self.update_display()

    def create_widgets(self):
        # Заголовок
        title_label = ctk.CTkLabel(
            self,
            text="START/STOP",
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color="#ffffff"
        )
        title_label.pack(pady=(30, 20))

        # Инструкция в рамке
        instruction_frame = ctk.CTkFrame(self, fg_color="#2b2b2b", corner_radius=10)
        instruction_frame.pack(pady=(0, 20), padx=40, fill="x")

        instruction_text = (
            "1. Запустите OBS\n"
            "2. Нажмите 'Добавить новый источник'\n"
            "3. Выберите 'Браузер'\n"
            "4. Впишите название источника и проверьте, что галочка 'Сделать источник видимым' стоит\n"
            "5. Нажмите 'ОК'\n"
            "6. В строке 'URL-адрес' вставьте ссылку, которая появится после нажатия кнопки 'Запустить'\n"
            "7. Поставьте 'Ширину' 400, а 'Высоту' 500\n"
            "8. Нажмите 'ОК'"
        )

        instruction_label = ctk.CTkLabel(
            instruction_frame,
            text=instruction_text,
            font=ctk.CTkFont(size=13),
            text_color="#cccccc",
            justify="left"
        )
        instruction_label.pack(pady=20, padx=20)

        # Разделительная линия
        separator = ctk.CTkFrame(self, height=2, fg_color="#444444")
        separator.pack(fill="x", padx=40, pady=15)

        # Кнопка запуска/остановки
        self.start_btn = ctk.CTkButton(
            self,
            text="Запустить",
            font=ctk.CTkFont(size=16, weight="bold"),
            fg_color="#1db954",
            hover_color="#1aa34a",
            height=45,
            command=self.toggle_server
        )
        self.start_btn.pack(pady=20)

        # Поле с ссылкой (только когда сервер запущен)
        self.url_frame = ctk.CTkFrame(self, fg_color="#2b2b2b", corner_radius=8)

        # Заголовок "Ссылка для источника"
        url_title = ctk.CTkLabel(
            self.url_frame,
            text="Ссылка для источника",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#ffffff"
        )
        url_title.pack(pady=(15, 10))

        # Поле с URL
        url_content = ctk.CTkFrame(self.url_frame, fg_color="transparent")
        url_content.pack(fill="x", padx=15, pady=(0, 15))

        self.url_label = ctk.CTkLabel(
            url_content,
            text="http://localhost:8080/vusialisation.html",
            font=ctk.CTkFont(family="Consolas", size=12),
            text_color="#00ff80",
            justify="left",
            anchor="w"
        )
        self.url_label.pack(side="left", fill="x", expand=True)

        # Кнопка копирования
        self.copy_btn = ctk.CTkButton(
            url_content,
            text="Копировать",
            font=ctk.CTkFont(size=11),
            width=70,
            height=28,
            fg_color="#444444",
            hover_color="#555555",
            command=self.copy_url
        )
        self.copy_btn.pack(side="right", padx=(10, 0))

        # Следим за изменениями ссылки
        self.controller.obs_link.trace_add("write", self.on_url_changed)

    def on_url_changed(self, *args):
        """Обновляет отображение при изменении URL"""
        url = self.controller.obs_link.get()
        if url:
            # Показываем блок с ссылкой
            self.url_label.configure(text=url)
            self.url_frame.pack(pady=(0, 30), padx=40, fill="x", after=self.start_btn)
            self.copy_btn.configure(state="normal")
        else:
            # Скрываем блок с ссылкой
            self.url_frame.pack_forget()
            self.copy_btn.configure(state="disabled")

    def toggle_server(self):
        if self.controller.is_server_running():
            self.stop_server()
        else:
            self.start_server()

    def start_server(self):
        if self.controller.start_server():
            self.start_btn.configure(
                text="Остановить",
                fg_color="#e53935",
                hover_color="#c62828"
            )

    def stop_server(self):
        if self.controller.stop_server():
            self.start_btn.configure(
                text="Запустить",
                fg_color="#1db954",
                hover_color="#1aa34a"
            )

    def copy_url(self):
        url = self.controller.obs_link.get()
        if url:
            self.clipboard_clear()
            self.clipboard_append(url)
            messagebox.showinfo("Успех", "Ссылка скопирована в буфер обмена!")

    def update_display(self):
        """Обновляет отображение при показе страницы"""
        if self.controller.is_server_running():
            self.start_btn.configure(
                text="Остановить",
                fg_color="#e53935",
                hover_color="#c62828"
            )
            # Принудительно обновляем отображение URL
            self.on_url_changed()
        else:
            self.start_btn.configure(
                text="Запустить",
                fg_color="#1db954",
                hover_color="#1aa34a"
            )
            # Скрываем блок с ссылкой
            self.url_frame.pack_forget()