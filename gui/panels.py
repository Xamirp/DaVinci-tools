#!/usr/bin/env python3
"""
panels.py — Модульные изолированные панели интерфейса (PanelBase, HeaderPanel, SettingsPanel, ResultsPanel, ActionsPanel).
Локализовано через i18n (EN / UK / RU).
"""

import os
import tkinter as tk
from tkinter import ttk
from pathlib import Path
from .theme import BG_PANEL, BG_HEADER, TEXT_MAIN, TEXT_MUTED, TEXT_ACCENT, BORDER_COLOR
from .i18n import tr, get_current_language, set_language, LANGUAGES, register_language_listener

MARKER_COLORS = ["Red", "Blue", "Green", "Yellow", "Pink", "Fuchsia",
                 "Lavender", "Cyan", "Cream", "Sand", "Mint", "Pear"]
MARKER_TARGETS = ["clip", "timeline"]


def get_frequency_map():
    return [
        (tr("density_preset_m2"), -2),
        (tr("density_preset_m1"), -1),
        (tr("density_preset_0"), 0),
        (tr("density_preset_1"), 1),
        (tr("density_preset_2"), 2),
    ]


class PanelBase(ttk.Frame):
    """Базовый класс для изолированной панели с перехватом событий мыши и клавиатуры."""
    def __init__(self, parent, title_key="", padding=8, **kwargs):
        super().__init__(parent, style="Panel.TFrame", padding=padding, **kwargs)
        self.title_key = title_key
        self._is_hovered = False
        self._has_focus = False

        if title_key:
            self.header_row = ttk.Frame(self, style="Panel.TFrame")
            self.header_row.pack(fill="x", pady=(0, 6))
            self.title_lbl = ttk.Label(self.header_row, text=tr(title_key), style="Section.TLabel")
            self.title_lbl.pack(side="left")
            ttk.Separator(self.header_row, orient="horizontal").pack(side="left", fill="x", expand=True, padx=(8, 0))

        # Перехват событий мыши для панели
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        self.bind("<FocusIn>", self._on_focus_in)
        self.bind("<FocusOut>", self._on_focus_out)

    def update_locale(self):
        if hasattr(self, "title_lbl") and self.title_key:
            self.title_lbl.config(text=tr(self.title_key))

    def _on_enter(self, event):
        self._is_hovered = True

    def _on_leave(self, event):
        self._is_hovered = False

    def _on_focus_in(self, event):
        self._has_focus = True

    def _on_focus_out(self, event):
        self._has_focus = False


