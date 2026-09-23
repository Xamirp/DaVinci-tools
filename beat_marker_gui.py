#!/usr/bin/env python3
"""beat_marker_gui.py — Графический интерфейс для анализа музыки и расстановки маркеров в DaVinci Resolve.
Локализовано через i18n (EN / UK / RU).
"""

import sys
import os
import json
import threading
import subprocess
import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path

# Fix Windows console encoding for Cyrillic / UTF-8
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

if getattr(sys, "frozen", False):
    SCRIPT_DIR = Path(sys.executable).parent.resolve()
else:
    SCRIPT_DIR = Path(__file__).parent.resolve()

sys.path.insert(0, str(SCRIPT_DIR))

# Self-relaunch in project .venv if needed (only for script mode)
if not getattr(sys, "frozen", False):
    _VENV_PYTHON = SCRIPT_DIR / ".venv" / "Scripts" / "python.exe"
    if not _VENV_PYTHON.exists():
        _VENV_PYTHON = SCRIPT_DIR / ".venv" / "bin" / "python"

    if __name__ == "__main__" and _VENV_PYTHON.exists() and sys.executable.lower() != str(_VENV_PYTHON).lower():
        subprocess.check_call([str(_VENV_PYTHON)] + sys.argv)
        raise SystemExit(0)

import beat_marker as bm
import fcp_xml_exporter as fcp_exporter
import edl_exporter as edl_exporter
from gui.theme import apply_theme, BG_DARK, TEXT_MAIN
from gui.i18n import tr, set_language, get_current_language, register_language_listener, LANGUAGES
from gui.command_manager import CommandManager, PlaceMarkersCommand, ClearMarkersCommand
from gui.dialogs import LogDialog, AdaptiveSettingsDialog, ProgressDialog, ExportFcpXmlDialog, ExportEdlDialog
from gui.panels import HeaderPanel, SettingsPanel, ResultsPanel, ActionsPanel
from gui.timeline_panel import TimelineWaveformPanel

SETTINGS_FILE = SCRIPT_DIR / "settings.json"

DEFAULT_SETTINGS = {
    "language": "en",
    "timeline": "intro",
    "track_index": 2,
    "frequency": 0,
    "adaptive": False,
    "freq_quiet": -1,
    "freq_loud": 0,
    "rms_threshold": 0.229,
    "marker_color": "Red",
    "marker_target": "clip",
    "window_width": 840,
    "window_height": 740,
}


def load_settings():
    try:
        with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
            saved = json.load(f)
            s = DEFAULT_SETTINGS.copy()
            s.update(saved)
            return s
    except Exception:
        return DEFAULT_SETTINGS.copy()


def save_settings(s):
    try:
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(s, f, indent=2, ensure_ascii=False)
    except Exception:
        pass


