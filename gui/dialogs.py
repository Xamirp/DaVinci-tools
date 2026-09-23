#!/usr/bin/env python3
"""
dialogs.py — Диалоговые окна: немодальный лог (LogDialog) и модальный диалог адаптивного режима (AdaptiveSettingsDialog).
"""

import os
import tkinter as tk
from tkinter import ttk, filedialog
from .theme import BG_DARK, BG_PANEL, BG_ENTRY, TEXT_MAIN, TEXT_MUTED, TEXT_ACCENT, BORDER_COLOR
from .panels import FREQUENCY_MAP, LABEL_TO_FREQ, FREQ_TO_LABEL



class LogDialog(tk.Toplevel):
    """Отдельное немодальное окно лога с автопрокруткой и подсветкой."""
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Журнал операций — Beat Marker")
        self.geometry("640x420")
        self.minsize(450, 300)
        self.configure(bg=BG_DARK)

        # Не блокирует родительское окно!
        self.parent = parent
        self._build_ui()

        # При закрытии крестиком скрываем, а не уничтожаем, чтобы сохранять текст
        self.protocol("WM_DELETE_WINDOW", self.hide)

    def _build_ui(self):
        main_frame = ttk.Frame(self, padding=8)
        main_frame.pack(fill="both", expand=True)

        # Текстовая область лога
        text_frame = ttk.Frame(main_frame)
        text_frame.pack(fill="both", expand=True)

        self.text_area = tk.Text(
            text_frame,
            bg=BG_ENTRY,
            fg=TEXT_MAIN,
            insertbackground=TEXT_MAIN,
            selectbackground="#1565c0",
            selectforeground="#ffffff",
            font=("Consolas", 9),
            wrap="word",
            relief="flat",
            highlightthickness=1,
            highlightbackground=BORDER_COLOR,
            highlightcolor=TEXT_ACCENT,
            padx=8,
            pady=8
        )
        scrollbar = ttk.Scrollbar(text_frame, orient="vertical", command=self.text_area.yview)
        self.text_area.configure(yscrollcommand=scrollbar.set)

        self.text_area.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Цветовые теги
        self.text_area.tag_config("info", foreground=TEXT_MAIN)
        self.text_area.tag_config("success", foreground="#4caf50")
        self.text_area.tag_config("warn", foreground="#ffb74d")
        self.text_area.tag_config("error", foreground="#ef5350")
        self.text_area.tag_config("header", foreground="#4fc3f7", font=("Consolas", 9, "bold"))
        self.text_area.tag_config("timestamp", foreground=TEXT_MUTED)

        # Панель кнопок внизу
        btn_bar = ttk.Frame(main_frame)
        btn_bar.pack(fill="x", pady=(8, 0))

        ttk.Button(btn_bar, text="Очистить лог", command=self.clear_log).pack(side="left", padx=(0, 6))
        ttk.Button(btn_bar, text="Скопировать всё", command=self.copy_all).pack(side="left")

        self.lbl_msg_count = ttk.Label(btn_bar, text="Сообщений: 0", style="Muted.TLabel")
        self.lbl_msg_count.pack(side="left", padx=12)

        ttk.Button(btn_bar, text="Закрыть", command=self.hide).pack(side="right")
        self.msg_count = 0

    def append_log(self, msg):
        """Потокобезопасное добавление строки в лог."""
        self.after(0, self._insert_text, str(msg))

    def _insert_text(self, text):
        tag = "info"
        lower = text.lower()
        if "error" in lower or "критическая ошибка" in lower or "ошибка" in lower or "fail" in lower:
            tag = "error"
        elif "success" in lower or "успешно" in lower or "готово" in lower or "сохранён" in lower:
            tag = "success"
        elif "warning" in lower or "внимание" in lower or "предупреждение" in lower or "остановка" in lower:
            tag = "warn"
        elif text.startswith("===") or text.startswith("---") or text.startswith("[*]"):
            tag = "header"

        self.text_area.config(state="normal")
        self.text_area.insert("end", text + "\n", tag)
        self.text_area.see("end")
        self.text_area.config(state="disabled")

        self.msg_count += 1
        self.lbl_msg_count.config(text=f"Сообщений: {self.msg_count}")

    def clear_log(self):
        self.text_area.config(state="normal")
        self.text_area.delete("1.0", "end")
        self.text_area.config(state="disabled")
        self.msg_count = 0
        self.lbl_msg_count.config(text="Сообщений: 0")

    def copy_all(self):
        txt = self.text_area.get("1.0", "end-1c")
        self.clipboard_clear()
        self.clipboard_append(txt)

    def show(self):
        self.deiconify()
        self.lift()
        self.focus_force()

    def hide(self):
        self.withdraw()


