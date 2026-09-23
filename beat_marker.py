#!/usr/bin/env python3
"""beat_marker.py — Автоматическая детекция музыкальных битов и расстановка маркеров в DaVinci Resolve.

Возможности:
- Автономный аудиоанализ (темп BPM, музыкальный размер 3/4 и 4/4, RMS-огибающая).
- Локализованный FFmpeg для безопасного извлечения и склейки аудиодорожек любой сложности.
- Расстановка маркеров на шкалу таймлайна или отдельные клипы в DaVinci Resolve.
- Сохранение результатов разметки в формате JSON.
"""

import sys
import os
import json
import shutil
import argparse
import subprocess
import tempfile
from pathlib import Path

# Windows console encoding for Unicode output
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

if getattr(sys, "frozen", False):
    SCRIPT_DIR = Path(sys.executable).parent.resolve()
else:
    SCRIPT_DIR = Path(__file__).parent.resolve()

# Self-relaunch in project .venv if available and not already inside it (only for script mode)
if not getattr(sys, "frozen", False):
    _VENV_PYTHON = SCRIPT_DIR / ".venv" / "Scripts" / "python.exe"
    if not _VENV_PYTHON.exists():
        _VENV_PYTHON = SCRIPT_DIR / ".venv" / "bin" / "python"

    if __name__ == "__main__" and _VENV_PYTHON.exists() and sys.executable.lower() != str(_VENV_PYTHON).lower():
        subprocess.check_call([str(_VENV_PYTHON)] + sys.argv)
        raise SystemExit(0)

import numpy as np
import librosa


# ─── FFmpeg Resolution ────────────────────────────────────────────────────────

def get_ffmpeg_path() -> str:
    """Получить путь к исполняемому файлу ffmpeg.
    
    Приоритет:
    1. Локальный каталог bin/ (bin/ffmpeg.exe или bin/ffmpeg)
    2. Системный PATH
    3. Fallback имя команды 'ffmpeg'
    """
    local_bin = SCRIPT_DIR / "bin"
    for name in ["ffmpeg.exe", "ffmpeg"]:
        p = local_bin / name
        if p.exists():
            return str(p)
    sys_ffmpeg = shutil.which("ffmpeg")
    if sys_ffmpeg:
        return sys_ffmpeg
    return "ffmpeg"


# ─── DaVinci Resolve API Discovery ───────────────────────────────────────────

def _setup_davinci_path():
    """Добавить стандартные пути к модулям DaVinci Resolve Scripting API в sys.path."""
    potential_paths = [
        r'C:\ProgramData\Blackmagic Design\DaVinci Resolve\Support\Developer\Scripting\Modules',
        '/Library/Application Support/Blackmagic Design/DaVinci Resolve/Developer/Scripting/Modules',
        '/opt/resolve/Developer/Scripting/Modules',
    ]
    # Также учитываем переменную окружения RESOLVE_SCRIPT_API если задана
    env_api = os.environ.get("RESOLVE_SCRIPT_API")
    if env_api:
        potential_paths.insert(0, os.path.join(env_api, "Modules"))

    for p in potential_paths:
        if os.path.exists(p) and p not in sys.path:
            sys.path.insert(0, p)

_setup_davinci_path()
try:
    import DaVinciResolveScript as dvr
except ImportError:
    dvr = None


# ─── DaVinci Connection ──────────────────────────────────────────────────────

def connect():
    """Подключиться к DaVinci Resolve Studio."""
    if dvr is None:
        print("ERROR: DaVinciResolveScript module not found", file=sys.stderr)
        return None
    resolve = dvr.scriptapp('Resolve')
    if not resolve:
        print("ERROR: Cannot connect to DaVinci Resolve. Is it running?", file=sys.stderr)
        return None
    proj = resolve.GetProjectManager().GetCurrentProject()
    if not proj:
        print("ERROR: No project open in DaVinci Resolve", file=sys.stderr)
        return None
    print(f"Подключение: {resolve.GetProductName()} {resolve.GetVersionString()} | Проект: {proj.GetName()}")
    return proj


def set_current_timeline(proj, name):
    """Переключиться на таймлайн по имени."""
    for i in range(1, proj.GetTimelineCount() + 1):
        t = proj.GetTimelineByIndex(i)
        if t and t.GetName().lower() == name.lower():
            proj.SetCurrentTimeline(t)
            return t
    print(f"Таймлайн '{name}' не найден", file=sys.stderr)
    return None


