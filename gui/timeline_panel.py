"""
Интерактивный таймлайн с огибающей звука (Waveform), линейкой времени,
курсором воспроизведения (Playhead), перетаскиванием маркеров (Drag & Drop),
магнитной привязкой (Snapping) и интеграцией Undo/Redo.
"""

import math
import tkinter as tk
from tkinter import ttk
import numpy as np

from gui.panels import PanelBase
from gui.theme import BG_DARK, BG_PANEL, TEXT_MAIN, TEXT_MUTED, ACCENT_BLUE
from gui.audio_player import AudioPlayer
from gui.command_manager import (
    MoveTimelineMarkerCommand,
    AddTimelineMarkerCommand,
    DeleteTimelineMarkerCommand
)

# Цветовая палитра DaVinci
COLOR_CANVAS_BG = "#181818"
COLOR_RULER_BG = "#222222"
COLOR_RULER_TEXT = "#9e9e9e"
COLOR_RULER_LINE = "#333333"
COLOR_GRID_BEAT = "#2e2e2e"        # Темно-серая сетка битов на теле таймлайна
COLOR_GRID_SEC = "#222222"         # Мягкая секундная сетка
COLOR_WAVE_BG = "#152930"          # Мягкий полупрозрачный фон огибающей
COLOR_WAVE_CONTOUR = "#2f8490"     # Плавный контур огибающей
COLOR_WAVE_CENTER = "#222222"      # Осевая линия середины
COLOR_PLAYHEAD = "#ffffff"         # Контрастный чистый белый плейхед
COLOR_MARKER_DEFAULT = "#e53935"
COLOR_SELECTION = "#ffd54f"

RULER_HEIGHT = 26
CANVAS_HEIGHT = 160
WAVEFORM_HEIGHT = CANVAS_HEIGHT - RULER_HEIGHT