class AdaptiveSettingsDialog(tk.Toplevel):
    """Модальный диалог настройки параметров адаптивного режима."""
    def __init__(self, parent, current_settings):
        super().__init__(parent)
        self.title("Настройки адаптивного режима")
        self.geometry("440x260")
        self.resizable(False, False)
        self.configure(bg=BG_DARK)

        self.transient(parent)
        self.grab_set()

        self.result = None
        self.current = current_settings.copy()

        self._build_ui()
        self._load_data()

        # Центрирование относительно родителя
        self.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() - self.winfo_width()) // 2
        y = parent.winfo_y() + (parent.winfo_height() - self.winfo_height()) // 2
        self.geometry(f"+{max(0, x)}+{max(0, y)}")

        self.protocol("WM_DELETE_WINDOW", self.on_cancel)

    def _build_ui(self):
        frame = ttk.Frame(self, padding=14, style="Panel.TFrame")
        frame.pack(fill="both", expand=True)

        ttk.Label(frame, text="Параметры адаптивной детекции", style="Section.TLabel").pack(anchor="w", pady=(0, 10))

        # Частота тихо
        row1 = ttk.Frame(frame, style="Panel.TFrame")
        row1.pack(fill="x", pady=4)
        ttk.Label(row1, text="Частота (тихо):", width=18, style="Panel.TLabel").pack(side="left")
        self.var_quiet_label = tk.StringVar(value=FREQ_TO_LABEL.get(-1, FREQUENCY_MAP[1][0]))
        cb_quiet = ttk.Combobox(row1, textvariable=self.var_quiet_label, values=[l for l, _ in FREQUENCY_MAP], state="readonly", width=34)
        cb_quiet.pack(side="left")

        # Частота громко
        row2 = ttk.Frame(frame, style="Panel.TFrame")
        row2.pack(fill="x", pady=4)
        ttk.Label(row2, text="Частота (громко):", width=18, style="Panel.TLabel").pack(side="left")
        self.var_loud_label = tk.StringVar(value=FREQ_TO_LABEL.get(0, FREQUENCY_MAP[2][0]))
        cb_loud = ttk.Combobox(row2, textvariable=self.var_loud_label, values=[l for l, _ in FREQUENCY_MAP], state="readonly", width=34)
        cb_loud.pack(side="left")

        # Порог RMS
        row3 = ttk.Frame(frame, style="Panel.TFrame")
        row3.pack(fill="x", pady=4)
        ttk.Label(row3, text="Порог громкости (RMS):", width=18, style="Panel.TLabel").pack(side="left")
        self.var_rms = tk.StringVar()
        ttk.Entry(row3, textvariable=self.var_rms, width=8).pack(side="left")
        ttk.Button(row3, text="Авто (0.229)", command=lambda: self.var_rms.set("0.229"), width=12).pack(side="left", padx=8)

        # Кнопки внизу
        sep = ttk.Separator(frame, orient="horizontal")
        sep.pack(fill="x", pady=(14, 10))

        btn_box = ttk.Frame(frame, style="Panel.TFrame")
        btn_box.pack(fill="x")

        ttk.Button(btn_box, text="Применить", style="Accent.TButton", command=self.on_apply).pack(side="right", padx=(6, 0))
        ttk.Button(btn_box, text="Отмена", command=self.on_cancel).pack(side="right")

    def _load_data(self):
        q_val = self.current.get("freq_quiet", -1)
        l_val = self.current.get("freq_loud", 0)
        self.var_quiet_label.set(FREQ_TO_LABEL.get(q_val, FREQUENCY_MAP[1][0]))
        self.var_loud_label.set(FREQ_TO_LABEL.get(l_val, FREQUENCY_MAP[2][0]))
        self.var_rms.set(str(self.current.get("rms_threshold", "0.229")))

    def on_apply(self):
        try:
            rms_val = float(self.var_rms.get().strip())
        except ValueError:
            rms_val = 0.229

        self.result = {
            "freq_quiet": LABEL_TO_FREQ.get(self.var_quiet_label.get(), -1),
            "freq_loud": LABEL_TO_FREQ.get(self.var_loud_label.get(), 0),
            "rms_threshold": rms_val,
        }
        self.grab_release()
        self.destroy()

    def on_cancel(self):
        self.result = None
        self.grab_release()
        self.destroy()


