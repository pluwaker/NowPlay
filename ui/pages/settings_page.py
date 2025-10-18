# ui/pages/settings_page.py
import customtkinter as ctk
from tkinter import colorchooser, messagebox
import tkinter
import sys
import os

# Добавляем путь к корневой папке для импорта config_manager
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from config_manager import config_manager


class SettingsPage(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="#1e1e1e")
        self.controller = controller
        self.config_data = config_manager.load_config()

        self.create_widgets()

    def create_widgets(self):
        # Заголовок
        title_label = ctk.CTkLabel(
            self,
            text="SETTINGS",
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color="#ffffff"
        )
        title_label.pack(pady=(30, 20))

        # Секция "Шаблоны"
        templates_frame = ctk.CTkFrame(self, fg_color="#2b2b2b", corner_radius=10)
        templates_frame.pack(pady=(0, 20), padx=40, fill="x")

        # Заголовок секции
        section_title = ctk.CTkLabel(
            templates_frame,
            text="Шаблоны",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color="#ffffff"
        )
        section_title.pack(pady=(15, 15))

        # Основной цвет (подложка)
        color_main_frame = ctk.CTkFrame(templates_frame, fg_color="transparent")
        color_main_frame.pack(fill="x", padx=20, pady=(0, 10))

        ctk.CTkLabel(
            color_main_frame,
            text="Цвет подложки",
            font=ctk.CTkFont(size=14),
            text_color="#cccccc"
        ).pack(side="left")

        self.main_color_btn = ctk.CTkButton(
            color_main_frame,
            text="",
            width=40,
            height=30,
            fg_color=self.config_data["main_color"],
            hover_color=self.config_data["main_color"],
            command=lambda: self.change_color("main_color")
        )
        self.main_color_btn.pack(side="right")

        # Цвет текста
        color_text_frame = ctk.CTkFrame(templates_frame, fg_color="transparent")
        color_text_frame.pack(fill="x", padx=20, pady=(0, 10))

        ctk.CTkLabel(
            color_text_frame,
            text="Цвет текста",
            font=ctk.CTkFont(size=14),
            text_color="#cccccc"
        ).pack(side="left")

        self.text_color_btn = ctk.CTkButton(
            color_text_frame,
            text="",
            width=40,
            height=30,
            fg_color=self.config_data["text_color"],
            hover_color=self.config_data["text_color"],
            command=lambda: self.change_color("text_color")
        )
        self.text_color_btn.pack(side="right")

        # Цвет волны
        color_wave_frame = ctk.CTkFrame(templates_frame, fg_color="transparent")
        color_wave_frame.pack(fill="x", padx=20, pady=(0, 10))

        ctk.CTkLabel(
            color_wave_frame,
            text="Цвет волны",
            font=ctk.CTkFont(size=14),
            text_color="#cccccc"
        ).pack(side="left")

        self.wave_color_btn = ctk.CTkButton(
            color_wave_frame,
            text="",
            width=40,
            height=30,
            fg_color=self.config_data["wave_color"],
            hover_color=self.config_data["wave_color"],
            command=lambda: self.change_color("wave_color")
        )
        self.wave_color_btn.pack(side="right")

        # Волна (переключатель)
        wave_switch_frame = ctk.CTkFrame(templates_frame, fg_color="transparent")
        wave_switch_frame.pack(fill="x", padx=20, pady=(0, 15))

        ctk.CTkLabel(
            wave_switch_frame,
            text="Волна",
            font=ctk.CTkFont(size=14),
            text_color="#cccccc"
        ).pack(side="left")

        self.wave_switch_var = ctk.BooleanVar(value=self.config_data["wave_enabled"])
        self.wave_switch = ctk.CTkSwitch(
            wave_switch_frame,
            text="",
            variable=self.wave_switch_var,
            command=self.toggle_wave
        )
        self.wave_switch.pack(side="right")

        # Разделительная линия
        separator = ctk.CTkFrame(self, height=2, fg_color="#444444")
        separator.pack(fill="x", padx=40, pady=15)

        # Кнопка сохранения
        self.save_btn = ctk.CTkButton(
            self,
            text="Сохранить настройки",
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#1db954",
            hover_color="#1aa34a",
            height=40,
            command=self.save_settings
        )
        self.save_btn.pack(pady=10)

        # Блок с ссылкой (только если сервер запущен)
        self.url_frame = ctk.CTkFrame(self, fg_color="#2b2b2b", corner_radius=8)

        # Заголовок ссылки
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

        # Следим за изменениями ссылки от контроллера
        self.controller.obs_link.trace_add("write", self.on_url_changed)
        self.update_url_display()

    def on_url_changed(self, *args):
        """Обновляет отображение URL при изменении"""
        self.update_url_display()

    def update_url_display(self):
        """Обновляет отображение ссылки"""
        url = self.controller.obs_link.get()
        if url:
            self.url_label.configure(text=url)
            self.url_frame.pack(pady=(0, 30), padx=40, fill="x", after=self.save_btn)
            self.copy_btn.configure(state="normal")
        else:
            self.url_frame.pack_forget()
            self.copy_btn.configure(state="disabled")

    def change_color(self, color_type):
        """Изменяет цвет"""
        current_color = self.config_data[color_type]
        color_code = colorchooser.askcolor(
            title=f"Выберите {color_type}",
            initialcolor=current_color
        )[1]

        if color_code:
            self.config_data[color_type] = color_code
            if color_type == "main_color":
                self.main_color_btn.configure(fg_color=color_code, hover_color=color_code)
            elif color_type == "text_color":
                self.text_color_btn.configure(fg_color=color_code, hover_color=color_code)
            else:
                self.wave_color_btn.configure(fg_color=color_code, hover_color=color_code)

    def toggle_wave(self):
        """Переключает визуализатор волны"""
        self.config_data["wave_enabled"] = self.wave_switch_var.get()

    def save_settings(self):
        """Сохраняет настройки"""
        try:
            success = config_manager.save_config(self.config_data)

            if success:
                # УВЕДОМЛЯЕМ СЕРВЕР ОБ ИЗМЕНЕНИИ НАСТРОЕК
                if hasattr(self.controller, 'config_updated'):
                    self.controller.config_updated(self.config_data)

                messagebox.showinfo(
                    "✅ Готово",
                    "Настройки сохранены!\n\n"
                )
            else:
                messagebox.showerror("Ошибка", "Не удалось сохранить настройки")

        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось сохранить настройки: {e}")

    def copy_url(self):
        """Копирует URL в буфер обмена"""
        url = self.controller.obs_link.get()
        if url:
            self.clipboard_clear()
            self.clipboard_append(url)
            messagebox.showinfo("Успех", "Ссылка скопирована в буфер обмена!")