def get_audio_file_from_timeline(tl, track_type="audio", track_index=2, item_index=0):
    """Получить путь к аудиофайлу с таймлайна."""
    items = tl.GetItemListInTrack(track_type, track_index) or []
    if not items:
        print(f"ERROR: No items on track {track_type} {track_index}", file=sys.stderr)
        return None, None

    if item_index >= len(items):
        print(f"ERROR: Item index {item_index} out of range (track has {len(items)} items)", file=sys.stderr)
        return None, None

    item = items[item_index]
    mpi = item.GetMediaPoolItem()
    if not mpi:
        print("ERROR: No MediaPoolItem for this timeline item", file=sys.stderr)
        return None, None

    file_path = mpi.GetClipProperty("File Path") or ""
    if not file_path or not os.path.exists(file_path):
        print(f"ERROR: File not found: {file_path}", file=sys.stderr)
        return None, None

    print(f"Аудиофайл: {file_path}")
    return file_path, item


# ─── Safe Audio Loading ──────────────────────────────────────────────────────

def load_audio_safely(audio_path, sr=22050):
    """Безопасная загрузка аудиофайла с нормализацией пикового уровня."""
    try:
        y, sr = librosa.load(audio_path, sr=sr)
    except Exception:
        # Fallback на извлечение через FFmpeg
        ffmpeg_bin = get_ffmpeg_path()
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            tmp_wav = tmp.name
        try:
            cmd = [ffmpeg_bin, "-y", "-i", str(audio_path), "-vn", "-acodec", "pcm_s16le", "-ar", str(sr), "-ac", "1", tmp_wav]
            subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
            y, sr = librosa.load(tmp_wav, sr=sr)
        finally:
            if os.path.exists(tmp_wav):
                try:
                    os.remove(tmp_wav)
                except Exception:
                    pass

    # Пиковая нормализация амплитуды к 1.0 для стабильного расчета RMS и onset-детекции
    if y is not None and len(y) > 0 and np.max(np.abs(y)) > 0:
        y = librosa.util.normalize(y)

    return y, sr


# ─── Beat Detection ──────────────────────────────────────────────────────────

def detect_beats(audio_path, sr=22050):
    """Детекция битов и расчёт огибающих в аудиофайле."""
    print(f"Загрузка аудио: {audio_path}")
    y, sr = load_audio_safely(audio_path, sr=sr)
    duration = len(y) / sr

    print(f"Длина: {duration:.1f} сек, SR: {sr}")

    # Темп и позиции битов
    tempo, beat_frames = librosa.beat.beat_track(y=y, sr=sr)
    if hasattr(tempo, '__len__'):
        tempo = float(tempo[0])
    else:
        tempo = float(tempo)
    beat_times = librosa.frames_to_time(beat_frames, sr=sr)

    # Onset strength для каждой доли
    onset_env = librosa.onset.onset_strength(y=y, sr=sr)
    onset_padded = np.pad(onset_env, (0, max(0, len(beat_frames) - len(onset_env))))
    beat_onset_strengths = [float(v) for v in onset_padded[beat_frames[:len(onset_padded)]]]

    # RMS energy envelope (для оценки динамики громкости)
    rms_env = librosa.feature.rms(y=y)[0]
    rms_padded = np.pad(rms_env, (0, max(0, len(beat_frames) - len(rms_env))))
    beat_rms = [float(v) for v in rms_padded[beat_frames[:len(rms_padded)]]]

    print(f"Tempo: {tempo:.1f} BPM, Битов: {len(beat_times)}")

    return {
        "tempo": tempo,
        "duration": duration,
        "beat_times": beat_times.tolist(),
        "beat_frames": beat_frames.tolist(),
        "beat_onset_strengths": beat_onset_strengths,
        "beat_rms": beat_rms,
        "sr": sr,
    }


def detect_time_signature(beat_data):
    """Определение музыкального размера (3/4 или 4/4)."""
    beat_times = np.array(beat_data["beat_times"])
    if len(beat_times) < 8:
        return 4, "4/4"

    strengths = np.array(beat_data["beat_onset_strengths"])

    def group_strengths(strengths, group_size):
        n_groups = len(strengths) // group_size
        if n_groups < 2:
            return 0
        strong = strengths[:n_groups * group_size].reshape(n_groups, group_size)
        strong_beats = strong[:, 0]
        weak_beats = strong[:, 1:].flatten()
        if len(weak_beats) == 0:
            return 0
        contrast = np.mean(strong_beats) / (np.mean(weak_beats) + 1e-10)
        return contrast

    contrast_3 = group_strengths(strengths, 3)
    contrast_4 = group_strengths(strengths, 4)

    if contrast_3 > contrast_4 * 1.15:
        return 3, "3/4"
    else:
        return 4, "4/4"