class ProgressDialog(tk.Toplevel):
    """Окно отображения прогресса операций (анализ аудио, разметка в DaVinci)."""
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Выполнение операции")
        self.geometry("520x210")
        self.minsize(460, 190)
        self.resizable(False, False)
        self.configure(bg=BG_DARK)

        self.parent = parent
        self._on_cancel_callback = None
        self._auto_close_job = None
        self._build_ui()

        self.protocol("WM_DELETE_WINDOW", self._on_close_clicked)

    def _build_ui(self):
        main_frame = ttk.Frame(self, padding=16, style="Panel.TFrame")
        main_frame.pack(fill="both", expand=True)

        # Заголовок операции
        self.lbl_title = ttk.Label(main_frame, text="Выполнение операции", style="Section.TLabel", font=("Segoe UI", 11, "bold"))
        self.lbl_title.pack(anchor="w", pady=(0, 10))

        # Основной статус
        self.lbl_status = ttk.Label(main_frame, text="Инициализация...", style="Panel.TLabel", font=("Segoe UI", 10))
        self.lbl_status.pack(anchor="w", pady=(0, 4))

        # Вторичный детальный текст
        self.lbl_detail = ttk.Label(main_frame, text="", style="Muted.TLabel")
        self.lbl_detail.pack(anchor="w", pady=(0, 10))

        # Шкала прогресса и процент
        prog_row = ttk.Frame(main_frame, style="Panel.TFrame")
        prog_row.pack(fill="x", pady=(0, 12))

        self.progressbar = ttk.Progressbar(
            prog_row,
            style="Horizontal.TProgressbar",
            mode="determinate",
            maximum=100
        )
        self.progressbar.pack(side="left", fill="x", expand=True, padx=(0, 10))

        self.lbl_percent = ttk.Label(prog_row, text="0%", width=5, style="Panel.TLabel", font=("Segoe UI", 9, "bold"))
        self.lbl_percent.pack(side="right")

        # Разделитель и кнопка закрытия/отмены
        sep = ttk.Separator(main_frame, orient="horizontal")
        sep.pack(fill="x", pady=(0, 10))

        btn_row = ttk.Frame(main_frame, style="Panel.TFrame")
        btn_row.pack(fill="x")

        self.btn_cancel = ttk.Button(btn_row, text="Отмена", command=self._on_close_clicked)
        self.btn_cancel.pack(side="right")

    def show_progress(self, title="Выполнение операции", status="Инициализация...", detail="", on_cancel=None):
        """Отобразить окно прогресса и отцентрировать над главным окном."""
        if self._auto_close_job:
            self.after_cancel(self._auto_close_job)
            self._auto_close_job = None

        self._on_cancel_callback = on_cancel
        self.lbl_title.config(text=title)
        self.lbl_status.config(text=status, foreground=TEXT_MAIN)
        self.lbl_detail.config(text=detail)
        self.progressbar.config(mode="determinate", value=0)
        self.lbl_percent.config(text="0%")
        self.btn_cancel.config(text="Отмена", state="normal" if on_cancel else "disabled")

        # Центрирование относительно родительского окна
        self.update_idletasks()
        try:
            px = self.parent.winfo_rootx()
            py = self.parent.winfo_rooty()
            pw = self.parent.winfo_width()
            ph = self.parent.winfo_height()
            w = 520
            h = 210
            x = px + (pw - w) // 2
            y = py + (ph - h) // 2
            self.geometry(f"{w}x{h}+{max(0, x)}+{max(0, y)}")
        except Exception:
            pass

        self.deiconify()
        self.lift(self.parent)
        self.focus_force()

    def update_progress(self, percent: float = None, status: str = None, detail: str = None):
        """Потокобезопасное обновление состояния прогресса."""
        def _apply():
            if percent is not None:
                p_val = min(100.0, max(0.0, float(percent)))
                self.progressbar["value"] = p_val
                self.lbl_percent.config(text=f"{int(p_val)}%")
            if status is not None:
                self.lbl_status.config(text=str(status))
            if detail is not None:
                self.lbl_detail.config(text=str(detail))
        self.after(0, _apply)

    def finish(self, status="Готово!", detail="", auto_close_ms=700, on_done=None):
        """Завершение операции с автозакрытием."""
        def _apply():
            self.progressbar["value"] = 100
            self.lbl_percent.config(text="100%")
            self.lbl_status.config(text=status, foreground="#4caf50")
            if detail:
                self.lbl_detail.config(text=detail)
            self.btn_cancel.config(state="disabled")

            def _close():
                self.hide()
                if on_done:
                    on_done()

            if auto_close_ms > 0:
                self._auto_close_job = self.after(auto_close_ms, _close)
            else:
                _close()

        self.after(0, _apply)

    def set_error(self, err_msg):
        """Отобразить ошибку в окне прогресса."""
        def _apply():
            self.lbl_status.config(text=f"Ошибка: {err_msg}", foreground="#ef5350")
            self.btn_cancel.config(text="Закрыть", state="normal")
        self.after(0, _apply)

    def _on_close_clicked(self):
        if self._on_cancel_callback:
            try:
                self._on_cancel_callback()
            except Exception:
                pass
        self.hide()

    def hide(self):
        if self._auto_close_job:
            self.after_cancel(self._auto_close_job)
            self._auto_close_job = None
        self.withdraw()


