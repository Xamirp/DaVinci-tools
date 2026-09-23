#!/usr/bin/env python3
"""edl_exporter.py — Генератор файлов маркеров в формате CMX 3600 EDL для DaVinci Resolve.

Позволяет экспортировать маркеры долей/битов в файл .edl, который легко импортируется
в DaVinci Resolve (Timeline -> Import -> Timeline Markers from EDL...).
"""

import os
from pathlib import Path
from typing import List, Dict, Any


def seconds_to_timecode(seconds: float, fps: float) -> str:
    """Преобразовать секунды в таймкод формата HH:MM:SS:FF."""
    fps_val = float(fps)
    # Округляем до ближайшего целого кадра
    total_frames = int(round(seconds * fps_val))
    
    fps_int = int(round(fps_val))
    if fps_int <= 0:
        fps_int = 24

    frames = total_frames % fps_int
    total_seconds = total_frames // fps_int
    secs = total_seconds % 60
    total_minutes = total_seconds // 60
    mins = total_minutes % 60
    hours = total_minutes // 60

    return f"{hours:02d}:{mins:02d}:{secs:02d}:{frames:02d}"


def export_to_edl(
    output_edl_path: str,
    strong_beats: List[Dict[str, Any]],
    title: str = "Music_Beats",
    timeline_fps: float = 23.976,
    default_color: str = "Red",
    log_fn=None
) -> str:
    """Сгенерировать и сохранить маркеры в формате CMX 3600 EDL для DaVinci Resolve.
    
    Args:
        output_edl_path: Путь к целевому файлу .edl.
        strong_beats: Список словарей с ключами 'time', 'name', 'dynamics', 'color' и т.д.
        title: Название проекта / таймлайна в заголовке EDL.
        timeline_fps: Частота кадров таймлайна.
        default_color: Цвет маркера по умолчанию.
        log_fn: Функция для вывода логов.
        
    Returns:
        Абсолютный путь к созданному файлу EDL.
    """
    fps_val = float(timeline_fps)
    fcm_mode = "DROP FRAME" if (abs(fps_val - 29.97) < 0.05 or abs(fps_val - 59.94) < 0.05) else "NON-DROP FRAME"

    # Очистка заголовка от спецсимволов для формата CMX 3600
    safe_title = "".join(c if c.isalnum() or c in " _-" else "_" for c in title)[:32].upper()
    if not safe_title:
        safe_title = "MUSIC_BEATS"

    lines = [
        f"TITLE: {safe_title}",
        f"FCM: {fcm_mode}",
        ""
    ]

    for idx, beat in enumerate(strong_beats, start=1):
        t = float(beat.get("time", 0.0))
        tc = seconds_to_timecode(t, fps_val)
        
        # Следующий кадр для конца интервала события в EDL
        next_t = t + (1.0 / fps_val)
        next_tc = seconds_to_timecode(next_t, fps_val)

        # Параметры маркера
        name = beat.get("name", f"Beat {idx}")
        dynamics = beat.get("dynamics", "")
        color = str(beat.get("color", default_color)).upper()

        comment_parts = [name]
        if dynamics:
            comment_parts.append(f"({dynamics})")
        comment_text = " ".join(comment_parts)

        # Стандартная CMX 3600 запись события + строка локатора DaVinci Resolve
        event_num = f"{idx:03d}"
        lines.append(f"{event_num}  AX       V     C        {tc} {next_tc} {tc} {next_tc}")
        lines.append(f"* FROM CLIP NAME: {name}")
        lines.append(f"* LOC: {tc} {color} {comment_text}")
        lines.append("")

    content = "\n".join(lines)
    out_file = Path(output_edl_path).resolve()
    out_file.parent.mkdir(parents=True, exist_ok=True)

    with open(out_file, "w", encoding="utf-8") as f:
        f.write(content)

    if log_fn:
        try:
            log_fn(f"EDL маркеры успешно сохранены: {out_file}")
        except Exception:
            pass

    return str(out_file)