class HeaderPanel(PanelBase):
    """Информационная панель: статус DaVinci, активный проект, файл на дорожке A2, переключатель языка."""
    def __init__(self, parent, on_refresh=None, on_language_change=None):
        super().__init__(parent, title_key="header_title")
        self.on_refresh = on_refresh
        self.on_language_change = on_language_change
        self._last_status = (False, "", None, "")

        # Статус DaVinci + Проект + Языковой переключатель
        row1 = ttk.Frame(self, style="Panel.TFrame")
        row1.pack(fill="x", pady=2)

        self.lbl_davinci_status = ttk.Label(row1, text="🟢 " + tr("status_connected"), font=("Segoe UI", 9, "bold"), style="Panel.TLabel")
        self.lbl_davinci_status.pack(side="left")

        self.lbl_project_name = ttk.Label(row1, text=f"| {tr('project_prefix')} —", style="Panel.TLabel")
        self.lbl_project_name.pack(side="left", padx=(8, 0))

        # Языковой переключатель справа
        lang_frame = ttk.Frame(row1, style="Panel.TFrame")
        lang_frame.pack(side="right")

        ttk.Label(lang_frame, text="🌐", style="Panel.TLabel").pack(side="left", padx=(0, 2))
        self.var_language = tk.StringVar(value=get_current_language().upper())
        self.cb_language = ttk.Combobox(
            lang_frame,
            textvariable=self.var_language,
            values=["EN", "UK", "RU"],
            state="readonly",
            width=4
        )
        self.cb_language.pack(side="left", padx=(0, 6))
        self.cb_language.bind("<<ComboboxSelected>>", self._on_lang_selected)

        if on_refresh:
            self.btn_refresh = ttk.Button(lang_frame, text=tr("dlg_reset") if False else "🔄", command=on_refresh, width=3)
            self.btn_refresh.pack(side="left")

        # Информация об аудиодорожке
        row2 = ttk.Frame(self, style="Panel.TFrame")
        row2.pack(fill="x", pady=(4, 2))

        self.lbl_audio_title = ttk.Label(row2, text=f"🎵 {tr('label_track')}", width=18, style="Panel.TLabel")
        self.lbl_audio_title.pack(side="left")
        self.lbl_audio_info = ttk.Label(row2, text=tr("stat_analyzing"), foreground="#4fc3f7", font=("Segoe UI", 9, "bold"), style="Panel.TLabel")
        self.lbl_audio_info.pack(side="left")

        # Папка сессии / Файл битов
        row3 = ttk.Frame(self, style="Panel.TFrame")
        row3.pack(fill="x", pady=2)
        self.lbl_target_title = ttk.Label(row3, text="📁 Session / JSON:", width=18, style="Muted.TLabel")
        self.lbl_target_title.pack(side="left")
        self.lbl_target_path = ttk.Label(row3, text="—", style="Muted.TLabel")
        self.lbl_target_path.pack(side="left")

    def _on_lang_selected(self, event=None):
        code = self.var_language.get().lower()
        if set_language(code):
            if self.on_language_change:
                self.on_language_change(code)

    def update_locale(self):
        super().update_locale()
        self.var_language.set(get_current_language().upper())
        self.lbl_audio_title.config(text=f"🎵 {tr('label_track')}")
        self.lbl_target_title.config(text="📁 Session / JSON:")
        self.update_info(*self._last_status)

    def update_info(self, is_connected, project_name="", audio_info=None, target_path=""):
        self._last_status = (is_connected, project_name, audio_info, target_path)
        if is_connected:
            self.lbl_davinci_status.config(text=f"🟢 {tr('status_connected')}", foreground="#4caf50")
            self.lbl_project_name.config(text=f"| {tr('project_prefix')} {project_name or '—'}")
        else:
            self.lbl_davinci_status.config(text=f"🔴 {tr('status_disconnected')}", foreground="#ef5350")
            self.lbl_project_name.config(text=f"| {tr('project_prefix')} {tr('no_project')}")

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
            msg = audio_info.get("message", tr("audio_not_found"))
            self.lbl_audio_info.config(text=f"⚠️ {msg}", foreground="#ef5350")
        else:
            self.lbl_audio_info.config(text=tr("audio_none"), foreground=TEXT_MUTED)

        if target_path:
            self.lbl_target_path.config(text=str(target_path))