class ExportFcpXmlDialog(tk.Toplevel):
    """Модальный диалог экспорта последовательности в Final Cut Pro 7 XML."""
    def __init__(self, parent, initial_dir: str, initial_filename: str, audio_path: str,
                 fps: float, beats_count: int, default_target: str = "clip"):
        super().__init__(parent)
        self.title("Экспорт последовательности FCP7 XML")
        self.geometry("540x360")
        self.minsize(480, 320)
        self.resizable(False, False)
        self.configure(bg=BG_DARK)

        self.transient(parent)
        self.grab_set()

        self.result = None
        self.audio_path = audio_path
        self.fps = fps
        self.beats_count = beats_count

        self.var_dir = tk.StringVar(value=str(initial_dir))
        self.var_filename = tk.StringVar(value=str(initial_filename))
        self.var_target = tk.StringVar(value=default_target)  # "clip", "timeline", "both"

        self._build_ui()

        # Центрирование относительно родителя
        self.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() - self.winfo_width()) // 2
        y = parent.winfo_y() + (parent.winfo_height() - self.winfo_height()) // 2
        self.geometry(f"+{max(0, x)}+{max(0, y)}")

        self.protocol("WM_DELETE_WINDOW", self.on_cancel)

    def _build_ui(self):
        frame = ttk.Frame(self, padding=16, style="Panel.TFrame")
        frame.pack(fill="both", expand=True)

        ttk.Label(frame, text="Экспорт в Final Cut Pro 7 XML (.xml)", style="Section.TLabel").pack(anchor="w", pady=(0, 10))

        # 1. Папка сохранения
        r1 = ttk.Frame(frame, style="Panel.TFrame")
        r1.pack(fill="x", pady=4)
        ttk.Label(r1, text="Папка сохранения:", width=18, style="Panel.TLabel").pack(side="left")
        ttk.Entry(r1, textvariable=self.var_dir).pack(side="left", fill="x", expand=True, padx=(0, 6))
        ttk.Button(r1, text="Обзор...", width=10, command=self._browse_dir).pack(side="right")

        # 2. Имя файла
        r2 = ttk.Frame(frame, style="Panel.TFrame")
        r2.pack(fill="x", pady=4)
        ttk.Label(r2, text="Имя XML-файла:", width=18, style="Panel.TLabel").pack(side="left")
        ttk.Entry(r2, textvariable=self.var_filename).pack(side="left", fill="x", expand=True)

        # 3. Размещение маркеров
        r3 = ttk.LabelFrame(frame, text=" Размещение маркеров долей ", padding=(10, 6))
        r3.pack(fill="x", pady=(10, 8))

        rb1 = ttk.Radiobutton(
            r3,
            text="На аудиоклипе (Clip markers) — рекомендуется для цельного аудиоклипа",
            value="clip",
            variable=self.var_target
        )
        rb1.pack(anchor="w", pady=2)

        rb2 = ttk.Radiobutton(
            r3,
            text="На таймлайне (Sequence / Timeline markers)",
            value="timeline",
            variable=self.var_target
        )
        rb2.pack(anchor="w", pady=2)

        rb3 = ttk.Radiobutton(
            r3,
            text="И на клипе, и на таймлайне (Both)",
            value="both",
            variable=self.var_target
        )
        rb3.pack(anchor="w", pady=2)

        # 4. Сводная информация
        audio_name = os.path.basename(self.audio_path) if self.audio_path else "—"
        info_text = (
            f"🎵 Аудиофайл: {audio_name}\n"
            f"⏱️ FPS: {self.fps:.3f} | Долей/битов: {self.beats_count} | Таймкод: 00:00:00:00\n"
            f"💡 Совместимо с Adobe Premiere Pro и Final Cut Pro 7.\n"
            f"   (Для DaVinci Resolve используйте кнопку «📍 Разметить в DaVinci»)."
        )
        lbl_info = ttk.Label(frame, text=info_text, style="Muted.TLabel", justify="left")
        lbl_info.pack(anchor="w", pady=(4, 10))


        # 5. Кнопки внизу
        sep = ttk.Separator(frame, orient="horizontal")
        sep.pack(fill="x", pady=(4, 10))

        btn_box = ttk.Frame(frame, style="Panel.TFrame")
        btn_box.pack(fill="x")

        ttk.Button(btn_box, text="🎬 Экспортировать", style="Accent.TButton", command=self.on_export).pack(side="right", padx=(6, 0))
        ttk.Button(btn_box, text="Отмена", command=self.on_cancel).pack(side="right")

    def _browse_dir(self):
        chosen = filedialog.askdirectory(initialdir=self.var_dir.get(), parent=self)
        if chosen:
            self.var_dir.set(os.path.normpath(chosen))

    def on_export(self):
        d = self.var_dir.get().strip()
        f = self.var_filename.get().strip()
        if not f:
            f = "sequence_beats_fcp7.xml"
        if not f.lower().endswith(".xml"):
            f += ".xml"

        self.result = {
            "output_dir": d,
            "filename": f,
            "marker_target": self.var_target.get(),
        }
        self.grab_release()
        self.destroy()

    def on_cancel(self):
        self.result = None
        self.grab_release()
        self.destroy()


