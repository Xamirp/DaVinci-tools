#!/usr/bin/env python3
"""
theme.py — Цветовая палитра и стили в духе DaVinci Resolve Studio (Dark Theme).
"""

import tkinter as tk
from tkinter import ttk

# Цветовая палитра DaVinci Resolve Studio
BG_DARK = "#202020"          # Основной фон окна
BG_PANEL = "#282828"         # Фон карточек и панелей
BG_HEADER = "#1c1c1c"        # Фон шапки и заголовков
BG_ENTRY = "#161616"         # Фон полей ввода и комбобоксов
BORDER_COLOR = "#3c3c3c"     # Границы панелей

TEXT_MAIN = "#e0e0e0"        # Основной текст
TEXT_MUTED = "#8e8e8e"       # Вторичный/пояснительный текст
TEXT_ACCENT = "#ff7043"      # DaVinci оранжевый акцент
TEXT_LINK = "#4fc3f7"        # Синий для кликабельных ссылок

BTN_BG = "#333333"           # Стандартная кнопка
BTN_HOVER = "#404040"        # Наведение на кнопку
BTN_ACTIVE = "#262626"       # Нажатие на кнопку

ACCENT_BLUE = "#1976d2"      # Акцентная кнопка (Запуск/Разметить)
ACCENT_BLUE_HOVER = "#2196f3"
ACCENT_GREEN = "#2e7d32"     # Успех
ACCENT_RED = "#c62828"       # Очистить / Ошибка


def apply_theme(root):
    """Применить темную тему DaVinci Resolve к окну и виджетам ttk."""
    root.configure(bg=BG_DARK)

    style = ttk.Style(root)
    # Используем базовую тему clam для гибкой кастомизации цветов
    try:
        style.theme_use("clam")
    except Exception:
        pass

    # 1. Общие стили фреймов и меток
    style.configure(".",
                    background=BG_DARK,
                    foreground=TEXT_MAIN,
                    font=("Segoe UI", 9))

    style.configure("TFrame", background=BG_DARK)
    style.configure("Panel.TFrame", background=BG_PANEL)

    style.configure("TLabel", background=BG_DARK, foreground=TEXT_MAIN)
    style.configure("Panel.TLabel", background=BG_PANEL, foreground=TEXT_MAIN)
    style.configure("Muted.TLabel", background=BG_PANEL, foreground=TEXT_MUTED, font=("Segoe UI", 8))
    style.configure("Section.TLabel", background=BG_PANEL, foreground=TEXT_ACCENT, font=("Segoe UI", 10, "bold"))
    style.configure("Title.TLabel", background=BG_HEADER, foreground=TEXT_MAIN, font=("Segoe UI", 11, "bold"))

    # 2. Кнопки
    style.configure("TButton",
                    background=BTN_BG,
                    foreground=TEXT_MAIN,
                    bordercolor=BORDER_COLOR,
                    lightcolor=BORDER_COLOR,
                    darkcolor=BORDER_COLOR,
                    padding=(10, 4),
                    font=("Segoe UI", 9))
    style.map("TButton",
              background=[("active", BTN_HOVER), ("pressed", BTN_ACTIVE), ("disabled", "#2a2a2a")],
              foreground=[("disabled", "#555555")])

    # Акцентная кнопка (Запуск)
    style.configure("Accent.TButton",
                    background=ACCENT_BLUE,
                    foreground="#ffffff",
                    bordercolor="#1565c0",
                    font=("Segoe UI", 9, "bold"))
    style.map("Accent.TButton",
              background=[("active", ACCENT_BLUE_HOVER), ("pressed", "#0d47a1"), ("disabled", "#2a2a2a")],
              foreground=[("disabled", "#555555")])

    # Кнопка Разметить (Зеленая)
    style.configure("Success.TButton",
                    background=ACCENT_GREEN,
                    foreground="#ffffff",
                    bordercolor="#1b5e20",
                    font=("Segoe UI", 9, "bold"))
    style.map("Success.TButton",
              background=[("active", "#388e3c"), ("pressed", "#1b5e20"), ("disabled", "#2a2a2a")],
              foreground=[("disabled", "#555555")])

    # Кнопка Очистить (Красная)
    style.configure("Danger.TButton",
                    background=ACCENT_RED,
                    foreground="#ffffff",
                    bordercolor="#b71c1c",
                    font=("Segoe UI", 9))
    style.map("Danger.TButton",
              background=[("active", "#d32f2f"), ("pressed", "#b71c1c"), ("disabled", "#2a2a2a")],
              foreground=[("disabled", "#555555")])

    # 3. Поля ввода и комбобоксы
    style.configure("TEntry",
                    fieldbackground=BG_ENTRY,
                    foreground=TEXT_MAIN,
                    insertcolor=TEXT_MAIN,
                    bordercolor=BORDER_COLOR,
                    padding=3)

    style.configure("TCombobox",
                    fieldbackground=BG_ENTRY,
                    background=BTN_BG,
                    foreground=TEXT_MAIN,
                    bordercolor=BORDER_COLOR,
                    padding=3)
    style.map("TCombobox",
              fieldbackground=[("readonly", BG_ENTRY)],
              selectbackground=[("readonly", "#1565c0")],
              selectforeground=[("readonly", "#ffffff")])

    style.configure("TSpinbox",
                    fieldbackground=BG_ENTRY,
                    background=BTN_BG,
                    foreground=TEXT_MAIN,
                    bordercolor=BORDER_COLOR,
                    padding=3)

    # 4. Checkbutton
    style.configure("TCheckbutton",
                    background=BG_PANEL,
                    foreground=TEXT_MAIN)
    style.map("TCheckbutton",
              background=[("active", BG_PANEL)])

    # 5. LabelFrame
    style.configure("TLabelframe",
                    background=BG_PANEL,
                    bordercolor=BORDER_COLOR,
                    darkcolor=BORDER_COLOR,
                    lightcolor=BORDER_COLOR)
    style.configure("TLabelframe.Label",
                    background=BG_PANEL,
                    foreground=TEXT_ACCENT,
                    font=("Segoe UI", 9, "bold"))

    # 6. Progressbar
    style.configure("Horizontal.TProgressbar",
                    troughcolor=BG_ENTRY,
                    background=ACCENT_BLUE,
                    bordercolor=BORDER_COLOR,
                    lightcolor=BORDER_COLOR,
                    darkcolor=BORDER_COLOR,
                    thickness=12)