class SettingsPanel(PanelBase):
    """Компактная панель настроек детекции и маркеров."""
    def __init__(self, parent, on_change=None, on_open_adaptive=None):
        super().__init__(parent, title_key="settings_title")
        self.on_change = on_change
        self.on_open_adaptive = on_open_adaptive

        # Строка 1: Таймлайн и Индекс аудиотрека
        r1 = ttk.Frame(self, style="Panel.TFrame")
        r1.pack(fill="x", pady=3)

        self.lbl_timeline = ttk.Label(r1, text=tr("label_timeline"), width=14, style="Panel.TLabel")
        self.lbl_timeline.pack(side="left")
        self.var_timeline = tk.StringVar(value="intro")
        self.cb_timeline = ttk.Combobox(r1, textvariable=self.var_timeline, state="readonly", width=18)
        self.cb_timeline.pack(side="left", padx=(0, 16))
        self.cb_timeline.bind("<<ComboboxSelected>>", self._trigger_change)

        self.lbl_track = ttk.Label(r1, text=tr("label_track"), width=12, style="Panel.TLabel")
        self.lbl_track.pack(side="left")
        self.var_track_index = tk.IntVar(value=2)
        sb_track = ttk.Spinbox(r1, from_=1, to=20, textvariable=self.var_track_index, width=5, command=self._trigger_change)
        sb_track.pack(side="left")
        sb_track.bind("<KeyRelease>", self._trigger_change)
        self.lbl_track_def = ttk.Label(r1, text=tr("label_track_default"), style="Muted.TLabel")
        self.lbl_track_def.pack(side="left", padx=4)

        # Строка 2: Частота маркеров (Плотность склеек), Цвет, Таргет
        r2 = ttk.Frame(self, style="Panel.TFrame")
        r2.pack(fill="x", pady=3)

        self.lbl_density = ttk.Label(r2, text=tr("label_density"), width=16, style="Panel.TLabel")
        self.lbl_density.pack(side="left")
        
        self._freq_val = 0
        freq_map = get_frequency_map()
        self.var_frequency_label = tk.StringVar(value=freq_map[2][0])
        self.cb_frequency = ttk.Combobox(
            r2,
            textvariable=self.var_frequency_label,
            values=[label for label, _ in freq_map],
            state="readonly",
            width=36
        )
        self.cb_frequency.pack(side="left", padx=(0, 12))
        self.cb_frequency.bind("<<ComboboxSelected>>", self._on_frequency_selected)

        self.lbl_color = ttk.Label(r2, text=tr("label_color"), width=6, style="Panel.TLabel")
        self.lbl_color.pack(side="left")
        self.var_color = tk.StringVar(value="Red")
        cb_color = ttk.Combobox(r2, textvariable=self.var_color, values=MARKER_COLORS, state="readonly", width=8)
        cb_color.pack(side="left", padx=(0, 10))

        self.lbl_target = ttk.Label(r2, text=tr("label_target"), width=6, style="Panel.TLabel")
        self.lbl_target.pack(side="left")
        self.var_target = tk.StringVar(value="clip")
        self._user_preferred_target = "clip"
        self._is_complex_locked = False
        self.cb_target = ttk.Combobox(r2, textvariable=self.var_target, values=MARKER_TARGETS, state="readonly", width=8)
        self.cb_target.pack(side="left")
        self.cb_target.bind("<<ComboboxSelected>>", self._on_target_selected)
        self.lbl_target_hint = ttk.Label(r2, text="", font=("Segoe UI", 8), style="Muted.TLabel")
        self.lbl_target_hint.pack(side="left", padx=(6, 0))

        # Строка 2.5: Динамический калькулятор темпа монтажа (Live Pace Indicator)
        r_pace = ttk.Frame(self, style="Panel.TFrame")
        r_pace.pack(fill="x", pady=(2, 4))
        self.lbl_pace_info = ttk.Label(
            r_pace,
            text="",
            foreground="#4fc3f7",
            font=("Segoe UI", 8, "bold"),
            style="Panel.TLabel"
        )
        self.lbl_pace_info.pack(side="left", padx=(4, 0))

        # Строка 3: Адаптивный режим
        r3 = ttk.Frame(self, style="Panel.TFrame")
        r3.pack(fill="x", pady=(6, 2))

        self.var_adaptive = tk.BooleanVar(value=False)
        self.chk_adapt = ttk.Checkbutton(r3, text=tr("adaptive_mode"), variable=self.var_adaptive, command=self._on_adaptive_toggle)
        self.chk_adapt.pack(side="left")

        self.lbl_adapt_status = ttk.Label(r3, text=tr("status_off"), foreground="#888888", font=("Segoe UI", 8, "bold"), style="Panel.TLabel")
        self.lbl_adapt_status.pack(side="left", padx=(8, 12))

        self.btn_adapt_config = ttk.Button(r3, text=tr("btn_configure"), command=self._on_click_adaptive, width=14)
        self.btn_adapt_config.pack(side="left")
        self._update_adaptive_view()
        self.update_pace_estimate()

    def update_locale(self):
        super().update_locale()
        self.lbl_timeline.config(text=tr("label_timeline"))
        self.lbl_track.config(text=tr("label_track"))
        self.lbl_track_def.config(text=tr("label_track_default"))
        self.lbl_density.config(text=tr("label_density"))
        self.lbl_color.config(text=tr("label_color"))
        self.lbl_target.config(text=tr("label_target"))
        self.chk_adapt.config(text=tr("adaptive_mode"))
        self.btn_adapt_config.config(text=tr("btn_configure"))

        # Refresh frequency presets
        freq_map = get_frequency_map()
        self.cb_frequency.config(values=[label for label, _ in freq_map])
        self.set_frequency_value(self._freq_val)

        if self._is_complex_locked:
            self.lbl_target_hint.config(text=tr("target_locked_hint"))

        self._update_adaptive_view()
        self.update_pace_estimate()

    def _trigger_change(self, event=None):
        if self.on_change:
            self.on_change()

    def _on_adaptive_toggle(self):
        self._update_adaptive_view()
        self._trigger_change()

    def _update_adaptive_view(self):
        if self.var_adaptive.get():
            self.lbl_adapt_status.config(text=tr("status_on"), foreground="#4caf50")
            self.btn_adapt_config.config(state="normal")
        else:
            self.lbl_adapt_status.config(text=tr("status_off"), foreground="#888888")
            self.btn_adapt_config.config(state="disabled")

    def _on_click_adaptive(self):
        if self.on_open_adaptive:
            self.on_open_adaptive()

    def _on_frequency_selected(self, event=None):
        lbl = self.var_frequency_label.get()
        freq_map = get_frequency_map()
        for label, val in freq_map:
            if label == lbl:
                self._freq_val = val
                break
        self.update_pace_estimate()
        self._trigger_change()

    def get_frequency_value(self):
        """Вернуть целочисленное значение frequency (-2..2) для бэкенда."""
        return self._freq_val

    def set_frequency_value(self, val):
        """Установить текстовый пресет по целочисленному значению."""
        self._freq_val = val
        freq_map = get_frequency_map()
        for label, f_val in freq_map:
            if f_val == val:
                self.var_frequency_label.set(label)
                break
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
        bar_dur = 4.0 * (60.0 / cur_bpm)
        clip_dur = bar_dur * (2.0 ** -freq)
        frames = int(round(clip_dur * cur_fps))
        expected_clips = int(round(cur_dur / clip_dur)) if clip_dur > 0 else 0

        self.lbl_pace_info.config(
            text=tr("pace_info_fmt", clip_dur=clip_dur, frames=frames, expected_clips=expected_clips, bpm=cur_bpm)
        )

    def _on_target_selected(self, event=None):
        if not getattr(self, "_is_complex_locked", False):
            self._user_preferred_target = self.var_target.get()
        self._trigger_change()

    def set_target_mode(self, is_complex=False):
        """Блокировка режима 'clip' для сложного монтажа во избежание сбоев DaVinci."""
        self._is_complex_locked = bool(is_complex)
        if is_complex:
            self.var_target.set("timeline")
            self.cb_target.config(state="disabled")
            self.lbl_target_hint.config(text=tr("target_locked_hint"), foreground="#ffb74d")
        else:
            self.cb_target.config(state="readonly", values=MARKER_TARGETS)
            self.lbl_target_hint.config(text="", foreground=TEXT_MUTED)
            pref = getattr(self, "_user_preferred_target", "clip")
            if pref in MARKER_TARGETS:
                self.var_target.set(pref)


