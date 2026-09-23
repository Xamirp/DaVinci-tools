#!/usr/bin/env python3
"""
panels.py — Модульные изолированные панели интерфейса (PanelBase, HeaderPanel, SettingsPanel, ResultsPanel, ActionsPanel).
"""

import os
import tkinter as tk
from tkinter import ttk
from pathlib import Path
from .theme import BG_PANEL, BG_HEADER, TEXT_MAIN, TEXT_MUTED, TEXT_ACCENT, BORDER_COLOR

MARKER_COLORS = ["Red", "Blue", "Green", "Yellow", "Pink", "Fuchsia",
                 "Lavender", "Cyan", "Cream", "Sand", "Mint", "Pear"]
MARKER_TARGETS = ["clip", "timeline"]

# Человекочитаемые пресеты частоты для видеомонтажера
FREQUENCY_MAP = [
    ("Каждые 4 такта (Редкий / Панорамы)", -2),
    ("Каждые 2 такта (Умеренный)", -1),
    ("Каждый такт (По умолчанию / Стандарт)", 0),
    ("Каждые 1/2 такта (Динамичный / Драйв)", 1),
    ("Каждый бит / удар (Экшен / Максимум)", 2),
]
LABEL_TO_FREQ = {label: val for label, val in FREQUENCY_MAP}
FREQ_TO_LABEL = {val: label for label, val in FREQUENCY_MAP}


class PanelBase(ttk.Frame):
    """Базовый класс для изолированной панели с перехватом событий мыши и клавиатуры."""
    def __init__(self, parent, title="", padding=8, **kwargs):
        super().__init__(parent, style="Panel.TFrame", padding=padding, **kwargs)
        self.title = title
        self._is_hovered = False
        self._has_focus = False

        if title:
            header_row = ttk.Frame(self, style="Panel.TFrame")
            header_row.pack(fill="x", pady=(0, 6))
            ttk.Label(header_row, text=title, style="Section.TLabel").pack(side="left")
            ttk.Separator(header_row, orient="horizontal").pack(side="left", fill="x", expand=True, padx=(8, 0))

        # Перехват событий мыши для панели
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        self.bind("<FocusIn>", self._on_focus_in)
        self.bind("<FocusOut>", self._on_focus_out)

    def _on_enter(self, event):
        self._is_hovered = True

    def _on_leave(self, event):
        self._is_hovered = False

    def _on_focus_in(self, event):
        self._has_focus = True

    def _on_focus_out(self, event):
        self._has_focus = False