def format_timecode(seconds: float) -> str:
    """Форматирование секунд в mm:ss.cc."""
    sec = max(0.0, float(seconds))
    mins = int(sec // 60)
    rem_sec = sec % 60
    return f"{mins:02d}:{rem_sec:05.2f}"


class TimelineWaveformPanel(PanelBase):
    """Панель интерактивного таймлайна с огибающей звука и маркерами."""

    def __init__(self, parent, command_manager=None, on_markers_changed=None, log_fn=print):
        super().__init__(parent, title="Интерактивный таймлайн и огибающая звука")
        self.command_manager = command_manager
        self.on_markers_changed = on_markers_changed
        self.log_fn = log_fn

        # Аудиоданные
        self.audio_y = None
        self.audio_sr = 22050
        self.duration_sec = 0.0
        self.timeline_fps = 23.976

        # Маркеры и состояние
        self.markers = []
        self.next_marker_id = 1
        self.selected_marker_id = None
        self.snap_enabled = True
        self.snap_beats_times = []

        # Навигация и масштабирование
        self.pixels_per_second = 40.0
        self.min_pps = 10.0
        self.max_pps = 300.0

        # Drag & Drop состояние
        self._dragging_marker_id = None
        self._drag_start_time = 0.0
        self._drag_last_x = 0
        self._is_scrubbing_playhead = False

        # Инициализация аудиоплеера
        self.player = AudioPlayer(
            on_time_update=None,
            on_playback_end=self._on_playback_finished
        )

        # Построение интерфейса
        self._create_toolbar()
        self._create_canvas()

        # Цикл обновления плейхеда
        self._playback_job = None

    # ─── UI Toolbar ──────────────────────────────────────────────────────────

    def _create_toolbar(self):
        tb = ttk.Frame(self, style="Panel.TFrame")
        tb.pack(fill="x", padx=4, pady=(0, 4))

        # 1. Воспроизведение
        self.btn_play = ttk.Button(tb, text="▶ Воспр. (Space)", command=self.toggle_play, width=16)
        self.btn_play.pack(side="left", padx=(0, 8))

        # 2. Индикатор времени
        self.lbl_time = ttk.Label(
            tb,
            text="00:00.00 / 00:00.00",
            font=("Consolas", 10, "bold"),
            foreground="#4fc3f7",
            style="Panel.TLabel"
        )
        self.lbl_time.pack(side="left", padx=(0, 16))

        # 3. Привязка (Snap)
        self.btn_snap = ttk.Button(tb, text="🧲 Привязка: [ ВКЛ ]", command=self.toggle_snap, width=20)
        self.btn_snap.pack(side="left", padx=(0, 8))

        # 4. Добавление маркера
        self.btn_add_marker = ttk.Button(tb, text="+ Маркер (M)", command=self.add_marker_at_playhead, width=14)
        self.btn_add_marker.pack(side="left", padx=(0, 4))

        # 5. Удаление маркера
        self.btn_del_marker = ttk.Button(tb, text="🗑️ Удалить (Del)", command=self.delete_selected_marker, width=14, state="disabled")
        self.btn_del_marker.pack(side="left", padx=(0, 16))

        # 6. Масштаб
        ttk.Label(tb, text="Зум:", style="Panel.TLabel").pack(side="left", padx=(4, 2))
        ttk.Button(tb, text="−", width=3, command=self.zoom_out).pack(side="left")
        ttk.Button(tb, text="+", width=3, command=self.zoom_in).pack(side="left", padx=2)
        ttk.Button(tb, text="↔ Вся ширина", width=12, command=self.zoom_fit).pack(side="left", padx=(4, 0))

    def _create_canvas(self):
        cv_frame = ttk.Frame(self, style="Panel.TFrame")
        cv_frame.pack(fill="x", expand=True)

        self.canvas = tk.Canvas(
            cv_frame,
            height=CANVAS_HEIGHT,
            bg=COLOR_CANVAS_BG,
            highlightthickness=1,
            highlightbackground="#333333"
        )
        self.canvas.pack(side="top", fill="x", expand=True)

        self.hbar = ttk.Scrollbar(cv_frame, orient="horizontal", command=self.canvas.xview)
        self.hbar.pack(side="bottom", fill="x")
        self.canvas.configure(xscrollcommand=self.hbar.set)

        # События мыши и клавиатуры
        self.canvas.bind("<Configure>", self._on_canvas_configure)
        self.canvas.bind("<Button-1>", self._on_canvas_click)
        self.canvas.bind("<B1-Motion>", self._on_canvas_drag)
        self.canvas.bind("<ButtonRelease-1>", self._on_canvas_release)
        self.canvas.bind("<MouseWheel>", self._on_mouse_wheel)
        self.canvas.bind("<Button-4>", lambda e: self.zoom_in() if (e.state & 0x0004) else self.canvas.xview_scroll(-1, "units"))
        self.canvas.bind("<Button-5>", lambda e: self.zoom_out() if (e.state & 0x0004) else self.canvas.xview_scroll(1, "units"))

    # ─── Загрузка данных ─────────────────────────────────────────────────────

    def load_audio(self, y: np.ndarray, sr: int, strong_beats=None, timeline_fps: float = 23.976):
        """Загрузить аудиоданные и отобразить волну с маркерами."""
        self.audio_y = y
        self.audio_sr = sr
        self.timeline_fps = timeline_fps
        self.duration_sec = len(y) / float(sr) if sr > 0 else 0.0

        self.player.load(y, sr)

        # Предрасчет пирамиды пиков для мгновенного зума без повторного сканирования миллионов сэмплов
        if len(y) > 0:
            target_base = 4800
            base_chunk = max(1, len(y) // target_base)
            c = len(y) // base_chunk
            self._cached_peaks = np.max(np.abs(y[:c * base_chunk].reshape(c, base_chunk)), axis=1)
        else:
            self._cached_peaks = None

        # Загрузка маркеров
        self.markers = []
        self.next_marker_id = 1
        self.snap_beats_times = []

        if strong_beats:
            for idx, b in enumerate(strong_beats):
                t = float(b.get("time", 0.0))
                self.markers.append({
                    "id": self.next_marker_id,
                    "time": t,
                    "color": b.get("color", COLOR_MARKER_DEFAULT),
                    "name": b.get("name", f"Beat {b.get('bar_index', idx) + 1}"),
                    "dynamics": b.get("dynamics", ""),
                    "strength": b.get("strength", 0.8),
                    "bar_index": b.get("bar_index", idx)
                })
                self.snap_beats_times.append(t)
                self.next_marker_id += 1

        self.selected_marker_id = None
        self.btn_del_marker.config(state="disabled")

        self.zoom_fit()
        self._update_time_label()

    def set_markers(self, strong_beats):
        """Обновить только маркеры (например, при смене настроек анализа)."""
        self.markers = []
        self.next_marker_id = 1
        self.snap_beats_times = []

        for idx, b in enumerate(strong_beats):
            t = float(b.get("time", 0.0))
            self.markers.append({
                "id": self.next_marker_id,
                "time": t,
                "color": b.get("color", COLOR_MARKER_DEFAULT),
                "name": b.get("name", f"Beat {b.get('bar_index', idx) + 1}"),
                "dynamics": b.get("dynamics", ""),
                "strength": b.get("strength", 0.8),
                "bar_index": b.get("bar_index", idx)
            })
            self.snap_beats_times.append(t)
            self.next_marker_id += 1

        self.selected_marker_id = None
        self.btn_del_marker.config(state="disabled")
        self.redraw()

    # ─── Масштаб и координаты ────────────────────────────────────────────────

    def time_to_x(self, time_sec: float) -> float:
        return time_sec * self.pixels_per_second

    def x_to_time(self, x: float) -> float:
        if self.pixels_per_second <= 0:
            return 0.0
        return max(0.0, min(self.duration_sec, x / self.pixels_per_second))

    def canvas_x(self, event_x: float) -> float:
        """Перевод экранной координаты события мыши в координату холста с учетом скролла."""
        return self.canvas.canvasx(event_x)

    def center_playhead(self):
        """Центрирование курсора воспроизведения в видимой области холста."""
        if self.duration_sec <= 0:
            return

        viewport_w = self.canvas.winfo_width()
        if viewport_w <= 1:
            self.canvas.update_idletasks()
            viewport_w = self.canvas.winfo_width()

        cur_t = self.player.get_time()
        cur_x = self.time_to_x(cur_t)
        total_width = max(viewport_w, int(self.duration_sec * self.pixels_per_second) + 40)

        if total_width <= viewport_w or total_width <= 0:
            self.canvas.xview_moveto(0.0)
            return

        # Позиционируем левый край так, чтобы cur_x оказался ровно посередине видимой области
        target_left_x = cur_x - (viewport_w / 2.0)
        target_left_x = max(0.0, min(float(total_width - viewport_w), target_left_x))
        fraction = target_left_x / float(total_width)
        self.canvas.xview_moveto(max(0.0, min(1.0, fraction)))

    def get_min_pps(self) -> float:
        """Минимальный зум строго ограничен шириной окна панели (весь трек помещается целиком)."""
        if self.duration_sec <= 0:
            return 10.0
        viewport_w = self.canvas.winfo_width()
        if viewport_w <= 1:
            self.canvas.update_idletasks()
            viewport_w = self.canvas.winfo_width()
        w = max(100, viewport_w)
        return max(0.5, (w - 20) / self.duration_sec)

    def zoom_in(self):
        min_pps = self.get_min_pps()
        self.pixels_per_second = min(self.max_pps, max(min_pps, self.pixels_per_second * 1.3))
        self.redraw()
        self.center_playhead()

    def zoom_out(self):
        min_pps = self.get_min_pps()
        if self.pixels_per_second <= min_pps * 1.02:
            # Уже достигнут минимальный зум на всю ширину окна -> фиксируем и сбрасываем скролл
            self.pixels_per_second = min_pps
            self.redraw()
            self.canvas.xview_moveto(0.0)
            return
        self.pixels_per_second = max(min_pps, self.pixels_per_second / 1.3)
        self.redraw()
        self.center_playhead()

    def zoom_fit(self):
        self.pixels_per_second = self.get_min_pps()
        self.redraw()
        self.canvas.xview_moveto(0.0)

    def _on_mouse_wheel(self, event):
        if event.state & 0x0004:  # Control зажат -> Zoom
            if event.delta > 0:
                self.zoom_in()
            else:
                self.zoom_out()
        else:  # Обычный скролл
            self.canvas.xview_scroll(int(-1 * (event.delta / 120)), "units")

    def _on_canvas_configure(self, event=None):
        if event is not None:
            w, h = event.width, event.height
            if getattr(self, "_last_canvas_size", None) == (w, h):
                return
            self._last_canvas_size = (w, h)
        if self.audio_y is not None:
            min_pps = self.get_min_pps()
            if self.pixels_per_second < min_pps:
                self.pixels_per_second = min_pps
            self.redraw()

    # ─── Отрисовка холста ────────────────────────────────────────────────────

    def redraw(self):
        """Полная перерисовка таймлайна, линейки, волны и маркеров."""
        self.canvas.delete("all")
        if self.duration_sec <= 0:
            self.canvas.create_text(
                200, 80,
                text="Аудио не загружено. Выполните анализ или запекание.",
                fill=COLOR_RULER_TEXT,
                font=("Segoe UI", 10)
            )
            return

        total_width = max(self.canvas.winfo_width(), int(self.duration_sec * self.pixels_per_second) + 40)
        self.canvas.config(scrollregion=(0, 0, total_width, CANVAS_HEIGHT))

        # 1. Линейка времени (Ruler)
        self._draw_ruler(total_width)

        # 2. Темно-серая фоновая сетка битов и времени на теле таймлайна
        self._draw_grid(total_width)

        # 3. Плавная огибающая аудио (Waveform) с мягким полупрозрачным фоном
        self._draw_waveform(total_width)

        # 4. Маркеры
        self._draw_markers()

        # 5. Плейхед (курсор воспроизведения)
        self._draw_playhead()

    def _draw_ruler(self, total_width: int):
        self.canvas.create_rectangle(0, 0, total_width, RULER_HEIGHT, fill=COLOR_RULER_BG, outline="")
        self.canvas.create_line(0, RULER_HEIGHT, total_width, RULER_HEIGHT, fill=COLOR_RULER_LINE, width=1)

        # Шаг засечек в зависимости от масштаба
        if self.pixels_per_second > 100:
            step_sec = 0.5
        elif self.pixels_per_second > 40:
            step_sec = 1.0
        elif self.pixels_per_second > 15:
            step_sec = 5.0
        else:
            step_sec = 10.0

        cur_t = 0.0
        while cur_t <= self.duration_sec:
            x = self.time_to_x(cur_t)
            is_major = (cur_t % (step_sec * 2) < 0.001) or (cur_t == 0)

            tick_len = 10 if is_major else 5
            self.canvas.create_line(x, RULER_HEIGHT - tick_len, x, RULER_HEIGHT, fill=COLOR_RULER_TEXT, width=1)

            if is_major:
                tc = format_timecode(cur_t)
                self.canvas.create_text(x + 2, 8, text=tc, fill=COLOR_RULER_TEXT, anchor="nw", font=("Consolas", 8))

            cur_t += step_sec

    def _draw_grid(self, total_width: int):
        """Отрисовка темно-серой сетки секунд и битов на теле таймлайна."""
        # 1. Секундные вертикальные засечки
        if self.pixels_per_second > 100:
            step_sec = 0.5
        elif self.pixels_per_second > 40:
            step_sec = 1.0
        elif self.pixels_per_second > 15:
            step_sec = 5.0
        else:
            step_sec = 10.0

        cur_t = 0.0
        while cur_t <= self.duration_sec:
            x = self.time_to_x(cur_t)
            if cur_t > 0:
                self.canvas.create_line(x, RULER_HEIGHT, x, CANVAS_HEIGHT, fill=COLOR_GRID_SEC, width=1)
            cur_t += step_sec

        # 2. Темно-серая сетка битов (музыкальных долей)
        for bt in self.snap_beats_times:
            x = self.time_to_x(bt)
            self.canvas.create_line(x, RULER_HEIGHT, x, CANVAS_HEIGHT, fill=COLOR_GRID_BEAT, dash=(3, 3), width=1)

    def _draw_waveform(self, total_width: int):
        """Отрисовка плавной огибающей с мягким полупрозрачным фоном (LOD + векторная оптимизация)."""
        if self.audio_y is None or len(self.audio_y) == 0:
            return

        mid_y = RULER_HEIGHT + (WAVEFORM_HEIGHT / 2.0)
        max_half_h = (WAVEFORM_HEIGHT / 2.0) - 6.0

        # LOD: Ограничиваем максимальное число точек до 2400.
        # Даже на 4K-мониторах 2400 точек дают идеальную детализацию,
        # полностью исключая генерацию 50 000+ лишних примитивов на холсте при глубоком зуме.
        max_peaks = 2400
        target_points = min(max_peaks, max(30, int(self.duration_sec * self.pixels_per_second)))

        # Быстрая выборка из предварительно кэшированных пиков (0.05 мс вместо сканирования миллионов сэмплов)
        cached = getattr(self, "_cached_peaks", None)
        if cached is not None and len(cached) >= target_points:
            step = max(1, len(cached) // target_points)
            c_z = len(cached) // step
            peaks = np.max(cached[:c_z * step].reshape(c_z, step), axis=1)
        else:
            samples_per_pixel = max(1, len(self.audio_y) // target_points)
            chunks = len(self.audio_y) // samples_per_pixel
            trimmed = self.audio_y[:chunks * samples_per_pixel].reshape(chunks, samples_per_pixel)
            peaks = np.max(np.abs(trimmed), axis=1)

        # Сглаживание скользящим окном для органичной плавной формы
        window_size = 5
        if len(peaks) > window_size:
            kernel = np.ones(window_size) / float(window_size)
            peaks = np.convolve(peaks, kernel, mode="same")

        # Длина аудиодорожки в пикселях с учетом текущего масштаба времени
        track_width = max(10.0, self.duration_sec * self.pixels_per_second)

        # Векторизованная генерация координат полигона и контура
        N = len(peaks)
        x_coords = np.linspace(0, track_width, N, endpoint=False)
        h_coords = np.maximum(1.0, peaks * max_half_h)
        top_y = mid_y - h_coords
        bot_y = mid_y + h_coords

        top_pts = np.column_stack((x_coords, top_y))
        bot_pts = np.column_stack((x_coords[::-1], bot_y[::-1]))

        poly_pts = np.vstack([top_pts, [[track_width, mid_y]], bot_pts, [[0, mid_y]]]).ravel().tolist()
        top_contour = top_pts.ravel().tolist()
        bot_contour = np.column_stack((x_coords, bot_y)).ravel().tolist()

        # 1. Мягкий полупрозрачный фоновый полигон огибающей
        self.canvas.create_polygon(poly_pts, fill=COLOR_WAVE_BG, outline="", tags="waveform")

        # 2. Плавные верхний и нижний контуры
        if len(top_contour) >= 4:
            self.canvas.create_line(top_contour, fill=COLOR_WAVE_CONTOUR, width=1, smooth=True, tags="waveform")
            self.canvas.create_line(bot_contour, fill=COLOR_WAVE_CONTOUR, width=1, smooth=True, tags="waveform")

        # 3. Тонкая осевая линия середины
        self.canvas.create_line(0, mid_y, track_width, mid_y, fill=COLOR_WAVE_CENTER, width=1, tags="waveform")

    def _draw_markers(self):
        for m in self.markers:
            m_id = m["id"]
            t = m["time"]
            color = m.get("color", COLOR_MARKER_DEFAULT)
            is_selected = (m_id == self.selected_marker_id)
            x = self.time_to_x(t)

            # Вертикальная линия через всю волну
            line_w = 2 if is_selected else 1
            line_color = COLOR_SELECTION if is_selected else color
            self.canvas.create_line(
                x, RULER_HEIGHT, x, CANVAS_HEIGHT,
                fill=line_color,
                width=line_w,
                dash=(4, 2) if not is_selected else (),
                tags=(f"marker_line_{m_id}", "marker_item")
            )

            # Флажок на линейке
            poly_color = COLOR_SELECTION if is_selected else color
            pts = [x - 5, 2, x + 5, 2, x + 5, 14, x, 22, x - 5, 14]
            self.canvas.create_polygon(
                pts,
                fill=poly_color,
                outline="#ffffff" if is_selected else "#000000",
                width=1,
                tags=(f"marker_handle_{m_id}", "marker_handle", "marker_item")
            )

            # Номер или имя доли
            name = m.get("name", "")
            if name.startswith("Beat "):
                b_num = name.split(" ")[-1]
                self.canvas.create_text(
                    x, 8, text=b_num,
                    fill="#000000" if is_selected else "#ffffff",
                    font=("Segoe UI", 7, "bold"),
                    tags=(f"marker_text_{m_id}", "marker_item")
                )

    def _draw_playhead(self):
        cur_t = self.player.get_time()
        x = self.time_to_x(cur_t)

        # Линия
        self.canvas.create_line(
            x, 0, x, CANVAS_HEIGHT,
            fill=COLOR_PLAYHEAD,
            width=2,
            tags="playhead"
        )
        # Стрелка-указатель на линейке
        pts = [x - 6, 0, x + 6, 0, x + 6, 8, x, 16, x - 6, 8]
        self.canvas.create_polygon(
            pts,
            fill=COLOR_PLAYHEAD,
            outline="#000000",
            width=1,
            tags="playhead"
        )

    def _update_playhead_pos(self):
        """Быстрое обновление позиции плейхеда без полной перерисовки холста."""
        cur_t = self.player.get_time()
        x = self.time_to_x(cur_t)
        self.canvas.delete("playhead")

        self.canvas.create_line(
            x, 0, x, CANVAS_HEIGHT,
            fill=COLOR_PLAYHEAD,
            width=2,
            tags="playhead"
        )
        pts = [x - 6, 0, x + 6, 0, x + 6, 8, x, 16, x - 6, 8]
        self.canvas.create_polygon(
            pts,
            fill=COLOR_PLAYHEAD,
            outline="#000000",
            width=1,
            tags="playhead"
        )
        self._update_time_label()

    def _update_time_label(self):
        cur_t = self.player.get_time()
        self.lbl_time.config(text=f"{format_timecode(cur_t)} / {format_timecode(self.duration_sec)}")

    # ─── Интерактивность мыши ────────────────────────────────────────────────

    def _on_canvas_click(self, event):
        cx = self.canvas_x(event.x)
        cy = event.y

        # Фокус на холст для уверенного приема клавиш
        self.canvas.focus_set()

        # 1. Выделение маркера возможно ТОЛЬКО по щелчку на его головке (флажке) на линейке (cy <= RULER_HEIGHT)
        if cy <= RULER_HEIGHT:
            clicked_marker = self._find_marker_near_x(cx, radius_px=8)
            if clicked_marker is not None:
                # Выбор маркера и начало перетаскивания
                self.selected_marker_id = clicked_marker["id"]
                self._dragging_marker_id = clicked_marker["id"]
                self._drag_start_time = clicked_marker["time"]
                self._drag_last_x = cx
                self.btn_del_marker.config(state="normal")
                self.redraw()
                return

        # 2. Если кликнули мимо головки маркера (по линейке или по телу волны) ->
        # снимаем выделение маркера, сбрасываем драг маркера и переходим к скраббингу плейхеда
        self._dragging_marker_id = None
        self._drag_start_time = None
        if self.selected_marker_id is not None:
            self.selected_marker_id = None
            self.btn_del_marker.config(state="disabled")
            self.redraw()

        # Клик по линейке или телу волны -> точное позиционирование плейхеда (Seek)
        target_t = self.x_to_time(cx)
        self.player.seek(target_t)
        self._is_scrubbing_playhead = True
        self._update_playhead_pos()

    def _on_canvas_drag(self, event):
        cx = self.canvas_x(event.x)

        if self._dragging_marker_id is not None:
            # Перетаскивание маркера
            target_t = self.x_to_time(cx)
            if self.snap_enabled:
                target_t = self._apply_snap(target_t)

            # Обновляем координаты маркера в памяти
            for m in self.markers:
                if m["id"] == self._dragging_marker_id:
                    m["time"] = target_t
                    break
            self.redraw()
            return

        if self._is_scrubbing_playhead:
            # Скраббинг курсора воспроизведения
            target_t = self.x_to_time(cx)
            self.player.seek(target_t)
            self._update_playhead_pos()

    def _on_canvas_release(self, event):
        if self._dragging_marker_id is not None:
            # Завершение перетаскивания -> запись в CommandManager для Undo
            final_marker = next((m for m in self.markers if m["id"] == self._dragging_marker_id), None)
            if final_marker:
                new_t = final_marker["time"]
                old_t = self._drag_start_time
                if abs(new_t - old_t) > 0.01:
                    cmd = MoveTimelineMarkerCommand(
                        self, self._dragging_marker_id, old_t, new_t, log_fn=self.log_fn
                    )
                    if self.command_manager:
                        self.command_manager.execute(cmd)
                    self._notify_markers_changed()

            self._dragging_marker_id = None

        self._is_scrubbing_playhead = False

    def _find_marker_near_x(self, cx: float, radius_px: float = 8.0):
        for m in self.markers:
            mx = self.time_to_x(m["time"])
            if abs(mx - cx) <= radius_px:
                return m
        return None

    def _apply_snap(self, time_sec: float, snap_radius_sec: float = None) -> float:
        """Магнитное притягивание к ближайшей доле или тактовой сетке."""
        if snap_radius_sec is None:
            snap_radius_sec = 8.0 / max(1.0, self.pixels_per_second)

        # 1. Привязка к исходным долям
        best_diff = snap_radius_sec
        snapped_time = time_sec

        for bt in self.snap_beats_times:
            diff = abs(bt - time_sec)
            if diff < best_diff:
                best_diff = diff
                snapped_time = bt

        # 2. Привязка к целым секундам
        sec_round = round(time_sec)
        if abs(sec_round - time_sec) < best_diff:
            snapped_time = float(sec_round)

        return snapped_time

    # ─── Команды модификации маркеров (вызываются через CommandManager) ────────

    def _apply_marker_move(self, marker_id: int, new_time: float):
        for m in self.markers:
            if m["id"] == marker_id:
                m["time"] = new_time
                break
        self.redraw()
        self._notify_markers_changed()

    def _apply_marker_add(self, marker_data: dict):
        # Добавляем или восстанавливаем маркер
        existing = [m for m in self.markers if m["id"] == marker_data["id"]]
        if not existing:
            self.markers.append(dict(marker_data))
            self.markers.sort(key=lambda x: x["time"])
            if marker_data["id"] >= self.next_marker_id:
                self.next_marker_id = marker_data["id"] + 1
        self.selected_marker_id = marker_data["id"]
        self.btn_del_marker.config(state="normal")
        self.redraw()
        self._notify_markers_changed()

    def _apply_marker_delete(self, marker_id: int):
        self.markers = [m for m in self.markers if m["id"] != marker_id]
        if self.selected_marker_id == marker_id:
            self.selected_marker_id = None
            self.btn_del_marker.config(state="disabled")
        self.redraw()
        self._notify_markers_changed()

    def _notify_markers_changed(self):
        if self.on_markers_changed:
            self.on_markers_changed(self.get_strong_beats())

    def get_strong_beats(self):
        """Получить текущий актуальный список долей для экспорта и DaVinci."""
        sorted_m = sorted(self.markers, key=lambda x: x["time"])
        out = []
        for idx, m in enumerate(sorted_m):
            out.append({
                "time": float(m["time"]),
                "strength": float(m.get("strength", 0.8)),
                "name": m.get("name", f"Beat {idx + 1}"),
                "dynamics": m.get("dynamics", ""),
                "bar_index": idx,
                "color": m.get("color", COLOR_MARKER_DEFAULT)
            })
        return out

    # ─── Действия пользователя ───────────────────────────────────────────────

    def add_marker_at_playhead(self):
        """Добавить новый маркер в позицию текущего курсора воспроизведения."""
        t = self.player.get_time()
        if self.snap_enabled:
            t = self._apply_snap(t)

        m_data = {
            "id": self.next_marker_id,
            "time": t,
            "color": COLOR_MARKER_DEFAULT,
            "name": f"Beat {len(self.markers) + 1}",
            "dynamics": "manual",
            "strength": 0.8,
            "bar_index": len(self.markers)
        }
        cmd = AddTimelineMarkerCommand(self, m_data, log_fn=self.log_fn)
        if self.command_manager:
            self.command_manager.execute(cmd)
        else:
            self._apply_marker_add(m_data)

    def delete_selected_marker(self):
        """Удалить выбранный маркер."""
        if self.selected_marker_id is None:
            return

        m_data = next((m for m in self.markers if m["id"] == self.selected_marker_id), None)
        if m_data:
            cmd = DeleteTimelineMarkerCommand(self, m_data, log_fn=self.log_fn)
            if self.command_manager:
                self.command_manager.execute(cmd)
            else:
                self._apply_marker_delete(self.selected_marker_id)

    def toggle_snap(self):
        """Переключить магнитную привязку."""
        self.snap_enabled = not self.snap_enabled
        status = "[ ВКЛ ]" if self.snap_enabled else "[ ВЫКЛ ]"
        self.btn_snap.config(text=f"🧲 Привязка: {status}")

    def toggle_play(self):
        """Воспроизведение / пауза по Space."""
        if self.audio_y is None:
            return

        is_now_playing = self.player.toggle_play()
        if is_now_playing:
            self.btn_play.config(text="⏸ Пауза (Space)")
            self._start_playback_loop()
        else:
            self.btn_play.config(text="▶ Воспр. (Space)")
            self._stop_playback_loop()

    def _start_playback_loop(self):
        self._stop_playback_loop()
        self._tick_playback()

    def _stop_playback_loop(self):
        if self._playback_job:
            self.after_cancel(self._playback_job)
            self._playback_job = None

    def _tick_playback(self):
        if self.player.is_playing:
            self._update_playhead_pos()
            # Автоскролл холста вслед за плейхедом
            cur_x = self.time_to_x(self.player.get_time())
            view_start = self.canvas.canvasx(0)
            view_end = view_start + self.canvas.winfo_width()
            if cur_x > view_end - 40 or cur_x < view_start:
                scroll_frac = max(0.0, (cur_x - 50) / max(1.0, self.duration_sec * self.pixels_per_second))
                self.canvas.xview_moveto(scroll_frac)

            self._playback_job = self.after(33, self._tick_playback)

    def _on_playback_finished(self):
        self.after(0, lambda: self.btn_play.config(text="▶ Воспр. (Space)"))
        self._stop_playback_loop()
        self._update_playhead_pos()

    def shutdown(self):
        """Корректное завершение потоков при закрытии окна."""
        self._stop_playback_loop()
        self.player.stop()