class ResultsPanel(PanelBase):
    """Панель результатов анализа музыки."""
    def __init__(self, parent):
        super().__init__(parent, title_key="results_title")

        self.cards_frame = ttk.Frame(self, style="Panel.TFrame")
        self.cards_frame.pack(fill="x", pady=2)

        self.cards = {}
        self.card_titles = {}
        self._last_res = None
        metrics = [
            ("bpm", "stat_bpm"),
            ("signature", "Time Signature"),
            ("total_beats", "stat_beats"),
            ("strong_beats", "stat_segments"),
            ("markers", "stat_placed"),
        ]

        for key, title_key in metrics:
            c = ttk.Frame(self.cards_frame, style="Panel.TFrame", padding=(8, 4))
            c.pack(side="left", fill="both", expand=True, padx=2)
            lbl_title = ttk.Label(c, text=tr(title_key) if title_key.startswith("stat_") else title_key, style="Muted.TLabel")
            lbl_title.pack(anchor="center")
            self.card_titles[key] = (lbl_title, title_key)
            val_lbl = ttk.Label(c, text="—", font=("Segoe UI", 12, "bold"), foreground="#4fc3f7", style="Panel.TLabel")
            val_lbl.pack(anchor="center", pady=(2, 0))
            self.cards[key] = val_lbl

    def update_locale(self):
        super().update_locale()
        for key, (lbl_title, title_key) in self.card_titles.items():
            lbl_title.config(text=tr(title_key) if title_key.startswith("stat_") else title_key)
        self.update_results(self._last_res)

    def update_results(self, res):
        self._last_res = res
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
    def __init__(self, parent, on_analyze=None, on_save_json=None, on_export_xml=None, on_export_edl=None,
                 on_place_markers=None, on_clear_markers=None, on_save_settings=None, on_undo=None, on_view_log=None):
        super().__init__(parent, title_key="menu_tools")

        # Основные кнопки процесса
        row1 = ttk.Frame(self, style="Panel.TFrame")
        row1.pack(fill="x", pady=(2, 6))

        # Шаг 1: Запуск детекции
        self.btn_analyze = ttk.Button(row1, text=tr("btn_analyze"), style="Accent.TButton", command=on_analyze, takefocus=False)
        self.btn_analyze.pack(side="left", padx=(0, 8))

        # Шаг 2: Разметить на таймлайне
        self.btn_place = ttk.Button(row1, text=tr("btn_place_markers"), style="Success.TButton", command=on_place_markers, state="disabled", takefocus=False)
        self.btn_place.pack(side="left", padx=(0, 8))

        # Шаг 3: Очистить маркеры
        self.btn_clear = ttk.Button(row1, text=tr("btn_clear_markers"), style="Danger.TButton", command=on_clear_markers, takefocus=False)
        self.btn_clear.pack(side="left")

        # Экспорт EDL, FCP XML и сохранение в JSON (справа)
        self.btn_save_json = ttk.Button(row1, text="💾 JSON", command=on_save_json, state="disabled", takefocus=False)
        self.btn_save_json.pack(side="right")

        self.btn_export_xml = ttk.Button(row1, text="🎬 FCP XML", command=on_export_xml, state="disabled", takefocus=False)
        self.btn_export_xml.pack(side="right", padx=(0, 6))

        self.btn_export_edl = ttk.Button(row1, text="📄 EDL", command=on_export_edl, state="disabled", takefocus=False)
        self.btn_export_edl.pack(side="right", padx=(0, 6))

        # Вспомогательные кнопки
        row2 = ttk.Frame(self, style="Panel.TFrame")
        row2.pack(fill="x", pady=2)

        self.btn_save = ttk.Button(row2, text=tr("dlg_save"), command=on_save_settings, takefocus=False)
        self.btn_save.pack(side="left", padx=(0, 8))

        self.btn_undo = ttk.Button(row2, text="↩ Undo", command=on_undo, state="disabled", takefocus=False)
        self.btn_undo.pack(side="left", padx=(0, 8))

        self.btn_log = ttk.Button(row2, text=f"📋 {tr('menu_show_log')}", command=on_view_log, takefocus=False)
        self.btn_log.pack(side="left")

        self.lbl_status = ttk.Label(row2, text=tr("status_ready"), style="Panel.TLabel")
        self.lbl_status.pack(side="right")

    def update_locale(self):
        super().update_locale()
        self.btn_analyze.config(text=tr("btn_analyze"))
        self.btn_place.config(text=tr("btn_place_markers"))
        self.btn_clear.config(text=tr("btn_clear_markers"))
        self.btn_save.config(text=tr("dlg_save"))
        self.btn_log.config(text=f"📋 {tr('menu_show_log')}")

    def set_status(self, text, color=TEXT_MAIN):
        self.lbl_status.config(text=text, foreground=color)

    def set_can_save_json(self, can_save):
        self.btn_save_json.config(state="normal" if can_save else "disabled")

    def set_can_export_xml(self, can_export):
        self.btn_export_xml.config(state="normal" if can_export else "disabled")

    def set_can_export_edl(self, can_export):
        self.btn_export_edl.config(state="normal" if can_export else "disabled")

    def set_can_place(self, can_place):
        self.btn_place.config(state="normal" if can_place else "disabled")

    def set_can_undo(self, can_undo):
        self.btn_undo.config(state="normal" if can_undo else "disabled")