class HeaderPanel(PanelBase):
    """Информационная панель: статус DaVinci, активный проект, файл на дорожке A2."""
    def __init__(self, parent, on_refresh=None):
        super().__init__(parent, title="Проект и Аудиотрек")
        self.on_refresh = on_refresh

        # Статус DaVinci + Проект
        row1 = ttk.Frame(self, style="Panel.TFrame")
        row1.pack(fill="x", pady=2)

        self.lbl_davinci_status = ttk.Label(row1, text="🟢 DaVinci Подключен", font=("Segoe UI", 9, "bold"), style="Panel.TLabel")
        self.lbl_davinci_status.pack(side="left")

        self.lbl_project_name = ttk.Label(row1, text="| Проект: —", style="Panel.TLabel")
        self.lbl_project_name.pack(side="left", padx=(8, 0))

        if on_refresh:
            ttk.Button(row1, text="Обновить", command=on_refresh, width=9).pack(side="right")

        # Информация об аудиодорожке
        row2 = ttk.Frame(self, style="Panel.TFrame")
        row2.pack(fill="x", pady=(4, 2))

        ttk.Label(row2, text="🎵 Аудиоклип на треке:", width=20, style="Panel.TLabel").pack(side="left")
        self.lbl_audio_info = ttk.Label(row2, text="Определение аудио...", foreground="#4fc3f7", font=("Segoe UI", 9, "bold"), style="Panel.TLabel")
        self.lbl_audio_info.pack(side="left")

        # Папка сессии / Файл битов
        row3 = ttk.Frame(self, style="Panel.TFrame")
        row3.pack(fill="x", pady=2)
        ttk.Label(row3, text="📁 Файл битов (JSON):", width=20, style="Muted.TLabel").pack(side="left")
        self.lbl_target_path = ttk.Label(row3, text="—", style="Muted.TLabel")
        self.lbl_target_path.pack(side="left")

    def update_info(self, is_connected, project_name="", audio_info=None, target_path=""):
        if is_connected:
            self.lbl_davinci_status.config(text="🟢 DaVinci Resolve", foreground="#4caf50")
            self.lbl_project_name.config(text=f"| Проект: {project_name or '—'}")
        else:
            self.lbl_davinci_status.config(text="🔴 DaVinci не запущен", foreground="#ef5350")
            self.lbl_project_name.config(text="| Проект: нет подключения")

        if audio_info and audio_info.get("found"):
            fn = audio_info.get("file_name", "—")
            dur = audio_info.get("duration_sec", 0)
            mins = int(dur // 60)
            secs = int(dur % 60)
            if audio_info.get("is_complex"):
                label_txt = audio_info.get("status_label", fn)
                self.lbl_audio_info.config(text=f"🎛️ {label_txt} ({mins}:{secs:02d})", foreground="#ffb74d")
            else:
                self.lbl_audio_info.config(text=f"🎵 {fn} ({mins}:{secs:02d})", foreground="#4fc3f7")
        elif audio_info:
            msg = audio_info.get("message", "Файл не найден")
            self.lbl_audio_info.config(text=f"⚠️ {msg}", foreground="#ef5350")
        else:
            self.lbl_audio_info.config(text="—", foreground=TEXT_MUTED)

        if target_path:
            self.lbl_target_path.config(text=str(target_path))


class SettingsPanel(PanelBase):
    """Компактная панель настроек детекции и маркеров."""
    def __init__(self, parent, on_change=None, on_open_adaptive=None):
        super().__init__(parent, title="Параметры детекции и разметки")
        self.on_change = on_change
        self.on_open_adaptive = on_open_adaptive

        # Строка 1: Таймлайн и Индекс аудиотрека
        r1 = ttk.Frame(self, style="Panel.TFrame")
        r1.pack(fill="x", pady=3)

        ttk.Label(r1, text="Таймлайн:", width=14, style="Panel.TLabel").pack(side="left")
        self.var_timeline = tk.StringVar(value="intro")
        self.cb_timeline = ttk.Combobox(r1, textvariable=self.var_timeline, state="readonly", width=18)
        self.cb_timeline.pack(side="left", padx=(0, 16))
        self.cb_timeline.bind("<<ComboboxSelected>>", self._trigger_change)

        ttk.Label(r1, text="Аудиотрек:", width=10, style="Panel.TLabel").pack(side="left")
        self.var_track_index = tk.IntVar(value=2)
        sb_track = ttk.Spinbox(r1, from_=1, to=20, textvariable=self.var_track_index, width=5, command=self._trigger_change)
        sb_track.pack(side="left")
        sb_track.bind("<KeyRelease>", self._trigger_change)
        ttk.Label(r1, text="(по умолч. A2)", style="Muted.TLabel").pack(side="left", padx=4)

        # Строка 2: Частота маркеров (Плотность склеек), Цвет, Таргет
        r2 = ttk.Frame(self, style="Panel.TFrame")
        r2.pack(fill="x", pady=3)

        ttk.Label(r2, text="Плотность склеек:", width=16, style="Panel.TLabel").pack(side="left")
        self.var_frequency_label = tk.StringVar(value=FREQ_TO_LABEL[0])
        self.cb_frequency = ttk.Combobox(
            r2,
            textvariable=self.var_frequency_label,
            values=[label for label, _ in FREQUENCY_MAP],
            state="readonly",
            width=33
        )
        self.cb_frequency.pack(side="left", padx=(0, 14))
        self.cb_frequency.bind("<<ComboboxSelected>>", self._on_frequency_selected)

        ttk.Label(r2, text="Цвет:", width=5, style="Panel.TLabel").pack(side="left")
        self.var_color = tk.StringVar(value="Red")
        cb_color = ttk.Combobox(r2, textvariable=self.var_color, values=MARKER_COLORS, state="readonly", width=8)
        cb_color.pack(side="left", padx=(0, 10))

        ttk.Label(r2, text="Таргет:", width=6, style="Panel.TLabel").pack(side="left")
        self.var_target = tk.StringVar(value="clip")
        self.cb_target = ttk.Combobox(r2, textvariable=self.var_target, values=MARKER_TARGETS, state="readonly", width=8)
        self.cb_target.pack(side="left")
        self.lbl_target_hint = ttk.Label(r2, text="", font=("Segoe UI", 8), style="Muted.TLabel")
        self.lbl_target_hint.pack(side="left", padx=(6, 0))

        # Строка 2.5: Динамический калькулятор темпа монтажа (Live Pace Indicator)
        r_pace = ttk.Frame(self, style="Panel.TFrame")
        r_pace.pack(fill="x", pady=(2, 4))
        self.lbl_pace_info = ttk.Label(
            r_pace,
            text="⏱️ Длина клипа: ~2.04с (49 кадров)  |  📊 Ожидаемо: ~81 клип",
            foreground="#4fc3f7",
            font=("Segoe UI", 8, "bold"),
            style="Panel.TLabel"
        )
        self.lbl_pace_info.pack(side="left", padx=(4, 0))

        # Строка 3: Адаптивный режим
        r3 = ttk.Frame(self, style="Panel.TFrame")
        r3.pack(fill="x", pady=(6, 2))

        self.var_adaptive = tk.BooleanVar(value=False)
        chk_adapt = ttk.Checkbutton(r3, text="Адаптивный режим", variable=self.var_adaptive, command=self._on_adaptive_toggle)
        chk_adapt.pack(side="left")

        self.lbl_adapt_status = ttk.Label(r3, text="[ ВЫКЛ ]", foreground="#888888", font=("Segoe UI", 8, "bold"), style="Panel.TLabel")
        self.lbl_adapt_status.pack(side="left", padx=(8, 12))

        self.btn_adapt_config = ttk.Button(r3, text="Настроить...", command=self._on_click_adaptive, width=12)
        self.btn_adapt_config.pack(side="left")
        self._update_adaptive_view()

    def _trigger_change(self, event=None):
        if self.on_change:
            self.on_change()

    def _on_adaptive_toggle(self):
        self._update_adaptive_view()
        self._trigger_change()

    def _update_adaptive_view(self):
        if self.var_adaptive.get():
            self.lbl_adapt_status.config(text="[ ВКЛ ]", foreground="#4caf50")
            self.btn_adapt_config.config(state="normal")
        else:
            self.lbl_adapt_status.config(text="[ ВЫКЛ ]", foreground="#888888")
            self.btn_adapt_config.config(state="disabled")

    def _on_click_adaptive(self):
        if self.on_open_adaptive:
            self.on_open_adaptive()

    def _on_frequency_selected(self, event=None):
        self.update_pace_estimate()
        self._trigger_change()

    def get_frequency_value(self):
        """Вернуть целочисленное значение frequency (-2..2) для бэкенда."""
        lbl = self.var_frequency_label.get()
        return LABEL_TO_FREQ.get(lbl, 0)

    def set_frequency_value(self, val):
        """Установить текстовый пресет по целочисленному значению."""
        lbl = FREQ_TO_LABEL.get(val, FREQUENCY_MAP[2][0])
        self.var_frequency_label.set(lbl)
        self.update_pace_estimate()

    def update_pace_estimate(self, bpm=None, audio_duration_sec=None, timeline_fps=None):
        """Динамический пересчет и отображение примерного хронометража клипа и числа склеек."""
        if bpm is not None:
            self._cached_bpm = float(bpm)
        if audio_duration_sec is not None:
            self._cached_audio_dur = float(audio_duration_sec)
        if timeline_fps is not None:
            self._cached_fps = float(timeline_fps)

        cur_bpm = getattr(self, "_cached_bpm", 117.5) or 117.5
        cur_dur = getattr(self, "_cached_audio_dur", 165.3) or 165.3
        cur_fps = getattr(self, "_cached_fps", 23.976) or 23.976

        freq = self.get_frequency_value()
        # Длительность одного такта в 4/4 = 4 * (60 / bpm)
        bar_dur = 4.0 * (60.0 / cur_bpm)
        clip_dur = bar_dur * (2.0 ** -freq)
        frames = int(round(clip_dur * cur_fps))
        expected_clips = int(round(cur_dur / clip_dur)) if clip_dur > 0 else 0

        self.lbl_pace_info.config(
            text=f"⏱️ Длина клипа: ~{clip_dur:.2f}с ({frames} кадров)  |  📊 Ожидаемо склеек: ~{expected_clips} клипов (при {cur_bpm:.1f} BPM)"
        )

    def set_target_mode(self, is_complex=False):
        """Блокировка режима 'clip' для сложного монтажа во избежание сбоев DaVinci."""
        if is_complex:
            self.var_target.set("timeline")
            self.cb_target.config(state="disabled")
            self.lbl_target_hint.config(text="🔒 Только Timeline (монтаж аудио)", foreground="#ffb74d")
        else:
            self.cb_target.config(state="readonly")
            self.lbl_target_hint.config(text="", foreground=TEXT_MUTED)


class ResultsPanel(PanelBase):
    """Панель результатов анализа музыки."""
    def __init__(self, parent):
        super().__init__(parent, title="Результаты аудиоанализа")

        cards_frame = ttk.Frame(self, style="Panel.TFrame")
        cards_frame.pack(fill="x", pady=2)

        self.cards = {}
        metrics = [
            ("bpm", "Темп (BPM)"),
            ("signature", "Размер"),
            ("total_beats", "Всего битов"),
            ("strong_beats", "Сильных долей"),
            ("markers", "Маркеров"),
        ]

        for key, title in metrics:
            c = ttk.Frame(cards_frame, style="Panel.TFrame", padding=(8, 4))
            c.pack(side="left", fill="both", expand=True, padx=2)
            ttk.Label(c, text=title, style="Muted.TLabel").pack(anchor="center")
            val_lbl = ttk.Label(c, text="—", font=("Segoe UI", 12, "bold"), foreground="#4fc3f7", style="Panel.TLabel")
            val_lbl.pack(anchor="center", pady=(2, 0))
            self.cards[key] = val_lbl

    def update_results(self, res):
        if not res:
            for lbl in self.cards.values():
                lbl.config(text="—", foreground=TEXT_MUTED)
            return

        bpm = res.get("tempo", 0)
        self.cards["bpm"].config(text=f"{bpm:.1f}", foreground="#ffffff")
        self.cards["signature"].config(text=str(res.get("time_signature", "4/4")), foreground="#ffffff")
        self.cards["total_beats"].config(text=str(res.get("total_beats", 0)), foreground="#ffffff")

        strong_len = len(res.get("strong_beat_frames", []))
        self.cards["strong_beats"].config(text=str(strong_len), foreground="#ffb74d")

        markers = res.get("markers_placed", 0)
        self.cards["markers"].config(text=str(markers), foreground="#4caf50" if markers > 0 else TEXT_MUTED)


class ActionsPanel(PanelBase):
    """Панель управляющих действий двухфазного жизненного цикла."""
    def __init__(self, parent, on_analyze=None, on_save_json=None, on_export_xml=None, on_place_markers=None,
                 on_clear_markers=None, on_save_settings=None, on_undo=None, on_view_log=None):
        super().__init__(parent, title="Действия")

        # Основные кнопки процесса
        row1 = ttk.Frame(self, style="Panel.TFrame")
        row1.pack(fill="x", pady=(2, 6))

        # Шаг 1: Запуск детекции
        self.btn_analyze = ttk.Button(row1, text="⚡ Запуск (Анализ)", style="Accent.TButton", command=on_analyze, takefocus=False)
        self.btn_analyze.pack(side="left", padx=(0, 8))

        # Шаг 2: Разметить на таймлайне
        self.btn_place = ttk.Button(row1, text="📍 Разметить в DaVinci", style="Success.TButton", command=on_place_markers, state="disabled", takefocus=False)
        self.btn_place.pack(side="left", padx=(0, 8))

        # Шаг 3: Очистить маркеры
        self.btn_clear = ttk.Button(row1, text="🗑 Очистить маркеры", style="Danger.TButton", command=on_clear_markers, takefocus=False)
        self.btn_clear.pack(side="left")

        # Экспорт FCP XML и сохранение в JSON (справа)
        self.btn_save_json = ttk.Button(row1, text="💾 Сохранить в JSON", command=on_save_json, state="disabled", takefocus=False)
        self.btn_save_json.pack(side="right")

        self.btn_export_xml = ttk.Button(row1, text="🎬 Экспорт FCP XML", command=on_export_xml, state="disabled", takefocus=False)
        self.btn_export_xml.pack(side="right", padx=(0, 6))

        # Вспомогательные кнопки
        row2 = ttk.Frame(self, style="Panel.TFrame")
        row2.pack(fill="x", pady=2)

        self.btn_save = ttk.Button(row2, text="Сохранить настройки", command=on_save_settings, takefocus=False)
        self.btn_save.pack(side="left", padx=(0, 8))

        self.btn_undo = ttk.Button(row2, text="↩ Отмена (Undo)", command=on_undo, state="disabled", takefocus=False)
        self.btn_undo.pack(side="left", padx=(0, 8))

        self.btn_log = ttk.Button(row2, text="📋 Просмотр лога", command=on_view_log, takefocus=False)
        self.btn_log.pack(side="left")

        self.lbl_status = ttk.Label(row2, text="Готов к анализу", style="Panel.TLabel")
        self.lbl_status.pack(side="right")

    def set_status(self, text, color=TEXT_MAIN):
        self.lbl_status.config(text=text, foreground=color)

    def set_can_save_json(self, can_save):
        self.btn_save_json.config(state="normal" if can_save else "disabled")

    def set_can_export_xml(self, can_export):
        self.btn_export_xml.config(state="normal" if can_export else "disabled")

    def set_can_place(self, can_place):
        self.btn_place.config(state="normal" if can_place else "disabled")

    def set_can_undo(self, can_undo):
        self.btn_undo.config(state="normal" if can_undo else "disabled")

