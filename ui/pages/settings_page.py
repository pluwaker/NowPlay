# ui/pages/settings_page.py
import customtkinter as ctk
<<<<<<< Updated upstream
from tkinter import messagebox
import tkinter
=======
from tkinter import colorchooser, messagebox
>>>>>>> Stashed changes
import sys
import os
import urllib.request
import urllib.error
import json
import threading
import colorsys

# Добавляем путь к корневой папке для импорта config_manager
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from config_manager import config_manager


class ModernColorPicker(ctk.CTkToplevel):
    """Современный виджет выбора цвета"""
    
    def __init__(self, parent, initial_color="#ffffff", callback=None):
        super().__init__(parent)
        self.callback = callback
        self.result = None
        
        # Парсим начальный цвет
        self.r, self.g, self.b = self.hex_to_rgb(initial_color)
        self.h, self.s, self.v = colorsys.rgb_to_hsv(self.r/255, self.g/255, self.b/255)
        
        self.title("Выбор цвета")
        self.geometry("500x400")
        self.configure(fg_color="#1e1e1e")
        self.resizable(False, False)
        
        # Центрируем окно
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - (500 // 2)
        y = (self.winfo_screenheight() // 2) - (400 // 2)
        self.geometry(f"500x550+{x}+{y}")
        
        self.create_widgets()
        
        # Блокируем родительское окно
        self.transient(parent)
        self.grab_set()
        
    def hex_to_rgb(self, hex_color):
        """Конвертирует hex в RGB"""
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    
    def rgb_to_hex(self, r, g, b):
        """Конвертирует RGB в hex"""
        return f"#{int(r):02x}{int(g):02x}{int(b):02x}"
    
    def create_widgets(self):
        """Создает виджеты выбора цвета"""
        # Основной контейнер
        main_frame = ctk.CTkFrame(self, fg_color="#2b2b2b", corner_radius=10)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Цветовой круг (цветовой тон)
        hue_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        hue_frame.pack(pady=(20, 10), padx=20, fill="x")
        
        ctk.CTkLabel(
            hue_frame,
            text="Цветовой тон",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#ffffff"
        ).pack(side="left")
        
        self.hue_slider = ctk.CTkSlider(
            hue_frame,
            from_=0,
            to=360,
            number_of_steps=360,
            command=self.update_hue,
            width=300
        )
        self.hue_slider.set(self.h * 360)
        self.hue_slider.pack(side="right", padx=10)
        
        # Насыщенность
        saturation_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        saturation_frame.pack(pady=10, padx=20, fill="x")
        
        ctk.CTkLabel(
            saturation_frame,
            text="Насыщенность",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#ffffff"
        ).pack(side="left")
        
        self.saturation_slider = ctk.CTkSlider(
            saturation_frame,
            from_=0,
            to=100,
            number_of_steps=100,
            command=self.update_saturation,
            width=300
        )
        self.saturation_slider.set(self.s * 100)
        self.saturation_slider.pack(side="right", padx=10)
        
        # Яркость
        brightness_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        brightness_frame.pack(pady=10, padx=20, fill="x")
        
        ctk.CTkLabel(
            brightness_frame,
            text="Яркость",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#ffffff"
        ).pack(side="left")
        
        self.brightness_slider = ctk.CTkSlider(
            brightness_frame,
            from_=0,
            to=100,
            number_of_steps=100,
            command=self.update_brightness,
            width=300
        )
        self.brightness_slider.set(self.v * 100)
        self.brightness_slider.pack(side="right", padx=10)
        
        # Превью цвета
        preview_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        preview_frame.pack(pady=20, padx=20, fill="x")
        
        ctk.CTkLabel(
            preview_frame,
            text="Предпросмотр:",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#ffffff"
        ).pack(side="left")
        
        self.color_preview = ctk.CTkFrame(
            preview_frame,
            width=100,
            height=50,
            corner_radius=5,
            fg_color=self.rgb_to_hex(self.r, self.g, self.b)
        )
        self.color_preview.pack(side="right", padx=10)
        
        # Hex код
        hex_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        hex_frame.pack(pady=10, padx=20, fill="x")
        
        ctk.CTkLabel(
            hex_frame,
            text="HEX:",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#ffffff"
        ).pack(side="left")
        
        self.hex_entry = ctk.CTkEntry(
            hex_frame,
            width=100,
            font=ctk.CTkFont(family="Consolas", size=12),
            fg_color="#1e1e1e",
            border_color="#555555"
        )
        self.hex_entry.insert(0, self.rgb_to_hex(self.r, self.g, self.b).upper())
        self.hex_entry.bind("<Return>", self.hex_entry_changed)
        self.hex_entry.pack(side="right", padx=10)
        
        # Быстрые цвета (предустановленные)
        presets_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        presets_frame.pack(pady=10, padx=20, fill="x")
        
        ctk.CTkLabel(
            presets_frame,
            text="Быстрый выбор:",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#ffffff"
        ).pack(side="left")
        
        presets_container = ctk.CTkFrame(presets_frame, fg_color="transparent")
        presets_container.pack(side="right", padx=10)
        
        preset_colors = [
            "#1db954", "#1ed760", "#ffffff", "#b3b3b3",
            "#ff0000", "#00ff00", "#0000ff", "#ffff00",
            "#ff00ff", "#00ffff", "#ffa500", "#800080"
        ]
        
        for i, color in enumerate(preset_colors):
            btn = ctk.CTkButton(
                presets_container,
                text="",
                width=30,
                height=30,
                fg_color=color,
                hover_color=color,
                command=lambda c=color: self.set_preset_color(c)
            )
            btn.grid(row=i // 4, column=i % 4, padx=2, pady=2)
        
        # Кнопки
        buttons_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        buttons_frame.pack(pady=20, padx=20, fill="x")
        
        cancel_btn = ctk.CTkButton(
            buttons_frame,
            text="Отмена",
            fg_color="#444444",
            hover_color="#555555",
            command=self.cancel,
            width=100
        )
        cancel_btn.pack(side="left", padx=5)
        
        ok_btn = ctk.CTkButton(
            buttons_frame,
            text="ОК",
            fg_color="#1db954",
            hover_color="#1aa34a",
            command=self.ok,
            width=100
        )
        ok_btn.pack(side="right", padx=5)
    
    def update_hue(self, value):
        """Обновляет цветовой тон"""
        self.h = float(value) / 360
        self.update_color()
    
    def update_saturation(self, value):
        """Обновляет насыщенность"""
        self.s = float(value) / 100
        self.update_color()
    
    def update_brightness(self, value):
        """Обновляет яркость"""
        self.v = float(value) / 100
        self.update_color()
    
    def update_color(self):
        """Обновляет цвет на основе HSV"""
        self.r, self.g, self.b = colorsys.hsv_to_rgb(self.h, self.s, self.v)
        self.r = int(self.r * 255)
        self.g = int(self.g * 255)
        self.b = int(self.b * 255)
        
        hex_color = self.rgb_to_hex(self.r, self.g, self.b)
        self.color_preview.configure(fg_color=hex_color)
        self.hex_entry.delete(0, tkinter.END)
        self.hex_entry.insert(0, hex_color.upper())
    
    def hex_entry_changed(self, event=None):
        """Обработка изменения hex кода"""
        try:
            hex_color = self.hex_entry.get().strip()
            if not hex_color.startswith('#'):
                hex_color = '#' + hex_color
            if len(hex_color) == 7:
                self.r, self.g, self.b = self.hex_to_rgb(hex_color)
                self.h, self.s, self.v = colorsys.rgb_to_hsv(self.r/255, self.g/255, self.b/255)
                
                self.hue_slider.set(self.h * 360)
                self.saturation_slider.set(self.s * 100)
                self.brightness_slider.set(self.v * 100)
                
                self.color_preview.configure(fg_color=hex_color)
        except:
            pass
    
    def set_preset_color(self, hex_color):
        """Устанавливает предустановленный цвет"""
        self.r, self.g, self.b = self.hex_to_rgb(hex_color)
        self.h, self.s, self.v = colorsys.rgb_to_hsv(self.r/255, self.g/255, self.b/255)
        
        self.hue_slider.set(self.h * 360)
        self.saturation_slider.set(self.s * 100)
        self.brightness_slider.set(self.v * 100)
        
        self.color_preview.configure(fg_color=hex_color)
        self.hex_entry.delete(0, tkinter.END)
        self.hex_entry.insert(0, hex_color.upper())
    
    def ok(self):
        """Подтверждение выбора"""
        hex_color = self.rgb_to_hex(self.r, self.g, self.b)
        self.result = hex_color
        if self.callback:
            self.callback(hex_color)
        self.destroy()
    
    def cancel(self):
        """Отмена выбора"""
        self.result = None
        self.destroy()


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

        # ========== ОТДЕЛ 1: Автоматические цвета ==========
        self.auto_colors_frame = ctk.CTkFrame(self.scrollable_frame, fg_color="#2b2b2b", corner_radius=10)
        self.auto_colors_frame.pack(pady=(0, 15), padx=30, fill="x")

        auto_colors_switch_frame = ctk.CTkFrame(self.auto_colors_frame, fg_color="transparent")
        auto_colors_switch_frame.pack(fill="x", padx=20, pady=15)

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

        # ========== ОТДЕЛ 1.5: Эффект стекла ==========
        self.glass_effect_frame = ctk.CTkFrame(self.scrollable_frame, fg_color="#2b2b2b", corner_radius=10)
        self.glass_effect_frame.pack(pady=(0, 15), padx=30, fill="x")

        glass_effect_switch_frame = ctk.CTkFrame(self.glass_effect_frame, fg_color="transparent")
        glass_effect_switch_frame.pack(fill="x", padx=20, pady=(15, 10))

        ctk.CTkLabel(
            glass_effect_switch_frame,
            text="Эффект стекла (Glassmorphism)",
            font=ctk.CTkFont(size=14),
            text_color="#cccccc"
        ).pack(side="left")

        self.glass_effect_switch_var = ctk.BooleanVar(value=self.config_data.get("glass_effect_enabled", False))
        self.glass_effect_switch = ctk.CTkSwitch(
            glass_effect_switch_frame,
            text="",
            variable=self.glass_effect_switch_var,
            command=self.toggle_glass_effect
        )
        self.glass_effect_switch.pack(side="right")

        # Выбор типа эффекта стекла (темное/белое)
        glass_type_frame = ctk.CTkFrame(self.glass_effect_frame, fg_color="transparent")
        glass_type_frame.pack(fill="x", padx=20, pady=(0, 15))

        ctk.CTkLabel(
            glass_type_frame,
            text="Тип эффекта",
            font=ctk.CTkFont(size=14),
            text_color="#cccccc"
        ).pack(side="left")

        glass_effect_type_value = self.config_data.get("glass_effect_type", "dark")
        glass_type_display_map = {
            "dark": "Темное",
            "light": "Белое"
        }
        self.glass_effect_type_var = ctk.StringVar(
            value=glass_type_display_map.get(glass_effect_type_value, "Темное")
        )
        self.glass_effect_type_menu = ctk.CTkOptionMenu(
            glass_type_frame,
            values=["Темное", "Белое"],
            variable=self.glass_effect_type_var,
            command=self.change_glass_effect_type,
            width=150
        )
        self.glass_effect_type_menu.pack(side="right")

        # Обновляем состояние меню в зависимости от включенности эффекта
        self.update_glass_effect_menu_state()

        # ========== ОТДЕЛ 2: Цвет подложки ==========
        self.background_color_frame = ctk.CTkFrame(self.scrollable_frame, fg_color="#2b2b2b", corner_radius=10)
        self.background_color_frame.pack(pady=(0, 15), padx=30, fill="x")

        color_main_frame = ctk.CTkFrame(self.background_color_frame, fg_color="transparent")
        color_main_frame.pack(fill="x", padx=20, pady=15)

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

        # ========== ОТДЕЛ 3: Цвета названия трека и исполнителя ==========
        self.text_colors_frame = ctk.CTkFrame(self.scrollable_frame, fg_color="#2b2b2b", corner_radius=10)
        self.text_colors_frame.pack(pady=(0, 15), padx=30, fill="x")

        # Цвет названия трека
        color_text_frame = ctk.CTkFrame(self.text_colors_frame, fg_color="transparent")
        color_text_frame.pack(fill="x", padx=20, pady=(15, 10))

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
        color_artist_frame = ctk.CTkFrame(self.text_colors_frame, fg_color="transparent")
        color_artist_frame.pack(fill="x", padx=20, pady=(0, 15))

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

        # ========== ОТДЕЛ 4: Цвет волны и акцентный цвет ==========
        self.wave_colors_frame = ctk.CTkFrame(self.scrollable_frame, fg_color="#2b2b2b", corner_radius=10)
        self.wave_colors_frame.pack(pady=(0, 15), padx=30, fill="x")

        # Цвет волны
        color_wave_frame = ctk.CTkFrame(self.wave_colors_frame, fg_color="transparent")
        color_wave_frame.pack(fill="x", padx=20, pady=(15, 10))

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

        # Акцентный цвет
        color_accent_frame = ctk.CTkFrame(self.wave_colors_frame, fg_color="transparent")
        color_accent_frame.pack(fill="x", padx=20, pady=(0, 15))

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

        # ========== ОТДЕЛ 5: Цвет прогресс-бара ==========
        self.progress_colors_frame = ctk.CTkFrame(self.scrollable_frame, fg_color="#2b2b2b", corner_radius=10)
        self.progress_colors_frame.pack(pady=(0, 15), padx=30, fill="x")

        # Задний фон прогресс-бара
        color_progress1_frame = ctk.CTkFrame(self.progress_colors_frame, fg_color="transparent")
        color_progress1_frame.pack(fill="x", padx=20, pady=(15, 10))

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

        # Цвет прогресс-бара
        color_progress2_frame = ctk.CTkFrame(self.progress_colors_frame, fg_color="transparent")
        color_progress2_frame.pack(fill="x", padx=20, pady=(0, 15))

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

        # ========== ОТДЕЛ 6: Переключатели ==========
        self.switches_frame = ctk.CTkFrame(self.scrollable_frame, fg_color="#2b2b2b", corner_radius=10)
        self.switches_frame.pack(pady=(0, 15), padx=30, fill="x")

        # Подсветка обложки
        ambient_switch_frame = ctk.CTkFrame(self.switches_frame, fg_color="transparent")
        ambient_switch_frame.pack(fill="x", padx=20, pady=(15, 10))

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

        # Волна
        wave_switch_frame = ctk.CTkFrame(self.switches_frame, fg_color="transparent")
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

        # ========== Дополнительные настройки ==========
        # Выбор источника медиа
        source_frame = ctk.CTkFrame(self.scrollable_frame, fg_color="#2b2b2b", corner_radius=10)
        source_frame.pack(pady=(0, 15), padx=30, fill="x")

        source_label_frame = ctk.CTkFrame(source_frame, fg_color="transparent")
        source_label_frame.pack(fill="x", padx=20, pady=(15, 10))

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

        source_menu_frame = ctk.CTkFrame(source_frame, fg_color="transparent")
        source_menu_frame.pack(fill="x", padx=20, pady=(0, 15))

        self.source_menu = ctk.CTkOptionMenu(
            source_menu_frame,
            values=["Автоматически"],
            variable=self.source_var,
            command=self.change_source,
            width=200
        )
        self.source_menu.pack(side="left", padx=(0, 10))

        self.source_display_label = ctk.CTkLabel(
            source_menu_frame,
            text="(Загрузка...)",
            font=ctk.CTkFont(size=11),
            text_color="#888888"
        )
        self.source_display_label.pack(side="left")

        # Инициализируем список источников
        self.sources_map = {}  # id -> name
        self.refresh_sources()

        # Изменение позиции
        position_frame = ctk.CTkFrame(self.scrollable_frame, fg_color="#2b2b2b", corner_radius=10)
        position_frame.pack(pady=(0, 15), padx=30, fill="x")

        position_content_frame = ctk.CTkFrame(position_frame, fg_color="transparent")
        position_content_frame.pack(fill="x", padx=20, pady=15)

        ctk.CTkLabel(
            position_content_frame,
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
            position_content_frame,
            values=list(positions.keys()),
            variable=self.position_var,
            command=self.change_position
        )
        self.position_menu.pack(side="right")

        self.positions_map = positions  # сохраним для доступа при сохранении


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
        
        # Автоматическое сохранение
        self.auto_save_settings()
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
            # Автоматическое сохранение
            self.auto_save_settings()
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
        
        def on_color_selected(color_code):
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
                
                # Автоматическое сохранение
                self.auto_save_settings()
        
        # Открываем современный выбор цвета
        color_picker = ModernColorPicker(self, initial_color=current_color, callback=on_color_selected)
        self.wait_window(color_picker)

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
        # Автоматическое сохранение
        self.auto_save_settings()

    def toggle_ambient_light(self):
        """Переключает подсветку обложки"""
        self.config_data["ambient_light_enabled"] = self.ambient_switch_var.get()
        # Автоматическое сохранение
        self.auto_save_settings()

    def toggle_auto_colors(self):
        """Переключает автоматические цвета"""
        self.config_data["auto_colors_enabled"] = self.auto_colors_switch_var.get()
        self.update_color_buttons_state()
        # Автоматическое сохранение
        self.auto_save_settings()

    def toggle_glass_effect(self):
        """Переключает эффект стекла"""
        self.config_data["glass_effect_enabled"] = self.glass_effect_switch_var.get()
        self.update_glass_effect_menu_state()
        # Автоматическое сохранение
        self.auto_save_settings()

    def change_glass_effect_type(self, choice):
        """Изменяет тип эффекта стекла"""
        glass_type_map = {
            "Темное": "dark",
            "Белое": "light"
        }
        self.config_data["glass_effect_type"] = glass_type_map.get(choice, "dark")
        # Автоматическое сохранение
        self.auto_save_settings()

    def update_glass_effect_menu_state(self):
        """Обновляет состояние меню выбора типа эффекта стекла"""
        is_enabled = self.config_data.get("glass_effect_enabled", False)
        if is_enabled:
            self.glass_effect_type_menu.configure(state="normal")
        else:
            self.glass_effect_type_menu.configure(state="disabled")

    def update_color_buttons_state(self):
        """Обновляет состояние кнопок цветов в зависимости от режима автоматических цветов"""
        auto_enabled = self.config_data.get("auto_colors_enabled", False)
        
        # Управляем состоянием кнопок и видимостью секций
        for color_type, button in self.color_buttons:
            if auto_enabled:
                button.configure(state="disabled")
            else:
                button.configure(state="normal")
        
        # Скрываем/показываем секции с настройками цветов
        if auto_enabled:
            self.background_color_frame.pack_forget()
            self.text_colors_frame.pack_forget()
            self.wave_colors_frame.pack_forget()
            self.progress_colors_frame.pack_forget()
        else:
            # Показываем секции в правильном порядке
            # Проверяем, скрыты ли они, и показываем если нужно
            try:
                # Проверяем, есть ли pack_info (если нет - виджет скрыт)
                self.background_color_frame.pack_info()
            except:
                self.background_color_frame.pack(pady=(0, 15), padx=30, fill="x")
            
            try:
                self.text_colors_frame.pack_info()
            except:
                self.text_colors_frame.pack(pady=(0, 15), padx=30, fill="x")
            
            try:
                self.wave_colors_frame.pack_info()
            except:
                self.wave_colors_frame.pack(pady=(0, 15), padx=30, fill="x")
            
            try:
                self.progress_colors_frame.pack_info()
            except:
                self.progress_colors_frame.pack(pady=(0, 15), padx=30, fill="x")

    def auto_save_settings(self):
        """Автоматически сохраняет настройки без уведомлений"""
        try:
            success = config_manager.save_config(self.config_data)
            
            if success:
                # Обновляем конфигурацию на сервере
                self.update_server_config()
                
                # УВЕДОМЛЯЕМ СЕРВЕР ОБ ИЗМЕНЕНИИ НАСТРОЕК
                if hasattr(self.controller, 'config_updated'):
                    self.controller.config_updated(self.config_data)
        except Exception as e:
            # Тихая ошибка - не показываем пользователю при каждом изменении
            print(f"⚠️ Не удалось автоматически сохранить настройки: {e}")

    def copy_url(self):
        """Копирует URL в буфер обмена"""
        url = self.controller.obs_link.get()
        if url:
            self.clipboard_clear()
            self.clipboard_append(url)
            messagebox.showinfo("Успех", "Ссылка скопирована в буфер обмена!")