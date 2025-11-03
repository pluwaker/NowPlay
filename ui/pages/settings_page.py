# ui/pages/settings_page.py
import customtkinter as ctk
from tkinter import colorchooser, messagebox
import tkinter
import sys
import os
import urllib.request
import urllib.error
import json
import threading

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
        # Создаем прокручиваемый контейнер для всего контента
        self.scrollable_frame = ctk.CTkScrollableFrame(
            self,
            fg_color="#1e1e1e",
            corner_radius=0
        )
        self.scrollable_frame.pack(fill="both", expand=True, padx=0, pady=0)
        
        # Заголовок
        title_label = ctk.CTkLabel(
            self.scrollable_frame,
            text="SETTINGS",
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color="#ffffff"
        )
        title_label.pack(pady=(20, 20))

        # Секция "Шаблоны"
        templates_frame = ctk.CTkFrame(self.scrollable_frame, fg_color="#2b2b2b", corner_radius=10)
        templates_frame.pack(pady=(0, 20), padx=30, fill="x")

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


        # Акцентный цвет
        color_accent_frame = ctk.CTkFrame(templates_frame, fg_color="transparent")
        color_accent_frame.pack(fill="x", padx=20, pady=(0, 10))

        ctk.CTkLabel(
            color_accent_frame,
            text="Акцентный цвет (градиент волны)",
            font=ctk.CTkFont(size=14),
            text_color="#cccccc"
        ).pack(side="left")

        self.accent_color_btn = ctk.CTkButton(
            color_accent_frame,
            text="",
            width=40,
            height=30,
            fg_color=self.config_data["accent_color"],
            hover_color=self.config_data["accent_color"],
            command=lambda: self.change_color("accent_color")
        )
        self.accent_color_btn.pack(side="right")

        # Цвет текста
        color_text_frame = ctk.CTkFrame(templates_frame, fg_color="transparent")
        color_text_frame.pack(fill="x", padx=20, pady=(0, 10))

        ctk.CTkLabel(
            color_text_frame,
            text="Цвет названия трека",
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

        # Цвет имени исполнителя
        color_artist_frame = ctk.CTkFrame(templates_frame, fg_color="transparent")
        color_artist_frame.pack(fill="x", padx=20, pady=(0, 10))

        ctk.CTkLabel(
            color_artist_frame,
            text="Цвет имени исполнителя",
            font=ctk.CTkFont(size=14),
            text_color="#cccccc"
        ).pack(side="left")

        self.artist_color_btn = ctk.CTkButton(
            color_artist_frame,
            text="",
            width=40,
            height=30,
            fg_color=self.config_data.get("artist_color", "#b3b3b3"),
            hover_color=self.config_data.get("artist_color", "#b3b3b3"),
            command=lambda: self.change_color("artist_color")
        )
        self.artist_color_btn.pack(side="right")

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

        # Градиент прогресс-бара - цвет 1
        color_progress1_frame = ctk.CTkFrame(templates_frame, fg_color="transparent")
        color_progress1_frame.pack(fill="x", padx=20, pady=(0, 5))

        ctk.CTkLabel(
            color_progress1_frame,
            text="Задний фон прогресс бара",
            font=ctk.CTkFont(size=14),
            text_color="#cccccc"
        ).pack(side="left")

        self.progress_color1_btn = ctk.CTkButton(
            color_progress1_frame,
            text="",
            width=40,
            height=30,
            fg_color=self.config_data.get("progress_color1", "#1db954"),
            hover_color=self.config_data.get("progress_color1", "#1db954"),
            command=lambda: self.change_color("progress_color1")
        )
        self.progress_color1_btn.pack(side="right")

        # Градиент прогресс-бара - цвет 2
        color_progress2_frame = ctk.CTkFrame(templates_frame, fg_color="transparent")
        color_progress2_frame.pack(fill="x", padx=20, pady=(0, 10))

        ctk.CTkLabel(
            color_progress2_frame,
            text="Цвет прогресс бара",
            font=ctk.CTkFont(size=14),
            text_color="#cccccc"
        ).pack(side="left")

        self.progress_color2_btn = ctk.CTkButton(
            color_progress2_frame,
            text="",
            width=40,
            height=30,
            fg_color=self.config_data.get("progress_color2", "#1ed760"),
            hover_color=self.config_data.get("progress_color2", "#1ed760"),
            command=lambda: self.change_color("progress_color2")
        )
        self.progress_color2_btn.pack(side="right")

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

        # Подсветка (переключатель)
        ambient_switch_frame = ctk.CTkFrame(templates_frame, fg_color="transparent")
        ambient_switch_frame.pack(fill="x", padx=20, pady=(0, 15))

        ctk.CTkLabel(
            ambient_switch_frame,
            text="Подсветка обложки",
            font=ctk.CTkFont(size=14),
            text_color="#cccccc"
        ).pack(side="left")

        self.ambient_switch_var = ctk.BooleanVar(value=self.config_data.get("ambient_light_enabled", True))
        self.ambient_switch = ctk.CTkSwitch(
            ambient_switch_frame,
            text="",
            variable=self.ambient_switch_var,
            command=self.toggle_ambient_light
        )
        self.ambient_switch.pack(side="right")

        # Автоматические цвета (переключатель)
        auto_colors_switch_frame = ctk.CTkFrame(templates_frame, fg_color="transparent")
        auto_colors_switch_frame.pack(fill="x", padx=20, pady=(0, 15))

        ctk.CTkLabel(
            auto_colors_switch_frame,
            text="Автоматические цвета",
            font=ctk.CTkFont(size=14),
            text_color="#cccccc"
        ).pack(side="left")

        self.auto_colors_switch_var = ctk.BooleanVar(value=self.config_data.get("auto_colors_enabled", False))
        self.auto_colors_switch = ctk.CTkSwitch(
            auto_colors_switch_frame,
            text="",
            variable=self.auto_colors_switch_var,
            command=self.toggle_auto_colors
        )
        self.auto_colors_switch.pack(side="right")

        # Сохраняем список всех кнопок цветов для управления их состоянием
        self.color_buttons = [
            ("main_color", self.main_color_btn),
            ("accent_color", self.accent_color_btn),
            ("text_color", self.text_color_btn),
            ("artist_color", self.artist_color_btn),
            ("wave_color", self.wave_color_btn),
            ("progress_color1", self.progress_color1_btn),
            ("progress_color2", self.progress_color2_btn)
        ]

        # Инициализируем состояние кнопок
        self.update_color_buttons_state()

        # Выбор источника медиа
        source_frame = ctk.CTkFrame(templates_frame, fg_color="transparent")
        source_frame.pack(fill="x", padx=20, pady=(10, 10))

        source_label_frame = ctk.CTkFrame(source_frame, fg_color="transparent")
        source_label_frame.pack(fill="x", pady=(0, 5))

        ctk.CTkLabel(
            source_label_frame,
            text="Источник медиа",
            font=ctk.CTkFont(size=14),
            text_color="#cccccc"
        ).pack(side="left")

        refresh_source_btn = ctk.CTkButton(
            source_label_frame,
            text="Обновить",
            font=ctk.CTkFont(size=11),
            width=80,
            height=25,
            fg_color="#444444",
            hover_color="#555555",
            command=self.refresh_sources
        )
        refresh_source_btn.pack(side="right")

        self.source_var = ctk.StringVar(
            value=self.config_data.get("selected_media_source", "auto")
        )

        self.source_menu = ctk.CTkOptionMenu(
            source_frame,
            values=["Автоматически"],
            variable=self.source_var,
            command=self.change_source,
            width=200
        )
        self.source_menu.pack(side="left", padx=(0, 10))

        self.source_display_label = ctk.CTkLabel(
            source_frame,
            text="(Загрузка...)",
            font=ctk.CTkFont(size=11),
            text_color="#888888"
        )
        self.source_display_label.pack(side="left")

        # Инициализируем список источников
        self.sources_map = {}  # id -> name
        self.refresh_sources()

        # Изменение позиции
        position_frame = ctk.CTkFrame(templates_frame, fg_color="transparent")
        position_frame.pack(fill="x", padx=20, pady=(10, 15))

        ctk.CTkLabel(
            position_frame,
            text="Позиционирование",
            font=ctk.CTkFont(size=14),
            text_color="#cccccc"
        ).pack(side="left")

        positions = {
            "Слева-сверху": ("flex-start", "flex-start"),
            "Справа-сверху": ("flex-end", "flex-start"),
            "Слева-снизу": ("flex-start", "flex-end"),
            "Справа-снизу": ("flex-end", "flex-end"),
            "Центр": ("center", "center")
        }

        self.position_var = ctk.StringVar(
            value=self.config_data.get("position", "Справа-снизу")
        )

        self.position_menu = ctk.CTkOptionMenu(
            position_frame,
            values=list(positions.keys()),
            variable=self.position_var,
            command=self.change_position
        )
        self.position_menu.pack(side="right")

        self.positions_map = positions  # сохраним для доступа при сохранении


        # Разделительная линия
        separator = ctk.CTkFrame(self.scrollable_frame, height=2, fg_color="#444444")
        separator.pack(fill="x", padx=30, pady=15)

        # Кнопка сохранения
        self.save_btn = ctk.CTkButton(
            self.scrollable_frame,
            text="Сохранить настройки",
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#1db954",
            hover_color="#1aa34a",
            height=40,
            width=250,
            command=self.save_settings
        )
        self.save_btn.pack(pady=15)

        # Блок с ссылкой (только если сервер запущен)
        self.url_frame = ctk.CTkFrame(self.scrollable_frame, fg_color="#2b2b2b", corner_radius=8)

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
            text="http://localhost:8080/index.html",
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
            self.url_frame.pack(pady=(0, 30), padx=30, fill="x")
            self.copy_btn.configure(state="normal")
        else:
            self.url_frame.pack_forget()
            self.copy_btn.configure(state="disabled")

    def get_server_url(self):
        """Получает URL сервера"""
        url = self.controller.obs_link.get()
        if url:
            # Извлекаем базовый URL (без index.html)
            base_url = url.replace('/index.html', '').replace('/visualisation.html', '').strip('/')
            return base_url
        return None

    def refresh_sources(self):
        """Обновляет список источников медиа"""
        server_url = self.get_server_url()
        if not server_url:
            self.source_display_label.configure(text="(Сервер не запущен)")
            return

        def fetch_sources():
            try:
                req = urllib.request.Request(f"{server_url}/sources")
                req.add_header('User-Agent', 'NowPlay/1.0')
                with urllib.request.urlopen(req, timeout=2) as response:
                    if response.status == 200:
                        data = json.loads(response.read().decode('utf-8'))
                        sources = data.get("sources", [])
                        
                        # Обновляем UI в главном потоке
                        self.after(0, self.update_sources_ui, sources)
                    else:
                        self.after(0, lambda: self.source_display_label.configure(
                            text="(Ошибка загрузки)")
                        )
            except urllib.error.URLError:
                self.after(0, lambda: self.source_display_label.configure(
                    text="(Сервер не доступен)")
            )
            except Exception as e:
                self.after(0, lambda: self.source_display_label.configure(
                    text=f"(Ошибка: {str(e)[:30]})")
                )

        # Запускаем в отдельном потоке
        thread = threading.Thread(target=fetch_sources, daemon=True)
        thread.start()
        self.source_display_label.configure(text="(Загрузка...)")

    def update_sources_ui(self, sources):
        """Обновляет UI со списком источников"""
        # Маппинг: display_name -> source_id
        self.sources_map = {}
        source_names = ["Автоматически"]
        
        for source in sources:
            source_id = source.get("id", "")
            source_name = source.get("name", source_id)
            if source_id:
                # Создаем читаемое имя
                if len(source_id) > 30:
                    display_name = f"{source_name} ({source_id[:20]}...)"
                else:
                    display_name = f"{source_name} ({source_id})"
                
                source_names.append(display_name)
                self.sources_map[display_name] = source_id

        # Обновляем меню
        self.source_menu.configure(values=source_names)
        
        # Восстанавливаем выбранное значение или ставим по умолчанию
        selected_source_id = self.config_data.get("selected_media_source", "auto")
        if selected_source_id == "auto" or selected_source_id == "":
            self.source_var.set("Автоматически")
        else:
            # Ищем соответствующий display_name
            found = False
            for display_name, mapped_source_id in self.sources_map.items():
                if mapped_source_id == selected_source_id:
                    self.source_var.set(display_name)
                    found = True
                    break
            if not found:
                self.source_var.set("Автоматически")
                self.config_data["selected_media_source"] = "auto"

        # Обновляем подпись
        count = len(sources)
        self.source_display_label.configure(
            text=f"({count} источников)" if count > 0 else "(Нет источников)"
        )

    def change_source(self, choice):
        """Меняет выбранный источник медиа"""
        if choice == "Автоматически":
            self.config_data["selected_media_source"] = "auto"
        else:
            # Получаем ID источника по display_name
            source_id = self.sources_map.get(choice, "auto")
            self.config_data["selected_media_source"] = source_id
        
        # Обновляем конфигурацию на сервере
        self.update_server_config()

    def update_server_config(self, config_update=None):
        """Обновляет конфигурацию на сервере"""
        server_url = self.get_server_url()
        if not server_url:
            return

        def send_update():
            try:
                # Если передан config_update, отправляем его, иначе отправляем текущую конфигурацию
                if config_update:
                    data_to_send = config_update
                else:
                    # Отправляем только настройки, которые должны применяться сразу
                    data_to_send = {
                        "selected_media_source": self.config_data.get("selected_media_source", "auto"),
                        "justify_content": self.config_data.get("justify_content", "flex-end"),
                        "align_items": self.config_data.get("align_items", "flex-end")
                    }
                
                data = json.dumps(data_to_send).encode('utf-8')
                req = urllib.request.Request(
                    f"{server_url}/update_config",
                    data=data,
                    headers={'Content-Type': 'application/json'},
                    method='POST'
                )
                req.add_header('User-Agent', 'NowPlay/1.0')
                with urllib.request.urlopen(req, timeout=2) as response:
                    if response.status == 200:
                        print(f"✅ Конфигурация обновлена на сервере")
            except urllib.error.URLError:
                # Сервер не запущен - это нормально
                pass
            except Exception as e:
                print(f"⚠️ Не удалось обновить конфигурацию на сервере: {e}")

        # Запускаем в отдельном потоке
        thread = threading.Thread(target=send_update, daemon=True)
        thread.start()

    def change_position(self, choice):
        """Меняет позицию отображения"""
        if choice in self.positions_map:
            justify, align = self.positions_map[choice]
            self.config_data["position"] = choice
            self.config_data["justify_content"] = justify
            self.config_data["align_items"] = align
            # Сразу сохраняем и применяем изменения
            config_manager.save_config(self.config_data)
            # Отправляем настройки позиционирования на сервер
            self.update_server_config({
                "justify_content": justify,
                "align_items": align,
                "position": choice
            })

    def change_color(self, color_type):
        """Изменяет цвет"""
        # Проверяем, включены ли автоматические цвета
        if self.config_data.get("auto_colors_enabled", False):
            messagebox.showwarning(
                "Автоматические цвета включены",
                "Отключите 'Автоматические цвета', чтобы изменить цвета вручную."
            )
            return

        current_color = self.config_data.get(color_type, self.get_default_color(color_type))
        color_code = colorchooser.askcolor(
            title=f"Выберите {color_type}",
            initialcolor=current_color
        )[1]

        if color_code:
            self.config_data[color_type] = color_code
            if color_type == "main_color":
                self.main_color_btn.configure(fg_color=color_code, hover_color=color_code)
            elif color_type == "accent_color":
                self.accent_color_btn.configure(fg_color=color_code, hover_color=color_code)
            elif color_type == "text_color":
                self.text_color_btn.configure(fg_color=color_code, hover_color=color_code)
            elif color_type == "artist_color":
                self.artist_color_btn.configure(fg_color=color_code, hover_color=color_code)
            elif color_type == "wave_color":
                self.wave_color_btn.configure(fg_color=color_code, hover_color=color_code)
            elif color_type == "progress_color1":
                self.progress_color1_btn.configure(fg_color=color_code, hover_color=color_code)
            elif color_type == "progress_color2":
                self.progress_color2_btn.configure(fg_color=color_code, hover_color=color_code)

    def get_default_color(self, color_type):
        """Возвращает цвет по умолчанию"""
        defaults = {
            "artist_color": "#b3b3b3",
            "progress_color1": "#1db954",
            "progress_color2": "#1ed760"
        }
        return defaults.get(color_type, "#ffffff")

    def toggle_wave(self):
        """Переключает визуализатор волны"""
        self.config_data["wave_enabled"] = self.wave_switch_var.get()

    def toggle_ambient_light(self):
        """Переключает подсветку обложки"""
        self.config_data["ambient_light_enabled"] = self.ambient_switch_var.get()

    def toggle_auto_colors(self):
        """Переключает автоматические цвета"""
        self.config_data["auto_colors_enabled"] = self.auto_colors_switch_var.get()
        self.update_color_buttons_state()

    def update_color_buttons_state(self):
        """Обновляет состояние кнопок цветов в зависимости от режима автоматических цветов"""
        auto_enabled = self.config_data.get("auto_colors_enabled", False)
        
        for color_type, button in self.color_buttons:
            if auto_enabled:
                button.configure(state="disabled")
            else:
                button.configure(state="normal")

    def save_settings(self):
        """Сохраняет настройки"""
        try:
            success = config_manager.save_config(self.config_data)

            if success:
                # Обновляем конфигурацию на сервере
                self.update_server_config()
                
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