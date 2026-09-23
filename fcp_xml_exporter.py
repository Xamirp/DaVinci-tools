#!/usr/bin/env python3
"""fcp_xml_exporter.py — Генератор файлов последовательностей в формате Final Cut Pro 7 XML (xmeml).

Совместим с DaVinci Resolve, Adobe Premiere Pro, Final Cut Pro 7 и другими NLE.
Позволяет экспортировать аудиодорожку с маркерами долей/битов на клипе или таймлайне.
"""

import os
import xml.etree.ElementTree as ET
from xml.dom import minidom
from pathlib import Path
from typing import List, Dict, Any, Optional


def get_fcp_rate(fps: float):
    """Определить timebase и флаг NTSC по частоте кадров."""
    fps_val = float(fps)
    if abs(fps_val - 23.976) < 0.05 or abs(fps_val - 23.98) < 0.05:
        return 24, "TRUE"
    elif abs(fps_val - 29.97) < 0.05:
        return 30, "TRUE"
    elif abs(fps_val - 59.94) < 0.05:
        return 60, "TRUE"
    else:
        return max(1, int(round(fps_val))), "FALSE"


def format_path_url(file_path: str) -> str:
    """Сформировать pathurl в формате FCP7 XML (file://localhost/...)."""
    p = Path(file_path).resolve()
    posix_path = p.as_posix()
    if not posix_path.startswith('/'):
        posix_path = '/' + posix_path
    return f"file://localhost{posix_path}"


def create_marker_element(
    name: str,
    comment: str,
    in_frame: int,
    out_frame: int = -1,
    color: str = "red"
) -> ET.Element:
    """Создать XML-элемент маркера FCP7."""
    marker = ET.Element("marker")
    
    el_name = ET.SubElement(marker, "name")
    el_name.text = str(name)
    
    el_comment = ET.SubElement(marker, "comment")
    el_comment.text = str(comment) if comment else ""
    
    el_in = ET.SubElement(marker, "in")
    el_in.text = str(int(in_frame))
    
    el_out = ET.SubElement(marker, "out")
    el_out.text = str(int(out_frame))
    
    el_color = ET.SubElement(marker, "markercolor")
    el_color.text = str(color).lower()
    
    return marker