class BeatMarkerApp(tk.Tk):
    """Главное окно приложения Beat Marker с компонентной архитектурой и поддержкой i18n."""
    def __init__(self):
        super().__init__()
        self.settings = load_settings()
        
        # Устанавливаем язык из настроек
        cur_lang = self.settings.get("language", "en")
        set_language(cur_lang)
        register_language_listener(self._on_language_changed)

        self.title(tr("app_title"))
        self.minsize(720, 640)

        w = self.settings.get("window_width", 840)
        h = self.settings.get("window_height", 740)
        self.geometry(f"{w}x{h}")

        # Применяем тему DaVinci Resolve
        apply_theme(self)

        # Менеджер команд Undo/Redo
        self.cmd_manager = CommandManager()
        self.cmd_manager.add_listener(self._on_undo_state_changed)

        # Диалог лога
        self.log_dialog = LogDialog(self)
        self.log_dialog.withdraw()

        # Диалог прогресса операций
        self.progress_dialog = ProgressDialog(self)
        self.progress_dialog.withdraw()

        # Кэш последнего анализа
        self.last_analysis_result = None
        self.is_analyzing = False

        # Построение меню и интерфейса
        self._build_menu()
        self._build_ui()

        # Привязка горячих клавиш Undo / Redo
        self.bind("<Control-z>", lambda e: self._on_undo())
        self.bind("<Control-Z>", lambda e: self._on_undo())
        self.bind("<Control-y>", lambda e: self._on_redo())
        self.bind("<Control-Y>", lambda e: self._on_redo())
        self.bind("<Control-Shift-Z>", lambda e: self._on_redo())
        self.bind("<Control-Shift-z>", lambda e: self._on_redo())

        # Отвязываем клавишу Space от кнопок
        try:
            self.unbind_class("TButton", "<space>")
            self.unbind_class("Button", "<space>")
        except Exception:
            pass

        # Безопасные горячие клавиши таймлайна
        def _safe_hotkey(action):
            def _h(event):
                focused = self.focus_get()
                if isinstance(focused, (ttk.Entry, ttk.Spinbox, tk.Entry, tk.Text)):
                    return
                w = event.widget
                if isinstance(w, (ttk.Entry, ttk.Spinbox, tk.Entry, tk.Text)):
                    return
                action()
                return "break"
            return _h

        self.bind_all("<space>", _safe_hotkey(self.timeline_panel.toggle_play))
        self.bind_all("<KeyRelease-space>", lambda e: "break")
        self.bind_all("<m>", _safe_hotkey(self.timeline_panel.add_marker_at_playhead))
        self.bind_all("<M>", _safe_hotkey(self.timeline_panel.add_marker_at_playhead))
        self.bind_all("<Delete>", _safe_hotkey(self.timeline_panel.delete_selected_marker))
        self.bind_all("<BackSpace>", _safe_hotkey(self.timeline_panel.delete_selected_marker))
        self.bind_all("<s>", _safe_hotkey(self.timeline_panel.toggle_snap))
        self.bind_all("<S>", _safe_hotkey(self.timeline_panel.toggle_snap))
        self.bind_all("<F5>", lambda e: self._refresh_davinci_state())

        # Инициализация подключения и данных
        self._refresh_davinci_state()
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _build_menu(self):
        menubar = tk.Menu(self, bg="#222222", fg="#ffffff", activebackground="#0d47a1", activeforeground="#ffffff")
        
        # 1. File
        file_menu = tk.Menu(menubar, tearoff=0, bg="#222222", fg="#ffffff")
        file_menu.add_command(label=tr("menu_export_edl"), command=self._export_edl)
        file_menu.add_command(label=tr("menu_export_xml"), command=self._export_fcp_xml)
        file_menu.add_command(label=tr("menu_export_json"), command=self._save_beats_to_json)
        file_menu.add_separator()
        file_menu.add_command(label=tr("menu_exit"), command=self._on_close)
        menubar.add_cascade(label=tr("menu_file"), menu=file_menu)

        # 2. View
        view_menu = tk.Menu(menubar, tearoff=0, bg="#222222", fg="#ffffff")
        view_menu.add_command(label=tr("menu_show_log"), command=self._open_log_dialog)
        menubar.add_cascade(label=tr("menu_view"), menu=view_menu)

        # 3. Language
        lang_menu = tk.Menu(menubar, tearoff=0, bg="#222222", fg="#ffffff")
        lang_menu.add_command(label="English (EN)", command=lambda: self._set_app_language("en"))
        lang_menu.add_command(label="Українська (UK)", command=lambda: self._set_app_language("uk"))
        lang_menu.add_command(label="Русский (RU)", command=lambda: self._set_app_language("ru"))
        menubar.add_cascade(label=tr("menu_language"), menu=lang_menu)

        # 4. Help
        help_menu = tk.Menu(menubar, tearoff=0, bg="#222222", fg="#ffffff")
        help_menu.add_command(label=tr("menu_shortcuts"), command=self._show_shortcuts)
        help_menu.add_separator()
        help_menu.add_command(label=tr("menu_about"), command=self._show_about)
        menubar.add_cascade(label=tr("menu_help"), menu=help_menu)

        self.config(menu=menubar)

    def _set_app_language(self, lang_code):
        if set_language(lang_code):
            self.settings["language"] = lang_code
            save_settings(self.settings)

    def _on_language_changed(self, lang_code):
        self.title(tr("app_title"))
        self._build_menu()
        self.header_panel.update_locale()
        self.settings_panel.update_locale()
        self.results_panel.update_locale()
        self.timeline_panel.update_locale()
        self.actions_panel.update_locale()
        self.log_dialog.update_locale()

    def _build_ui(self):
        container = ttk.Frame(self, padding=8)
        container.pack(fill="both", expand=True)

        # 1. Панель заголовка и статуса проекта
        self.header_panel = HeaderPanel(
            container,
            on_refresh=self._refresh_davinci_state,
            on_language_change=self._set_app_language
        )
        self.header_panel.pack(fill="x", pady=(0, 6))

        # 2. Панель параметров
        self.settings_panel = SettingsPanel(
            container,
            on_change=self._on_settings_changed,
            on_open_adaptive=self._open_adaptive_dialog
        )
        self.settings_panel.pack(fill="x", pady=(0, 6))

        # 3. Панель результатов
        self.results_panel = ResultsPanel(container)
        self.results_panel.pack(fill="x", pady=(0, 6))

        # 4. Панель интерактивного таймлайна и волны звука
        self.timeline_panel = TimelineWaveformPanel(
            container,
            command_manager=self.cmd_manager,
            on_markers_changed=self._on_timeline_markers_changed,
            log_fn=self.log_dialog.append_log
        )
        self.timeline_panel.pack(fill="x", pady=(0, 6))

        # 5. Панель действий
        self.actions_panel = ActionsPanel(
            container,
            on_analyze=self._start_analysis,
            on_save_json=self._save_beats_to_json,
            on_export_xml=self._export_fcp_xml,
            on_export_edl=self._export_edl,
            on_place_markers=self._start_place_markers,
            on_clear_markers=self._start_clear_markers,
            on_save_settings=self._save_settings_clicked,
            on_undo=self._on_undo,
            on_view_log=self._open_log_dialog
        )
        self.actions_panel.pack(fill="x", pady=(0, 2))

        # Загрузка значений настроек в поля панели
        self._apply_settings_to_ui()

    def _apply_settings_to_ui(self):
        s = self.settings
        self.settings_panel.var_timeline.set(s.get("timeline", "intro"))
        self.settings_panel.var_track_index.set(s.get("track_index", 2))
        self.settings_panel.set_frequency_value(s.get("frequency", 0))
        self.settings_panel.var_color.set(s.get("marker_color", "Red"))
        t_val = s.get("marker_target", "clip")
        self.settings_panel._user_preferred_target = t_val
        self.settings_panel.var_target.set(t_val)
        self.settings_panel.var_adaptive.set(s.get("adaptive", False))
        self.settings_panel._update_adaptive_view()

    def _collect_settings_from_ui(self):
        return {
            "language": get_current_language(),
            "timeline": self.settings_panel.var_timeline.get(),
            "track_index": self.settings_panel.var_track_index.get(),
            "frequency": self.settings_panel.get_frequency_value(),
            "marker_color": self.settings_panel.var_color.get(),
            "marker_target": self.settings_panel.var_target.get(),
            "adaptive": self.settings_panel.var_adaptive.get(),
            "freq_quiet": self.settings.get("freq_quiet", -1),
            "freq_loud": self.settings.get("freq_loud", 0),
            "rms_threshold": self.settings.get("rms_threshold", 0.229),
            "window_width": self.winfo_width(),
            "window_height": self.winfo_height(),
        }

    def _refresh_davinci_state(self):
        """Проверить подключение, загрузить таймлайны и проинспектировать трек."""
        try:
            proj = bm.connect()
            if not proj:
                self.header_panel.update_info(False)
                self.settings_panel.cb_timeline['values'] = [f"({tr('status_disconnected')})"]
                return

            proj_name = proj.GetName()
            target_out = bm.resolve_target_output(proj)

            # Список таймлайнов
            timelines = []
            for i in range(1, proj.GetTimelineCount() + 1):
                t = proj.GetTimelineByIndex(i)
                if t:
                    timelines.append(t.GetName())

            if timelines:
                self.settings_panel.cb_timeline['values'] = timelines
                cur_tl = self.settings_panel.var_timeline.get()
                if cur_tl not in timelines:
                    intro_match = next((t for t in timelines if t.lower() == "intro"), timelines[0])
                    self.settings_panel.var_timeline.set(intro_match)

            # Инспекция аудио
            tl_name = self.settings_panel.var_timeline.get()
            track_idx = self.settings_panel.var_track_index.get()
            audio_info = bm.inspect_audio_track(proj, tl_name, track_idx)

            self.header_panel.update_info(
                is_connected=True,
                project_name=proj_name,
                audio_info=audio_info,
                target_path=target_out
            )
            if audio_info and audio_info.get("found"):
                self.settings_panel.update_pace_estimate(
                    audio_duration_sec=audio_info.get("duration_sec"),
                    timeline_fps=audio_info.get("timeline_fps")
                )
                is_complex = audio_info.get("is_complex", False)
                self.settings_panel.set_target_mode(is_complex=is_complex)
            else:
                self.settings_panel.set_target_mode(is_complex=False)

                # Загрузка существующего слепка аудио и маркеров в таймлайн
                baked_wav = target_out.parent / "audio" / f"timeline_A{track_idx}_baked.wav"
                if baked_wav.exists() and self.timeline_panel.audio_y is None:
                    try:
                        y, sr = bm.load_audio_safely(str(baked_wav))
                        existing_beats = []
                        if target_out.exists():
                            with open(target_out, "r", encoding="utf-8") as bf:
                                b_data = json.load(bf)
                                fps = float(b_data.get("timeline_fps", 23.976))
                                for idx, fr in enumerate(b_data.get("strong_beat_frames", [])):
                                    existing_beats.append({
                                        "time": float(fr) / fps,
                                        "name": f"Beat {idx + 1}",
                                        "strength": 0.8
                                    })
                        self.timeline_panel.load_audio(
                            y, sr,
                            strong_beats=existing_beats,
                            timeline_fps=audio_info.get("timeline_fps", 23.976)
                        )
                    except Exception:
                        pass

        except Exception as e:
            self.header_panel.update_info(False)
            self.log_dialog.append_log(f"Connection error: {e}")

    def _on_settings_changed(self):
        try:
            proj = bm.connect()
            if proj:
                tl_name = self.settings_panel.var_timeline.get()
                track_idx = self.settings_panel.var_track_index.get()
                audio_info = bm.inspect_audio_track(proj, tl_name, track_idx)
                target_out = bm.resolve_target_output(proj)
                self.header_panel.update_info(True, proj.GetName(), audio_info, target_out)
                if audio_info and audio_info.get("found"):
                    self.settings_panel.update_pace_estimate(
                        audio_duration_sec=audio_info.get("duration_sec"),
                        timeline_fps=audio_info.get("timeline_fps")
                    )
                    is_complex = audio_info.get("is_complex", False)
                    self.settings_panel.set_target_mode(is_complex=is_complex)
                else:
                    self.settings_panel.set_target_mode(is_complex=False)
        except Exception:
            pass

    def _open_adaptive_dialog(self):
        dlg = AdaptiveSettingsDialog(self, self.settings)
        self.wait_window(dlg)
        if dlg.result:
            self.settings.update(dlg.result)
            save_settings(self.settings)
            self.actions_panel.set_status(tr("status_ready"), "#4caf50")

    def _open_log_dialog(self):
        self.log_dialog.show()

    def _show_shortcuts(self):
        shortcuts_text = (
            "Space\t\tPlay / Pause Audio\n"
            "M\t\tAdd Marker at Playhead\n"
            "Delete / Backspace\tDelete Selected Marker\n"
            "S\t\tToggle Magnetic Snap\n"
            "Ctrl + Z\t\tUndo Action\n"
            "Ctrl + Y\t\tRedo Action\n"
            "F5\t\tRefresh DaVinci Connection\n"
            "Mouse Wheel\tScroll Timeline\n"
            "Ctrl + Wheel\tZoom Timeline In / Out\n"
        )
        messagebox.showinfo(tr("dlg_shortcuts_title"), shortcuts_text)

    def _show_about(self):
        messagebox.showinfo(tr("dlg_about_title"), tr("dlg_about_text"))

    # ─── ФАЗА 1: Анализ аудио (Запуск) ─────────────────────────────────────────

    def _start_analysis(self):
        if self.is_analyzing:
            return

        self.settings = self._collect_settings_from_ui()
        save_settings(self.settings)

        self.log_dialog.append_log("\n" + "=" * 60)
        self.log_dialog.append_log(tr("log_phase1_start"))
        self.log_dialog.append_log("=" * 60)

        self.progress_dialog.show_progress(
            title=tr("btn_analyze"),
            status=tr("stat_analyzing"),
            detail=f"{tr('label_timeline')} '{self.settings['timeline']}' | {tr('label_track')} A{self.settings['track_index']}"
        )

        self.is_analyzing = True
        self.actions_panel.btn_analyze.config(state="disabled")
        self.actions_panel.set_can_save_json(False)
        self.actions_panel.set_can_place(False)
        self.actions_panel.set_status(tr("stat_analyzing"), "#29b6f6")

        params = {
            "timeline": self.settings["timeline"],
            "track_type": "audio",
            "track_index": self.settings["track_index"],
            "item_index": 0,
            "beats_per_bar": None,
            "frequency": self.settings["frequency"],
            "adaptive": self.settings["adaptive"],
            "freq_quiet": self.settings["freq_quiet"],
            "freq_loud": self.settings["freq_loud"],
            "rms_threshold": self.settings["rms_threshold"],
            "marker_color": self.settings["marker_color"],
            "marker_target": self.settings["marker_target"],
            "place_markers": False,
            "save_json": False,
            "output_path": None,
        }

        def worker():
            try:
                res = bm.run_analysis(
                    params,
                    log_fn=self.log_dialog.append_log,
                    progress_fn=self.progress_dialog.update_progress
                )
                self.after(0, self._on_analysis_complete, res)
            except Exception as e:
                self.after(0, self._on_analysis_error, str(e))

        t = threading.Thread(target=worker, daemon=True)
        t.start()

    def _on_analysis_complete(self, res):
        self.is_analyzing = False
        self.actions_panel.btn_analyze.config(state="normal")

        if res.get("status") == "success":
            self.last_analysis_result = res
            self.results_panel.update_results(res)
            self.actions_panel.set_can_save_json(True)
            self.actions_panel.set_can_export_xml(True)
            self.actions_panel.set_can_export_edl(True)
            self.actions_panel.set_can_place(True)
            self.settings_panel.update_pace_estimate(
                bpm=res.get("tempo"),
                audio_duration_sec=res.get("audio_duration"),
                timeline_fps=res.get("timeline_fps")
            )
            n_beats = len(res.get("strong_beat_frames", []))
            bpm_val = res.get('tempo', 0)
            self.actions_panel.set_status(tr("log_success_analyzed", bpm=bpm_val, count=n_beats), "#4caf50")
            self.log_dialog.append_log(tr("log_success_analyzed", bpm=bpm_val, count=n_beats))

            # Закрываем прогресс
            self.progress_dialog.finish(
                status=tr("status_ready"),
                detail=f"BPM: {bpm_val:.1f} | Beats: {n_beats}",
                auto_close_ms=750
            )

            # Загрузка аудиоволны и долей в интерактивный таймлайн
            baked_path = res.get("_baked_audio_path")
            if baked_path and os.path.exists(baked_path):
                try:
                    y, sr = bm.load_audio_safely(baked_path)
                    self.timeline_panel.load_audio(
                        y, sr,
                        strong_beats=res.get("_strong_beats_data", []),
                        timeline_fps=res.get("timeline_fps", 23.976)
                    )
                except Exception as e:
                    self.log_dialog.append_log(f"Warning: Could not render timeline: {e}")
        else:
            err = res.get("message", "Unknown error")
            self.actions_panel.set_can_save_json(False)
            self.actions_panel.set_can_export_xml(False)
            self.actions_panel.set_can_export_edl(False)
            self.actions_panel.set_status(f"{tr('dlg_error')}: {err}", "#ef5350")
            self.log_dialog.append_log(f"\n[ERROR]: {err}")
            self.progress_dialog.set_error(err)

    def _on_timeline_markers_changed(self, updated_strong_beats):
        if self.last_analysis_result is None:
            self.last_analysis_result = {
                "status": "success",
                "tempo": getattr(self.settings_panel, "_cached_bpm", 117.5) or 117.5,
                "audio_duration": self.timeline_panel.duration_sec,
                "timeline_fps": self.timeline_panel.timeline_fps,
                "time_signature": "4/4",
                "beats_per_bar": 4,
                "frequency": self.settings_panel.get_frequency_value(),
                "markers_placed": 0,
            }

        fps = float(self.last_analysis_result.get("timeline_fps", 23.976))
        self.last_analysis_result["_strong_beats_data"] = updated_strong_beats
        self.last_analysis_result["strong_beat_frames"] = [int(b["time"] * fps) for b in updated_strong_beats]
        self.last_analysis_result["total_beats"] = len(updated_strong_beats)

        self.results_panel.update_results(self.last_analysis_result)
        self.actions_panel.set_can_save_json(True)
        self.actions_panel.set_can_export_xml(True)
        self.actions_panel.set_can_export_edl(True)
        self.actions_panel.set_can_place(True)
        self.actions_panel.set_status(f"Beats updated: {len(updated_strong_beats)} markers", "#4fc3f7")

    def _on_analysis_error(self, err_msg):
        self.is_analyzing = False
        self.actions_panel.btn_analyze.config(state="normal")
        self.actions_panel.set_can_save_json(False)
        self.actions_panel.set_can_export_xml(False)
        self.actions_panel.set_can_export_edl(False)
        self.actions_panel.set_status(f"{tr('dlg_error')}: {err_msg}", "#ef5350")
        self.log_dialog.append_log(f"\n[ERROR]: {err_msg}")
        self.progress_dialog.set_error(err_msg)

    def _save_beats_to_json(self):
        if not self.last_analysis_result:
            messagebox.showwarning(tr("dlg_warning"), tr("dlg_no_analysis_data"))
            return

        try:
            proj = bm.connect()
            out_file = bm.save_analysis_json(
                self.last_analysis_result,
                proj=proj,
                output_path=self.settings.get("output_path"),
                log_fn=self.log_dialog.append_log
            )
            if out_file:
                self.header_panel.lbl_target_path.config(text=str(out_file))
                self.actions_panel.set_status(f"JSON saved: {Path(out_file).name}", "#4caf50")
                messagebox.showinfo(tr("dlg_export_success"), f"JSON file saved:\n{out_file}")
        except Exception as e:
            self.actions_panel.set_status("JSON Error", "#ef5350")
            self.log_dialog.append_log(f"[JSON Error]: {e}")
            messagebox.showerror(tr("dlg_error"), f"Failed to save JSON:\n{e}")

    def _export_fcp_xml(self):
        if not self.last_analysis_result:
            messagebox.showwarning(tr("dlg_warning"), tr("dlg_no_analysis_data"))
            return

        baked_audio_path = self.last_analysis_result.get("_baked_audio_path")
        if not baked_audio_path or not os.path.exists(baked_audio_path):
            messagebox.showerror(tr("dlg_error"), "Compiled audio file not found. Please run analysis again.")
            return

        proj = bm.connect()
        proj_name = proj.GetName() if proj else "DefaultProject"
        tl_name = self.settings_panel.var_timeline.get() or "Sequence"

        default_dir = os.path.dirname(os.path.abspath(baked_audio_path))
        default_filename = f"{tl_name}_beats_fcp7.xml"
        fps = float(self.last_analysis_result.get("timeline_fps", 23.976))
        strong_beats = self.last_analysis_result.get("_strong_beats_data", [])

        dlg = ExportFcpXmlDialog(
            self,
            initial_dir=default_dir,
            initial_filename=default_filename,
            audio_path=baked_audio_path,
            fps=fps,
            beats_count=len(strong_beats),
            default_target="clip"
        )
        self.wait_window(dlg)

        if not dlg.result:
            return

        out_dir = dlg.result.get("output_dir", default_dir)
        filename = dlg.result.get("filename", default_filename)
        marker_target = dlg.result.get("marker_target", "clip")
        out_xml_path = os.path.join(out_dir, filename)
        marker_color = self.settings_panel.var_color.get()

        try:
            saved_path = fcp_exporter.export_to_fcp7_xml(
                output_xml_path=out_xml_path,
                audio_file_path=baked_audio_path,
                strong_beats=strong_beats,
                sequence_name=tl_name,
                timeline_fps=fps,
                sample_rate=48000,
                marker_target=marker_target,
                default_color=marker_color,
                log_fn=self.log_dialog.append_log
            )
            self.actions_panel.set_status(f"FCP XML: {Path(saved_path).name}", "#4caf50")
            self.log_dialog.append_log(f"[SUCCESS] Export FCP XML: {saved_path}")

            try:
                norm_path = os.path.normpath(saved_path)
                subprocess.Popen(f'explorer /select,"{norm_path}"')
            except Exception:
                pass

            messagebox.showinfo(
                tr("dlg_export_success"),
                f"FCP7 XML exported successfully:\n{saved_path}\n\nCompatible with Adobe Premiere Pro and Final Cut Pro 7."
            )
        except Exception as e:
            self.actions_panel.set_status("XML Error", "#ef5350")
            self.log_dialog.append_log(f"[XML Error]: {e}")
            messagebox.showerror(tr("dlg_error"), f"Failed to export XML:\n{e}")

    def _export_edl(self):
        if not self.last_analysis_result:
            messagebox.showwarning(tr("dlg_warning"), tr("dlg_no_analysis_data"))
            return

        proj = bm.connect()
        proj_name = proj.GetName() if proj else "DefaultProject"
        tl_name = self.settings_panel.var_timeline.get() or "Sequence"

        default_dir = os.path.abspath(f"output/{proj_name}")
        baked_audio_path = self.last_analysis_result.get("_baked_audio_path")
        if baked_audio_path and os.path.exists(baked_audio_path):
            default_dir = os.path.dirname(os.path.abspath(baked_audio_path))

        default_filename = f"{tl_name}_markers.edl"
        fps = float(self.last_analysis_result.get("timeline_fps", 23.976))
        strong_beats = self.last_analysis_result.get("_strong_beats_data", [])
        current_color = self.settings_panel.var_color.get()

        dlg = ExportEdlDialog(
            self,
            initial_dir=default_dir,
            initial_filename=default_filename,
            fps=fps,
            beats_count=len(strong_beats),
            default_color=current_color
        )
        self.wait_window(dlg)

        if not dlg.result:
            return

        out_dir = dlg.result.get("output_dir", default_dir)
        filename = dlg.result.get("filename", default_filename)
        marker_color = dlg.result.get("color", current_color)
        out_edl_path = os.path.join(out_dir, filename)

        try:
            saved_path = edl_exporter.export_to_edl(
                output_edl_path=out_edl_path,
                strong_beats=strong_beats,
                title=tl_name,
                timeline_fps=fps,
                default_color=marker_color,
                log_fn=self.log_dialog.append_log
            )
            self.actions_panel.set_status(f"EDL: {Path(saved_path).name}", "#4caf50")
            self.log_dialog.append_log(f"[SUCCESS] Export EDL: {saved_path}")

            try:
                norm_path = os.path.normpath(saved_path)
                subprocess.Popen(f'explorer /select,"{norm_path}"')
            except Exception:
                pass

            messagebox.showinfo(
                tr("dlg_export_success"),
                f"EDL Marker File created:\n{saved_path}\n\n"
                f"In DaVinci Resolve:\n"
                f"Right-click Timeline → Timelines → Import → Timeline Markers from EDL..."
            )
        except Exception as e:
            self.actions_panel.set_status("EDL Error", "#ef5350")
            self.log_dialog.append_log(f"[EDL Error]: {e}")
            messagebox.showerror(tr("dlg_error"), f"Failed to export EDL:\n{e}")

    # ─── ФАЗА 2: Разметка маркеров (в DaVinci) ─────────────────────────────────

    def _start_place_markers(self):
        if not self.last_analysis_result:
            messagebox.showwarning(tr("dlg_warning"), tr("dlg_no_analysis_data"))
            return

        proj = bm.connect()
        if not proj:
            messagebox.showerror(tr("dlg_error"), tr("dlg_davinci_not_running"))
            return

        tl_name = self.settings_panel.var_timeline.get()
        track_idx = self.settings_panel.var_track_index.get()
        color = self.settings_panel.var_color.get()
        target = self.settings_panel.var_target.get()
        strong_beats = self.last_analysis_result.get("_strong_beats_data", [])

        self.log_dialog.append_log("\n" + "-" * 50)
        self.log_dialog.append_log(tr("log_phase2_start", color=color, target=target))

        self.progress_dialog.show_progress(
            title=tr("btn_place_markers"),
            status="Placing markers in DaVinci Resolve...",
            detail=f"{tr('label_color')} {color} | {tr('label_target')} {target} | Beats: {len(strong_beats)}"
        )

        def worker():
            try:
                cmd = PlaceMarkersCommand(
                    proj=proj,
                    timeline_name=tl_name,
                    track_index=track_idx,
                    strong_beats=strong_beats,
                    color=color,
                    target=target,
                    log_fn=self.log_dialog.append_log,
                    progress_fn=self.progress_dialog.update_progress
                )
                res = self.cmd_manager.execute(cmd)
                placed = res.get("markers_placed", 0)

                def _done():
                    self.last_analysis_result["markers_placed"] = placed
                    self.results_panel.update_results(self.last_analysis_result)
                    self.actions_panel.set_status(f"Placed {placed} markers", "#4caf50")
                    self.log_dialog.append_log(tr("log_success_markers"))
                    self.progress_dialog.finish(
                        status=f"Placed {placed} markers",
                        detail=f"{color} | {target}",
                        auto_close_ms=750
                    )

                self.after(0, _done)
            except Exception as e:
                self.after(0, lambda: self.progress_dialog.set_error(str(e)))

        threading.Thread(target=worker, daemon=True).start()

    def _start_clear_markers(self):
        proj = bm.connect()
        if not proj:
            messagebox.showerror(tr("dlg_error"), tr("dlg_davinci_not_running"))
            return

        tl_name = self.settings_panel.var_timeline.get()
        track_idx = self.settings_panel.var_track_index.get()
        target = self.settings_panel.var_target.get()
        target_name = tr("target_desc_timeline") if target == "timeline" else tr("target_desc_clip", track=track_idx)

        self.progress_dialog.show_progress(
            title=tr("btn_clear_markers"),
            status="Clearing markers...",
            detail=f"{tr('label_timeline')} '{tl_name}', {target_name}"
        )

        def worker():
            try:
                cmd = ClearMarkersCommand(
                    proj=proj,
                    timeline_name=tl_name,
                    track_index=track_idx,
                    color="All",
                    target=target,
                    log_fn=self.log_dialog.append_log
                )
                deleted = self.cmd_manager.execute(cmd)

                def _done():
                    if self.last_analysis_result:
                        self.last_analysis_result["markers_placed"] = 0
                        self.results_panel.update_results(self.last_analysis_result)
                    self.actions_panel.set_status(f"Cleared {deleted} markers ({target})", "#ffb74d")
                    self.progress_dialog.finish(
                        status=f"Cleared {deleted} markers",
                        detail=f"Target: {target_name}",
                        auto_close_ms=600
                    )

                self.after(0, _done)
            except Exception as e:
                self.after(0, lambda: self.progress_dialog.set_error(str(e)))

        threading.Thread(target=worker, daemon=True).start()

    def _on_undo(self):
        if self.cmd_manager.can_undo():
            self.cmd_manager.undo()
            self.actions_panel.set_status("Action undone (Undo)", "#4fc3f7")

    def _on_redo(self):
        if self.cmd_manager.can_redo():
            self.cmd_manager.redo()
            self.actions_panel.set_status("Action redone (Redo)", "#4fc3f7")

    def _on_undo_state_changed(self, can_undo, can_redo):
        self.actions_panel.set_can_undo(can_undo)

    def _save_settings_clicked(self):
        self.settings = self._collect_settings_from_ui()
        save_settings(self.settings)
        self.actions_panel.set_status(tr("status_ready"), "#4caf50")
        self.after(2000, lambda: self.actions_panel.set_status(tr("status_ready"), TEXT_MAIN))

    def _on_close(self):
        try:
            self.timeline_panel.shutdown()
        except Exception:
            pass
        self.settings = self._collect_settings_from_ui()
        save_settings(self.settings)
        self.destroy()


def main():
    app = BeatMarkerApp()
    app.mainloop()


if __name__ == "__main__":
    main()