# ─── Beat Filtering ──────────────────────────────────────────────────────────

def filter_strong_beats(beat_data, beats_per_bar=4, frequency=0):
    """Отфильтровать биты по частоте маркеров."""
    beat_times = beat_data["beat_times"]
    strengths = beat_data["beat_onset_strengths"]
    sr = beat_data["sr"]

    beats_per_marker = max(1, round(beats_per_bar * (2 ** -frequency)))

    markers = []
    for i in range(0, len(beat_times), beats_per_marker):
        bar_idx = int(i // beats_per_bar)
        markers.append({
            "time": float(beat_times[i]),
            "frame": int(librosa.time_to_frames(beat_times[i], sr=sr)),
            "strength": float(strengths[i]) if i < len(strengths) else 0.0,
            "bar_index": bar_idx,
        })

    # Экстраполяция на 2 такта вперед в конце трека
    if len(markers) >= 2:
        interval = float(markers[-1]["time"] - markers[-2]["time"])
        last_time = float(markers[-1]["time"])
        for k in range(1, 3):
            new_time = last_time + interval * k
            markers.append({
                "time": float(new_time),
                "frame": int(librosa.time_to_frames(new_time, sr=sr)),
                "strength": 0.0,
                "bar_index": -1,
            })

    return markers


def filter_adaptive_beats(beat_data, beats_per_bar=4, freq_quiet=-1, freq_loud=0, threshold=None):
    """Адаптивная фильтрация битов по динамике (громкости)."""
    beat_times = np.array(beat_data["beat_times"])
    strengths = np.array(beat_data["beat_onset_strengths"])
    rms_values = np.array(beat_data["beat_rms"])
    sr = beat_data["sr"]

    if len(beat_times) == 0:
        return []

    median_rms = float(np.median(rms_values))
    if threshold is None:
        threshold = median_rms
        print(f"Порог RMS (медиана): {threshold:.4f}")
    else:
        print(f"Порог RMS (ручной): {threshold:.4f}")

    bars_skip_quiet = max(1, round(2 ** -freq_quiet))
    bars_skip_loud = max(1, round(2 ** -freq_loud))

    num_bars = len(beat_times) // beats_per_bar
    bar_rms = []
    for bar_idx in range(num_bars):
        start = bar_idx * beats_per_bar
        end = start + beats_per_bar
        bar_rms.append(float(np.mean(rms_values[start:end])))

    bar_dynamics = ["loud" if rms >= threshold else "quiet" for rms in bar_rms]

    markers = []
    last_marker_bar = -max(bars_skip_quiet, bars_skip_loud) - 1

    for bar_idx in range(num_bars):
        is_loud = bar_dynamics[bar_idx] == "loud"
        required_skip = bars_skip_loud if is_loud else bars_skip_quiet

        if bar_idx - last_marker_bar >= required_skip:
            beat_idx = bar_idx * beats_per_bar
            markers.append({
                "time": float(beat_times[beat_idx]),
                "frame": int(librosa.time_to_frames(beat_times[beat_idx], sr=sr)),
                "strength": float(strengths[beat_idx]) if beat_idx < len(strengths) else 0,
                "bar_index": bar_idx,
                "dynamics": bar_dynamics[bar_idx],
            })
            last_marker_bar = bar_idx

    if len(markers) >= 2:
        interval = markers[-1]["time"] - markers[-2]["time"]
        last_time = markers[-1]["time"]
        for k in range(1, 3):
            new_time = last_time + interval * k
            markers.append({
                "time": new_time,
                "frame": int(librosa.time_to_frames(new_time, sr=sr)),
                "strength": 0,
                "bar_index": -1,
                "dynamics": "quiet",
            })

    return markers


# ─── Markers Placement ───────────────────────────────────────────────────────

def place_markers(tl, strong_beats, color="Red", timeline_item=None, timeline_items=None):
    """Расстановка маркеров в DaVinci Resolve.
    
    Поддерживает:
    - Шкалу таймлайна: timeline_items=None и timeline_item=None
    - Один или множество клипов на треке: timeline_items=[item1, item2, ...]
    """
    timeline_fps = float(tl.GetSetting("timelineFrameRate") or 23.976)

    # Нормализуем список целевых клипов
    target_items = None
    if timeline_items is not None:
        target_items = timeline_items if isinstance(timeline_items, list) else [timeline_items]
    elif timeline_item is not None:
        target_items = timeline_item if isinstance(timeline_item, list) else [timeline_item]

    # 1. Очистка старых маркеров указанного цвета
    if target_items:
        for item in target_items:
            for f, m in list((item.GetMarkers() or {}).items()):
                if m.get("color") == color:
                    item.DeleteMarkerAtFrame(f)
    else:
        for f, m in list((tl.GetMarkers() or {}).items()):
            if m.get("color") == color:
                tl.DeleteMarkerAtFrame(f)

    placed = 0

    # 2. Расстановка новых маркеров
    for b in strong_beats:
        timeline_frame = int(b["time"] * timeline_fps)
        name = f"Beat {b.get('bar_index', 0) + 1}"
        note = b.get("dynamics", "")
        custom_data = json.dumps({"time": b["time"], "strength": b.get("strength", 0)})

        if target_items:
            for item in target_items:
                start = item.GetStart() or 0
                dur = item.GetDuration() or 0
                end = item.GetEnd() or (start + dur)
                if start <= timeline_frame < end:
                    clip_frame = timeline_frame - start
                    if 0 <= clip_frame < dur:
                        try:
                            if item.AddMarker(clip_frame, color, name, note, 1, custom_data):
                                placed += 1
                        except Exception:
                            pass
                    break
        else:
            try:
                if tl.AddMarker(timeline_frame, color, name, note, 1, custom_data):
                    placed += 1
            except Exception:
                pass

    return placed


def delete_markers(tl, color="Red", timeline_item=None, timeline_items=None):
    """Удалить маркеры заданного цвета с клипов (одного/многих) или таймлайна."""
    target_items = None
    if timeline_items is not None:
        target_items = timeline_items if isinstance(timeline_items, list) else [timeline_items]
    elif timeline_item is not None:
        target_items = timeline_item if isinstance(timeline_item, list) else [timeline_item]

    deleted = 0
    if target_items:
        for item in target_items:
            for f, m in list((item.GetMarkers() or {}).items()):
                if m.get("color") == color:
                    if item.DeleteMarkerAtFrame(f):
                        deleted += 1
    elif tl:
        for f, m in list((tl.GetMarkers() or {}).items()):
            if m.get("color") == color:
                if tl.DeleteMarkerAtFrame(f):
                    deleted += 1

    return deleted


# ─── Track Inspection & Baking ───────────────────────────────────────────────

def get_track_state(tl, track_index=2):
    """Считать полную структуру дорожки аудио и определить сложность монтажа."""
    items = tl.GetItemListInTrack("audio", track_index) or []
    tl_fps = float(tl.GetSetting("timelineFrameRate") or 23.976)
    if not items:
        return {"items_count": 0, "clips": [], "is_complex": False, "timeline_fps": tl_fps, "total_duration_sec": 0.0}

    clips = []
    is_complex = len(items) > 1

    for idx, item in enumerate(items):
        mpi = item.GetMediaPoolItem()
        fp = mpi.GetClipProperty("File Path") if mpi else ""
        mtime = os.path.getmtime(fp) if fp and os.path.exists(fp) else 0.0
        start = item.GetStart() or 0
        end = item.GetEnd() or 0
        dur = item.GetDuration() or 0
        raw_left = item.GetLeftOffset()
        left_off = int(raw_left) if raw_left is not None else 0

        if end <= start and dur > 0:
            end = start + dur

        if idx == 0 and (start > 0 or left_off > 0):
            is_complex = True

        clips.append({
            "index": idx,
            "name": item.GetName() or (os.path.basename(fp) if fp else f"Clip_{idx}"),
            "file_path": fp,
            "file_mtime": mtime,
            "start_frame": start,
            "end_frame": end,
            "duration_frames": dur,
            "left_offset": left_off,
        })

    total_dur_frames = max((c["end_frame"] for c in clips), default=0)
    total_dur_sec = total_dur_frames / tl_fps if tl_fps > 0 else 0.0

    return {
        "timeline_name": tl.GetName(),
        "timeline_fps": tl_fps,
        "track_index": track_index,
        "items_count": len(items),
        "is_complex": is_complex,
        "total_duration_frames": total_dur_frames,
        "total_duration_sec": total_dur_sec,
        "clips": clips,
    }


def is_track_state_changed(current_state, state_file):
    """Проверить, изменился ли монтаж трека по сравнению с сохраненным track_state.json."""
    if not os.path.exists(state_file):
        return True
    try:
        with open(state_file, "r", encoding="utf-8") as f:
            saved = json.load(f)
        if saved.get("items_count") != current_state.get("items_count"):
            return True
        if saved.get("total_duration_frames") != current_state.get("total_duration_frames"):
            return True
        if saved.get("is_complex") != current_state.get("is_complex"):
            return True
        saved_clips = saved.get("clips", [])
        curr_clips = current_state.get("clips", [])
        if len(saved_clips) != len(curr_clips):
            return True
        for sc, cc in zip(saved_clips, curr_clips):
            if sc.get("file_path") != cc.get("file_path"):
                return True
            if sc.get("start_frame") != cc.get("start_frame"):
                return True
            if sc.get("end_frame") != cc.get("end_frame"):
                return True
            if sc.get("left_offset") != cc.get("left_offset"):
                return True
            if abs(sc.get("file_mtime", 0) - cc.get("file_mtime", 0)) > 1.0:
                return True
        return False
    except Exception:
        return True


def bake_timeline_audio(tl, track_index=2, session_dir=None, log_fn=print):
    """Сформировать и запечь сквозной аудиофайл дорожки (timeline_A2_baked.wav).
    
    Поддерживает умное кэширование: если монтаж не менялся, переиспользует существующий слепок.
    """
    track_state = get_track_state(tl, track_index)
    if track_state["items_count"] == 0:
        return None, track_state

    if session_dir is None:
        session_dir = SCRIPT_DIR / "output" / "audio_baked"

    audio_dir = Path(session_dir) / "audio"
    audio_dir.mkdir(parents=True, exist_ok=True)
    baked_wav = audio_dir / f"timeline_A{track_index}_baked.wav"
    state_file = audio_dir / f"track_state_A{track_index}.json"

    # Проверяем кэш
    if baked_wav.exists() and not is_track_state_changed(track_state, state_file):
        log_fn(f"[Кэш] Слепок аудио актуален ({track_state['total_duration_sec']:.1f} сек), используется {baked_wav.name}")
        return str(baked_wav), track_state

    # Пересоздаем слепок с помощью FFmpeg
    ffmpeg_bin = get_ffmpeg_path()
    is_complex = track_state["is_complex"]
    tl_fps = track_state["timeline_fps"]
    clips = track_state["clips"]

    if not is_complex and len(clips) == 1:
        log_fn(f"[Запекание] Простой режим: извлечение аудио {clips[0]['name']}...")
        src_path = clips[0]["file_path"]
        cmd = [
            ffmpeg_bin, "-y", "-i", src_path,
            "-vn", "-acodec", "pcm_s16le", "-ar", "22050", "-ac", "1",
            str(baked_wav)
        ]
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    else:
        log_fn(f"[Запекание] Сложный режим (монтаж/подрезка: {len(clips)} сегментов) -> Сборка сквозного аудио через FFmpeg...")
        temp_slices = []
        concat_list = audio_dir / f"_concat_list_A{track_index}.txt"
        try:
            prev_end = 0
            for idx, c in enumerate(clips):
                c_start = c.get("start_frame") or 0
                c_dur = c.get("duration_frames") or 0
                c_off = c.get("left_offset") or 0
                c_end = c.get("end_frame") or (c_start + c_dur)
                src_fp = c.get("file_path") or ""

                if not src_fp or not os.path.exists(src_fp):
                    log_fn(f"[Предупреждение] Файл сегмента {idx} не найден: {src_fp}")
                    continue

                # 1. Зазор / тишина перед клипом (включая задержку от 0 кадра)
                if c_start > prev_end:
                    gap_frames = c_start - prev_end
                    gap_dur = gap_frames / tl_fps
                    silence_wav = audio_dir / f"_temp_silence_{idx}.wav"
                    sil_cmd = [
                        ffmpeg_bin, "-y", "-f", "lavfi",
                        "-i", "anullsrc=r=22050:cl=mono",
                        "-t", f"{gap_dur:.4f}",
                        "-acodec", "pcm_s16le", str(silence_wav)
                    ]
                    subprocess.run(sil_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
                    temp_slices.append(silence_wav)

                # 2. Вырезка фрагмента с учетом left_offset
                start_sec = float(c_off) / tl_fps
                dur_sec = float(c_dur) / tl_fps
                slice_wav = audio_dir / f"_temp_slice_{idx}.wav"
                slice_cmd = [
                    ffmpeg_bin, "-y",
                    "-ss", f"{start_sec:.4f}",
                    "-i", src_fp,
                    "-t", f"{dur_sec:.4f}",
                    "-vn", "-acodec", "pcm_s16le", "-ar", "22050", "-ac", "1",
                    str(slice_wav)
                ]
                subprocess.run(slice_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
                temp_slices.append(slice_wav)

                prev_end = c_end

            with open(concat_list, "w", encoding="utf-8") as f:
                for s in temp_slices:
                    f.write(f"file '{s.resolve().as_posix()}'\n")

            concat_cmd = [
                ffmpeg_bin, "-y", "-f", "concat", "-safe", "0",
                "-i", str(concat_list),
                "-c", "copy",
                str(baked_wav)
            ]
            subprocess.run(concat_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

        finally:
            for s in temp_slices:
                if s.exists():
                    try:
                        s.unlink()
                    except Exception:
                        pass
            if concat_list.exists():
                try:
                    concat_list.unlink()
                except Exception:
                    pass

    # Сохраняем актуальное состояние дорожки
    with open(state_file, "w", encoding="utf-8") as f:
        json.dump(track_state, f, indent=2, ensure_ascii=False)

    log_fn(f"[Запекание] Слепок готов: {baked_wav.name} ({track_state['total_duration_sec']:.1f} сек)")
    return str(baked_wav), track_state


def inspect_audio_track(proj, timeline_name="intro", track_index=2):
    """Быстрая инспекция дорожки аудио: возвращает детальную структуру и статус редактирования."""
    if not proj:
        return {"found": False, "message": "DaVinci не подключен"}

    tl = None
    for i in range(1, proj.GetTimelineCount() + 1):
        t = proj.GetTimelineByIndex(i)
        if t and t.GetName().lower() == timeline_name.lower():
            tl = t
            break

    if not tl:
        return {"found": False, "message": f"Таймлайн '{timeline_name}' не найден"}

    track_state = get_track_state(tl, track_index)
    if track_state["items_count"] == 0:
        return {"found": False, "message": f"Трек A{track_index} пуст"}

    clips = track_state["clips"]
    is_complex = track_state["is_complex"]
    tl_fps = track_state["timeline_fps"]
    dur_sec = track_state["total_duration_sec"]

    if not is_complex:
        fn = clips[0]["name"]
        fp = clips[0]["file_path"]
        status_label = fn
    else:
        fn = f"Составной трек ({len(clips)} сегм., монтаж)"
        fp = clips[0]["file_path"] if clips else ""
        status_label = f"Составной трек: {len(clips)} сегментов (монтаж/подрезка)"

    items = tl.GetItemListInTrack("audio", track_index) or []
    item = items[0] if items else None

    return {
        "found": True,
        "file_name": fn,
        "file_path": fp,
        "status_label": status_label,
        "duration_sec": dur_sec,
        "duration_frames": track_state["total_duration_frames"],
        "timeline_fps": tl_fps,
        "is_complex": is_complex,
        "clips_count": len(clips),
        "track_state": track_state,
        "item": item,
        "timeline": tl,
    }


# ─── Output Resolution ───────────────────────────────────────────────────────

def resolve_target_output(proj=None, custom_output=None) -> Path:
    """Определить путь сохранения music-beats.json."""
    if custom_output:
        out_p = Path(custom_output).resolve()
        out_p.parent.mkdir(parents=True, exist_ok=True)
        return out_p

    out_dir = SCRIPT_DIR / "output"
    if proj:
        proj_name = proj.GetName()
        safe_name = "".join(c for c in proj_name if c.isalnum() or c in (' ', '.', '_', '-')).rstrip()
        project_dir = out_dir / safe_name
        project_dir.mkdir(parents=True, exist_ok=True)
        return project_dir / "music-beats.json"

    out_dir.mkdir(parents=True, exist_ok=True)
    return out_dir / "music-beats.json"


# ─── Execution ───────────────────────────────────────────────────────────────

def run_analysis(params, log_fn=print, stop_event=None, progress_fn=None):
    def _notify_progress(pct, status, detail=""):
        if progress_fn:
            progress_fn(pct, status, detail)

    track_type = params.get("track_type", "audio")
    track_index = params.get("track_index", 2)
    timeline_name = params.get("timeline", "intro")
    item_index = params.get("item_index", 0)
    beats_per_bar = params.get("beats_per_bar")
    frequency = params.get("frequency", 0)
    adaptive = params.get("adaptive", False)
    freq_quiet = params.get("freq_quiet", -1)
    freq_loud = params.get("freq_loud", 0)
    rms_threshold = params.get("rms_threshold", 0.229)
    marker_color = params.get("marker_color", "Red")
    marker_target = params.get("marker_target", "clip")
    output_path = params.get("output_path")

    _notify_progress(10, "Подключение к DaVinci Resolve...", f"Таймлайн: '{timeline_name}'")
    log_fn("Подключение к DaVinci Resolve...")
    proj = connect()
    if not proj:
        return {"status": "error", "message": "Cannot connect to DaVinci Resolve"}

    if timeline_name:
        tl = set_current_timeline(proj, timeline_name)
    else:
        tl = proj.GetCurrentTimeline()

    if not tl:
        return {"status": "error", "message": f"Timeline '{timeline_name}' not found"}

    log_fn(f"Таймлайн: {tl.GetName()}")
    target_out = resolve_target_output(proj, output_path)
    session_dir = target_out.parent

    _notify_progress(25, "Инспекция и подготовка аудиодорожки...", f"Трек A{track_index} на таймлайне '{tl.GetName()}'")
    log_fn(f"Инспекция и запекание аудиодорожки A{track_index}...")
    baked_audio_path, track_state = bake_timeline_audio(tl, track_index, session_dir, log_fn=log_fn)
    if not baked_audio_path or not os.path.exists(baked_audio_path):
        return {"status": "error", "message": f"Не удалось сформировать слепок аудио с трека A{track_index}"}

    items = tl.GetItemListInTrack(track_type, track_index) or []
    timeline_item = items[0] if items else None

    if stop_event and stop_event.is_set():
        return {"status": "cancelled"}

    _notify_progress(55, "Анализ звука и детекция битов (Librosa)...", f"Длительность: {track_state['total_duration_sec']:.1f} сек")
    log_fn("Детекция битов по слепку аудио...")
    beat_data = detect_beats(baked_audio_path)

    _notify_progress(75, "Определение музыкального размера и долей...")
    if beats_per_bar is None:
        beats_per_bar, time_sig = detect_time_signature(beat_data)
        log_fn(f"Определён музыкальный размер: {time_sig}")
    else:
        time_sig = f"{beats_per_bar}/4" if beats_per_bar != 3 else "3/4"

    _notify_progress(85, "Расчет сетки маркеров...")
    if adaptive:
        strong_beats = filter_adaptive_beats(beat_data, beats_per_bar, freq_quiet, freq_loud, rms_threshold)
    else:
        strong_beats = filter_strong_beats(beat_data, beats_per_bar, frequency)

    if stop_event and stop_event.is_set():
        return {"status": "cancelled"}

    do_place_markers = params.get("place_markers", True)
    if marker_target == "clip" and len(items) > 1:
        log_fn(f"[Защита DaVinci] Нарезка из {len(items)} сегментов: маркеры безопасно перенаправлены на шкалу таймлайна.")
        marker_target = "timeline"

    clip_items = items if (marker_target == "clip" and len(items) == 1) else None
    placed = 0

    if do_place_markers:
        _notify_progress(92, f"Расстановка маркеров в DaVinci Resolve...", f"Цель: {marker_target}, цвет: {marker_color}")
        log_fn(f"Расстановка маркеров ({marker_target}) в DaVinci Resolve...")
        placed = place_markers(tl, strong_beats, color=marker_color, timeline_items=clip_items)
    else:
        log_fn("Маркеры на таймлайн не наносились (готовы к ручной разметке).")

    timeline_fps = float(tl.GetSetting("timelineFrameRate") or 23.976)
    beat_frames = [int(b["time"] * timeline_fps) for b in strong_beats]

    result = {
        "status": "success",
        "tempo": beat_data["tempo"],
        "audio_duration": beat_data["duration"],
        "timeline_fps": timeline_fps,
        "time_signature": time_sig,
        "beats_per_bar": beats_per_bar,
        "frequency": frequency,
        "total_beats": len(beat_data["beat_times"]),
        "markers_placed": placed,
        "strong_beat_frames": beat_frames,
        "_strong_beats_data": strong_beats,  # кэш для быстрой расстановки
        "_baked_audio_path": str(baked_audio_path),
    }

    save_json = params.get("save_json", True)
    if save_json:
        save_analysis_json(result, proj=proj, output_path=output_path, log_fn=log_fn)
    else:
        log_fn("Результат рассчитан (для сохранения нажмите кнопку 'Сохранить биты в JSON').")

    _notify_progress(100, f"Готово! Темп: {beat_data['tempo']:.1f} BPM", f"Рассчитано долей: {len(beat_frames)}")
    log_fn(f"Готово! Темп: {beat_data['tempo']:.1f} BPM, долей: {len(beat_frames)}, расставлено маркеров: {placed}")
    return result


def save_analysis_json(result, proj=None, output_path=None, log_fn=print):
    """Сохранить результат анализа в целевой JSON-файл."""
    if not result:
        return None
    to_save = {k: v for k, v in result.items() if not k.startswith('_')}
    final_out = resolve_target_output(proj, output_path)
    final_out.parent.mkdir(parents=True, exist_ok=True)
    with open(final_out, "w", encoding="utf-8") as f:
        json.dump(to_save, f, indent=2, ensure_ascii=False)
    log_fn(f"Файл битов сохранён: {final_out}")
    return final_out


def place_markers_for_result(proj, timeline_name="intro", track_index=2, strong_beats=None, color="Red", target="clip", log_fn=print, progress_fn=None):
    """Фаза 2: физическая расстановка маркеров по уже рассчитанным долям."""
    def _notify_progress(pct, status, detail=""):
        if progress_fn:
            progress_fn(pct, status, detail)

    _notify_progress(15, "Подключение к DaVinci Resolve...", f"Таймлайн: '{timeline_name}'")
    if not proj:
        return {"status": "error", "message": "DaVinci не подключен"}

    tl = set_current_timeline(proj, timeline_name) if timeline_name else proj.GetCurrentTimeline()
    if not tl:
        return {"status": "error", "message": f"Таймлайн '{timeline_name}' не найден"}

    items = tl.GetItemListInTrack("audio", track_index) or []
    if not items and target == "clip":
        return {"status": "error", "message": f"Нет клипов на треке A{track_index}"}

    # Защита от сбоя DaVinci Resolve при множественных фрагментах на клипе
    if target == "clip" and len(items) > 1:
        log_fn(f"[Защита DaVinci] Обнаружен монтаж аудио из {len(items)} сегментов.")
        log_fn("[Защита DaVinci] Режим 'clip' заблокирован во избежание сбоя Resolve. Маркеры безопасно наносятся на шкалу таймлайна.")
        target = "timeline"

    clip_items = items if (target == "clip" and len(items) == 1) else None

    _notify_progress(40, f"Очистка и расстановка маркеров ({color})...", f"Цель: {target}, долей: {len(strong_beats or [])}")
    if clip_items:
        log_fn(f"Расстановка маркеров цвета '{color}' на клип трека A{track_index}...")
    else:
        log_fn(f"Расстановка маркеров цвета '{color}' на шкалу таймлайна '{tl.GetName()}'...")

    placed = place_markers(tl, strong_beats or [], color=color, timeline_items=clip_items)
    _notify_progress(100, f"Готово! Размечено маркеров: {placed}", f"Цвет: {color}, таймлайн: '{tl.GetName()}'")
    log_fn(f"Успешно расставлено маркеров: {placed}")
    return {"status": "success", "markers_placed": placed, "target": target}


def main():
    parser = argparse.ArgumentParser(description="Автоматический анализ музыки и расстановка маркеров битов")
    parser.add_argument("--timeline", default="intro", help="Имя таймлайна (default: intro)")
    parser.add_argument("--track-type", default="audio", choices=["audio", "video"])
    parser.add_argument("--track-index", type=int, default=2, help="Индекс аудиотрека (default: 2 / A2)")
    parser.add_argument("--item-index", type=int, default=0)
    parser.add_argument("--beats-per-bar", type=int, default=None)
    parser.add_argument("--frequency", type=int, default=0, help="Частота маркеров (default: 0 = каждый такт)")
    parser.add_argument("--adaptive", action="store_true", default=False, help="Адаптивный режим (default: False)")
    parser.add_argument("--freq-quiet", type=int, default=-1)
    parser.add_argument("--freq-loud", type=int, default=0)
    parser.add_argument("--rms-threshold", type=float, default=0.229)
    parser.add_argument("--marker-color", default="Red")
    parser.add_argument("--marker-target", default="clip", choices=["clip", "timeline"])
    parser.add_argument("--output", type=str, default=None, help="Путь для сохранения music-beats.json")
    args = parser.parse_args()

    res = run_analysis({
        "timeline": args.timeline,
        "track_type": args.track_type,
        "track_index": args.track_index,
        "item_index": args.item_index,
        "beats_per_bar": args.beats_per_bar,
        "frequency": args.frequency,
        "adaptive": args.adaptive,
        "freq_quiet": args.freq_quiet,
        "freq_loud": args.freq_loud,
        "rms_threshold": args.rms_threshold,
        "marker_color": args.marker_color,
        "marker_target": args.marker_target,
        "output_path": args.output,
    })

    if res.get("status") == "error":
        print(f"ERROR: {res['message']}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