def export_to_fcp7_xml(
    output_xml_path: str,
    audio_file_path: str,
    strong_beats: List[Dict[str, Any]],
    sequence_name: str = "BitMaker_Sequence",
    timeline_fps: float = 23.976,
    sample_rate: int = 48000,
    marker_target: str = "clip",  # "clip", "timeline", "both"
    default_color: str = "Red",
    log_fn=print
) -> str:
    """Сгенерировать и сохранить XML-файл в формате FCP7.
    
    Args:
        output_xml_path: Путь к целевому XML-файлу.
        audio_file_path: Путь к аудиофайлу (.wav/.mp3).
        strong_beats: Список словарей маркеров с ключами 'time', 'name', 'dynamics', 'color' и т.д.
        sequence_name: Название создаваемой секвенции.
        timeline_fps: Частота кадров таймлайна.
        sample_rate: Частота дискретизации аудио.
        marker_target: Где ставить маркеры ('clip', 'timeline', 'both').
        default_color: Цвет маркеров по умолчанию.
        log_fn: Функция логирования.
        
    Returns:
        Абсолютный путь к созданному XML-файлу.
    """
    timebase, ntsc = get_fcp_rate(timeline_fps)
    audio_path_obj = Path(audio_file_path).resolve()
    audio_file_name = audio_path_obj.name
    path_url = format_path_url(str(audio_path_obj))
    
    # Расчет общей длительности в кадрах
    max_beat_time = max((b.get("time", 0.0) for b in strong_beats), default=0.0)
    # Если возможно, проверяем длительность файла
    duration_frames = max(100, int(round(max_beat_time * timeline_fps)) + int(timeline_fps * 4))

    # Корневой элемент <xmeml version="5">
    root = ET.Element("xmeml", version="5")
    
    sequence = ET.SubElement(root, "sequence", id="sequence-1")
    
    el_seq_name = ET.SubElement(sequence, "name")
    el_seq_name.text = str(sequence_name)
    
    el_seq_dur = ET.SubElement(sequence, "duration")
    el_seq_dur.text = str(duration_frames)
    
    seq_rate = ET.SubElement(sequence, "rate")
    ET.SubElement(seq_rate, "timebase").text = str(timebase)
    ET.SubElement(seq_rate, "ntsc").text = str(ntsc)
    
    timecode = ET.SubElement(sequence, "timecode")
    tc_rate = ET.SubElement(timecode, "rate")
    ET.SubElement(tc_rate, "timebase").text = str(timebase)
    ET.SubElement(tc_rate, "ntsc").text = str(ntsc)
    ET.SubElement(timecode, "string").text = "00:00:00:00"
    ET.SubElement(timecode, "frame").text = "0"
    ET.SubElement(timecode, "displayformat").text = "NDF"

    # Маркеры на уровне секвенции (Timeline markers)
    if marker_target in ("timeline", "both"):
        for idx, b in enumerate(strong_beats):
            t = float(b.get("time", 0.0))
            frame_num = int(round(t * timeline_fps))
            m_name = b.get("name", f"Beat {idx + 1}")
            m_comment = b.get("dynamics", "")
            m_color = b.get("color", default_color)
            m_elem = create_marker_element(m_name, m_comment, frame_num, -1, m_color)
            sequence.append(m_elem)

    # <media> блок
    media = ET.SubElement(sequence, "media")
    
    # Видеоформат по умолчанию (Full HD)
    video = ET.SubElement(media, "video")
    v_format = ET.SubElement(video, "format")
    v_sample = ET.SubElement(v_format, "samplecharacteristics")
    v_rate = ET.SubElement(v_sample, "rate")
    ET.SubElement(v_rate, "timebase").text = str(timebase)
    ET.SubElement(v_rate, "ntsc").text = str(ntsc)
    ET.SubElement(v_sample, "width").text = "1920"
    ET.SubElement(v_sample, "height").text = "1080"
    ET.SubElement(v_sample, "pixelaspectratio").text = "square"

    # <audio> блок
    audio = ET.SubElement(media, "audio")
    ET.SubElement(audio, "numOutputChannels").text = "2"
    a_format = ET.SubElement(audio, "format")
    a_sample = ET.SubElement(a_format, "samplecharacteristics")
    ET.SubElement(a_sample, "depth").text = "16"
    ET.SubElement(a_sample, "samplerate").text = str(sample_rate)

    # Аудиотрек A1
    track = ET.SubElement(audio, "track")
    
    # Клип на аудиотреке
    clipitem = ET.SubElement(track, "clipitem", id="clipitem-1")
    ET.SubElement(clipitem, "masterclipid").text = "masterclip-1"
    ET.SubElement(clipitem, "name").text = audio_file_name
    ET.SubElement(clipitem, "enabled").text = "TRUE"
    ET.SubElement(clipitem, "duration").text = str(duration_frames)
    
    c_rate = ET.SubElement(clipitem, "rate")
    ET.SubElement(c_rate, "timebase").text = str(timebase)
    ET.SubElement(c_rate, "ntsc").text = str(ntsc)
    
    ET.SubElement(clipitem, "start").text = "0"
    ET.SubElement(clipitem, "end").text = str(duration_frames)
    ET.SubElement(clipitem, "in").text = "0"
    ET.SubElement(clipitem, "out").text = str(duration_frames)

    # Информация о файле
    file_elem = ET.SubElement(clipitem, "file", id="file-1")
    ET.SubElement(file_elem, "name").text = audio_file_name
    ET.SubElement(file_elem, "pathurl").text = path_url
    
    f_rate = ET.SubElement(file_elem, "rate")
    ET.SubElement(f_rate, "timebase").text = str(timebase)
    ET.SubElement(f_rate, "ntsc").text = str(ntsc)
    
    ET.SubElement(file_elem, "duration").text = str(duration_frames)
    
    f_media = ET.SubElement(file_elem, "media")
    f_audio = ET.SubElement(f_media, "audio")
    f_sample = ET.SubElement(f_audio, "samplecharacteristics")
    ET.SubElement(f_sample, "depth").text = "16"
    ET.SubElement(f_sample, "samplerate").text = str(sample_rate)
    ET.SubElement(f_audio, "channelcount").text = "1"

    sourcetrack = ET.SubElement(clipitem, "sourcetrack")
    ET.SubElement(sourcetrack, "mediatype").text = "audio"
    ET.SubElement(sourcetrack, "trackindex").text = "1"

    # Маркеры на уровне клипа (Clip markers)
    if marker_target in ("clip", "both"):
        for idx, b in enumerate(strong_beats):
            t = float(b.get("time", 0.0))
            frame_num = int(round(t * timeline_fps))
            m_name = b.get("name", f"Beat {idx + 1}")
            m_comment = b.get("dynamics", "")
            m_color = b.get("color", default_color)
            m_elem = create_marker_element(m_name, m_comment, frame_num, -1, m_color)
            clipitem.append(m_elem)

    # Красивое форматирование с отступами
    xml_str = ET.tostring(root, encoding="utf-8")
    parsed_dom = minidom.parseString(xml_str)
    pretty_xml = parsed_dom.toprettyxml(indent="  ", encoding="utf-8")
    
    # Вставка <!DOCTYPE xmeml> после <?xml ... ?>
    lines = pretty_xml.decode("utf-8").splitlines()
    if len(lines) > 0 and lines[0].startswith("<?xml"):
        lines.insert(1, "<!DOCTYPE xmeml>")
    else:
        lines.insert(0, "<!DOCTYPE xmeml>")
    final_output = "\n".join(lines)

    out_file = Path(output_xml_path).resolve()
    out_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(out_file, "w", encoding="utf-8") as f:
        f.write(final_output)

    if log_fn:
        try:
            log_fn(f"FCP7 XML успешно сохранен: {out_file}")
        except Exception:
            try:
                log_fn(f"FCP7 XML successfully saved: {out_file}")
            except Exception:
                pass

    return str(out_file)