class ExportEdlDialog(tk.Toplevel):
    """Модальный диалог экспорта маркеров таймлайна в формат CMX 3600 EDL (для DaVinci Resolve)."""
    def __init__(self, parent, initial_dir: str, initial_filename: str, fps: float,
                 beats_count: int, default_color: str = "Red"):
        super().__init__(parent)
        self.title("Экспорт маркеров EDL (DaVinci Resolve)")
        self.geometry("540x330")
        self.minsize(480, 290)
        self.resizable(False, False)
        self.configure(bg=BG_DARK)

        self.transient(parent)
        self.grab_set()

        self.result = None
        self.fps = fps
        self.beats_count = beats_count

        self.var_dir = tk.StringVar(value=str(initial_dir))
        self.var_filename = tk.StringVar(value=str(initial_filename))
        self.var_color = tk.StringVar(value=str(default_color))

        self._build_ui()

        # Центрирование относительно родителя
        self.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() - self.winfo_width()) // 2
        y = parent.winfo_y() + (parent.winfo_height() - self.winfo_height()) // 2
        self.geometry(f"+{max(0, x)}+{max(0, y)}")

        self.protocol("WM_DELETE_WINDOW", self.on_cancel)

    def _build_ui(self):
        frame = ttk.Frame(self, padding=16, style="Panel.TFrame")
        frame.pack(fill="both", expand=True)

        ttk.Label(frame, text="Экспорт маркеров в CMX 3600 EDL (.edl)", style="Section.TLabel").pack(anchor="w", pady=(0, 10))

        # 1. Папка сохранения
        r1 = ttk.Frame(frame, style="Panel.TFrame")
        r1.pack(fill="x", pady=4)
        ttk.Label(r1, text="Папка сохранения:", width=18, style="Panel.TLabel").pack(side="left")
        ttk.Entry(r1, textvariable=self.var_dir).pack(side="left", fill="x", expand=True, padx=(0, 6))
        ttk.Button(r1, text="Обзор...", width=10, command=self._browse_dir).pack(side="right")

        # 2. Имя файла
        r2 = ttk.Frame(frame, style="Panel.TFrame")
        r2.pack(fill="x", pady=4)
        ttk.Label(r2, text="Имя EDL-файла:", width=18, style="Panel.TLabel").pack(side="left")
        ttk.Entry(r2, textvariable=self.var_filename).pack(side="left", fill="x", expand=True)

        # 3. Цвет маркеров
        r3 = ttk.Frame(frame, style="Panel.TFrame")
        r3.pack(fill="x", pady=(6, 4))
        ttk.Label(r3, text="Цвет маркеров:", width=18, style="Panel.TLabel").pack(side="left")
        colors = ["Red", "Blue", "Green", "Yellow", "Cyan", "Pink", "Purple", "Fuchsia", "Rose", "Lavender", "Sky", "Mint", "Lemon", "Sand", "Cocoa", "White"]
        cb_color = ttk.Combobox(r3, textvariable=self.var_color, values=colors, state="readonly", width=16)
        cb_color.pack(side="left")

        # 4. Сводная информация и подсказка
        info_text = (
            f"⏱️ Частота кадров: {self.fps:.3f} fps | Маркеров к экспорту: {self.beats_count}\n"
            f"💡 Как импортировать в DaVinci Resolve:\n"
            f"   Кликните правой кнопкой на Таймлайн → Timelines → Import → Timeline Markers from EDL..."
        )
        lbl_info = ttk.Label(frame, text=info_text, style="Muted.TLabel", justify="left")
        lbl_info.pack(anchor="w", pady=(8, 10))

        # 5. Кнопки внизу
        sep = ttk.Separator(frame, orient="horizontal")
        sep.pack(fill="x", pady=(4, 10))

        btn_box = ttk.Frame(frame, style="Panel.TFrame")
        btn_box.pack(fill="x")

        ttk.Button(btn_box, text="📄 Экспортировать EDL", style="Accent.TButton", command=self.on_export).pack(side="right", padx=(6, 0))
        ttk.Button(btn_box, text="Отмена", command=self.on_cancel).pack(side="right")

    def _browse_dir(self):
        chosen = filedialog.askdirectory(initialdir=self.var_dir.get(), parent=self)
        if chosen:
            self.var_dir.set(os.path.normpath(chosen))

    def on_export(self):
        d = self.var_dir.get().strip()
        f = self.var_filename.get().strip()
        if not f:
            f = "timeline_markers.edl"
        if not f.lower().endswith(".edl"):
            f += ".edl"

        self.result = {
            "output_dir": d,
            "filename": f,
            "color": self.var_color.get(),
        }
        self.grab_release()
        self.destroy()

    def on_cancel(self):
        self.result = None
        self.grab_release()
        self.destroy()


