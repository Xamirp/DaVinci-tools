#!/usr/bin/env python3
"""
i18n.py — Система интернационализации и локализации (English, Українська, Русский).
"""

LANGUAGES = {
    "en": "English",
    "uk": "Українська",
    "ru": "Русский"
}

_CURRENT_LANGUAGE = "en"
_LISTENERS = []

TRANSLATIONS = {
    "en": {
        # App & Window
        "app_title": "BitMaker — AI Musical Beat & Rhythm Analysis for DaVinci Resolve",
        "menu_file": "File",
        "menu_export_edl": "Export EDL Markers...",
        "menu_export_xml": "Export FCPXML Markers (Premiere)...",
        "menu_export_csv": "Export CSV Beats...",
        "menu_export_json": "Export JSON Beats...",
        "menu_exit": "Exit",
        "menu_tools": "Tools",
        "menu_batch_analysis": "Batch Music Analysis...",
        "menu_short_video": "Short-Video Generator (TikTok/Reels/Shorts)...",
        "menu_waveform_viewer": "Interactive Waveform & Frequency Spectrogram...",
        "menu_view": "View",
        "menu_show_log": "Console & Process Log",
        "menu_shortcuts": "Keyboard Shortcuts Reference",
        "menu_help": "Help",
        "menu_about": "About BitMaker",
        "menu_about_ai": "Created with Google AI Studio",
        "menu_language": "Language",

        # Header Panel
        "header_title": "BitMaker",
        "header_subtitle": "AI Rhythm & Beat Marker Tool for Video Editors",
        "status_connected": "Connected to DaVinci Resolve Studio",
        "status_disconnected": "DaVinci Resolve not running",
        "project_prefix": "Project:",
        "no_project": "No active project",
        "audio_not_found": "Audio file not found",
        "audio_none": "—",

        # Settings Panel
        "settings_title": "Detection & Marker Parameters",
        "label_timeline": "Timeline:",
        "label_track": "Audio Track:",
        "label_track_default": "(default A2)",
        "label_density": "Cut Density:",
        "label_color": "Color:",
        "label_target": "Target:",
        "target_clip": "clip",
        "target_timeline": "timeline",
        "target_locked_hint": "🔒 Timeline only (audio montage)",
        "adaptive_mode": "Adaptive Mode",
        "status_on": "[ ON ]",
        "status_off": "[ OFF ]",
        "btn_configure": "Configure...",
        "pace_info_fmt": "⏱️ Cut duration: ~{clip_dur:.2f}s ({frames} frames)  |  📊 Expected cuts: ~{expected_clips} clips (at {bpm:.1f} BPM)",

        # Density presets
        "density_preset_m2": "Every 4 bars (Slow / Landscapes / Drone)",
        "density_preset_m1": "Every 2 bars (Moderate / Cinematic)",
        "density_preset_0": "Every 1 bar (Default / Standard Montage)",
        "density_preset_1": "Every 1/2 bar (Dynamic / Rhythm Drive)",
        "density_preset_2": "Every beat / hit (Action / Maximum Rush)",

        # Results Panel
        "results_title": "Audio Analysis & Track Metrics",
        "stat_bpm": "BPM (Tempo)",
        "stat_beats": "Beats Detected",
        "stat_segments": "Musical Sections",
        "stat_placed": "Markers Placed",
        "stat_not_analyzed": "Not analyzed",
        "stat_measuring": "Measuring...",
        "stat_analyzing": "Analyzing...",
        "stat_none": "—",
        "stat_na": "N/A",

        # Actions Panel
        "btn_analyze": "⚡ 1. Analyze Audio Track",
        "btn_place_markers": "🎯 2. Place Markers in DaVinci",
        "btn_clear_markers": "🗑 Clear Markers",
        "status_ready": "Ready",
        "shortcuts_hint": "Hotkeys: Space - Play/Pause | F5 - Refresh | Del - Remove | Ctrl+Z - Undo | Ctrl+Y - Redo",

        # Timeline Panel
        "timeline_title": "Interactive Timeline & Beat Waveform",
        "btn_play": "▶ Play",
        "btn_pause": "⏸ Pause",
        "btn_stop": "⏹ Stop",
        "label_zoom": "Zoom:",
        "time_fmt": "Time: {current:.2f}s / {total:.2f}s",
        "no_data_hint": "Run audio analysis (⚡ Step 1) or click Refresh (F5) to display timeline",
        "ctx_edit_marker": "Edit Marker...",
        "ctx_delete_marker": "Delete Marker (Del)",
        "ctx_add_marker": "Add Marker Here",

        # Commands & Logs
        "cmd_place_markers": "Place markers ({color}, {target})",
        "cmd_clear_markers": "Clear markers ({target})",
        "cmd_move_marker": "Move marker #{id} ({old_t:.2f}s -> {new_t:.2f}s)",
        "cmd_delete_marker": "Delete marker #{id} ({time:.2f}s)",
        "cmd_add_marker": "Add marker ({time:.2f}s)",
        "log_phase1_start": "PHASE 1: Extracting audio and running AI beat detection...",
        "log_phase2_start": "PHASE 2: Placing markers ({color}) on {target}...",
        "log_undo": "[Undo] Action reverted: {desc}",
        "log_redo": "[Redo] Action restored: {desc}",
        "log_markers_cleared": "[Clear] Deleted {count} markers on {target} ({color}).",
        "log_markers_remaining": "[Info] Markers remaining on timeline ruler: {count} ({colors})",
        "log_success_markers": "[SUCCESS] Markers successfully placed in DaVinci Resolve!",
        "log_success_analyzed": "[SUCCESS] Audio analyzed: {bpm:.1f} BPM, {count} beats found.",
        "target_desc_clip": "track A{track} clips",
        "target_desc_timeline": "timeline ruler",

        # Dialogs
        "dlg_progress_title": "Processing",
        "dlg_cancel": "Cancel",
        "dlg_close": "Close",
        "dlg_save": "Save",
        "dlg_reset": "Reset",
        "dlg_apply": "Apply",
        "dlg_export_success": "Export Successful",
        "dlg_error": "Error",
        "dlg_warning": "Warning",
        "dlg_davinci_not_running": "DaVinci Resolve is not running or no active project found.",
        "dlg_no_analysis_data": "Please run audio track analysis (Step 1) first.",
        "dlg_shortcuts_title": "Keyboard Shortcuts Reference",
        "dlg_about_title": "About BitMaker",
        "dlg_about_text": "BitMaker v2.3.0\nProfessional AI Beat & Rhythm Analysis Tool for DaVinci Resolve Studio.\n\nDeveloped with Google AI Studio & Gemini 2.5 Pro.",
        "dlg_adaptive_title": "Adaptive Rhythm Detection Settings",
        "dlg_waveform_title": "Interactive Waveform & Spectrogram Viewer",
        "dlg_log_title": "Execution Console & Logs",
        "dlg_batch_title": "Batch Audio Files Analysis",
        "dlg_short_video_title": "Short-Video Video Generator",

        # Export
        "export_edl_filter": "EDL files (*.edl)",
        "export_xml_filter": "FCPXML files (*.xml)",
        "export_csv_filter": "CSV files (*.csv)",
        "export_json_filter": "JSON files (*.json)",
        "all_files_filter": "All files (*.*)"
    },

    "uk": {
        # App & Window
        "app_title": "BitMaker — AI аналіз музичних бітів та ритму для DaVinci Resolve",
        "menu_file": "Файл",
        "menu_export_edl": "Експорт маркерів в EDL...",
        "menu_export_xml": "Експорт маркерів в FCPXML (Premiere)...",
        "menu_export_csv": "Експорт бітів у CSV...",
        "menu_export_json": "Експорт бітів у JSON...",
        "menu_exit": "Вихід",
        "menu_tools": "Інструменти",
        "menu_batch_analysis": "Пакетний аналіз треків...",
        "menu_short_video": "Генератор коротких відео (TikTok/Reels/Shorts)...",
        "menu_waveform_viewer": "Інтерактивна форма хвилі та спектрограма...",
        "menu_view": "Вигляд",
        "menu_show_log": "Консоль та лог процесів",
        "menu_shortcuts": "Довідка гарячих клавіш",
        "menu_help": "Довідка",
        "menu_about": "Про програму BitMaker",
        "menu_about_ai": "Створено за допомогою Google AI Studio",
        "menu_language": "Мова (Language)",

        # Header Panel
        "header_title": "BitMaker",
        "header_subtitle": "AI-інструмент розмітки бітів та ритму для відеомонтажерів",
        "status_connected": "Підключено до DaVinci Resolve Studio",
        "status_disconnected": "DaVinci Resolve не запущено",
        "project_prefix": "Проєкт:",
        "no_project": "Немає підключення",
        "audio_not_found": "Аудіофайл не знайдено",
        "audio_none": "—",

        # Settings Panel
        "settings_title": "Параметри детекції та розмітки",
        "label_timeline": "Таймлайн:",
        "label_track": "Аудіотрек:",
        "label_track_default": "(за замовч. A2)",
        "label_density": "Щільність склейок:",
        "label_color": "Колір:",
        "label_target": "Таргет:",
        "target_clip": "clip",
        "target_timeline": "timeline",
        "target_locked_hint": "🔒 Тільки Timeline (монтаж аудіо)",
        "adaptive_mode": "Адаптивний режим",
        "status_on": "[ УВІМК ]",
        "status_off": "[ ВИМК ]",
        "btn_configure": "Налаштувати...",
        "pace_info_fmt": "⏱️ Довжина кліпу: ~{clip_dur:.2f}с ({frames} кадрів)  |  📊 Очікувано: ~{expected_clips} склейок (при {bpm:.1f} BPM)",

        # Density presets
        "density_preset_m2": "Кожні 4 такти (Рідкісний / Панорами)",
        "density_preset_m1": "Кожні 2 такти (Помірний)",
        "density_preset_0": "Кожен такт (За замовчуванням / Стандарт)",
        "density_preset_1": "Кожні 1/2 такту (Динамічний / Драйв)",
        "density_preset_2": "Кожен біт / удар (Екшен / Максимум)",

        # Results Panel
        "results_title": "Аналіз аудіо та метрики треку",
        "stat_bpm": "BPM (Темп)",
        "stat_beats": "Знайдено часток",
        "stat_segments": "Музичні секції",
        "stat_placed": "Розміщено маркерів",
        "stat_not_analyzed": "Не проаналізовано",
        "stat_measuring": "Вимірювання...",
        "stat_analyzing": "Аналіз...",
        "stat_none": "—",
        "stat_na": "Н/Д",

        # Actions Panel
        "btn_analyze": "⚡ 1. Аналізувати аудіотрек",
        "btn_place_markers": "🎯 2. Розставити маркери в DaVinci",
        "btn_clear_markers": "🗑 Очистити маркери",
        "status_ready": "Готово",
        "shortcuts_hint": "Гарячі клавіші: Space - Плей/Пауза | F5 - Оновити | Del - Видалити | Ctrl+Z - Undo | Ctrl+Y - Redo",

        # Timeline Panel
        "timeline_title": "Інтерактивний таймлайн та хвильова форма",
        "btn_play": "▶ Відтворити",
        "btn_pause": "⏸ Пауза",
        "btn_stop": "⏹ Стоп",
        "label_zoom": "Масштаб:",
        "time_fmt": "Час: {current:.2f}с / {total:.2f}с",
        "no_data_hint": "Запустіть аналіз треку (⚡ Крок 1) або натисніть Оновити (F5) для відображення",
        "ctx_edit_marker": "Редагувати маркер...",
        "ctx_delete_marker": "Видалити маркер (Del)",
        "ctx_add_marker": "Додати маркер тут",

        # Commands & Logs
        "cmd_place_markers": "Розмітка маркерів ({color}, {target})",
        "cmd_clear_markers": "Очищення маркерів ({target})",
        "cmd_move_marker": "Переміщення маркера #{id} ({old_t:.2f}с -> {new_t:.2f}с)",
        "cmd_delete_marker": "Видалення маркера #{id} ({time:.2f}с)",
        "cmd_add_marker": "Додавання маркера ({time:.2f}с)",
        "log_phase1_start": "ФАЗА 1: Вилучення аудіо та нейросітковий аналіз ритму...",
        "log_phase2_start": "ФАЗА 2: Нанесення маркерів ({color}) на {target}...",
        "log_undo": "[Undo] Скасування дії: {desc}",
        "log_redo": "[Redo] Повернення дії: {desc}",
        "log_markers_cleared": "[Очищення] Видалено {count} маркерів на {target} ({color}).",
        "log_markers_remaining": "[Інфо] На шкалі таймлайну залишилось маркерів: {count} ({colors})",
        "log_success_markers": "[УСПІХ] Маркери успішно розміщені в DaVinci Resolve!",
        "log_success_analyzed": "[УСПІХ] Трек проаналізовано: {bpm:.1f} BPM, знайдено {count} часток.",
        "target_desc_clip": "кліпах треку A{track}",
        "target_desc_timeline": "шкалі таймлайну",

        # Dialogs
        "dlg_progress_title": "Обробка",
        "dlg_cancel": "Скасувати",
        "dlg_close": "Закрити",
        "dlg_save": "Зберегти",
        "dlg_reset": "Скинути",
        "dlg_apply": "Застосувати",
        "dlg_export_success": "Експорт успішно завершено",
        "dlg_error": "Помилка",
        "dlg_warning": "Увага",
        "dlg_davinci_not_running": "DaVinci Resolve не запущено або немає відкритого проєкту.",
        "dlg_no_analysis_data": "Спочатку виконайте аналіз аудіотреку (Крок 1).",
        "dlg_shortcuts_title": "Довідка гарячих клавіш",
        "dlg_about_title": "Про BitMaker",
        "dlg_about_text": "BitMaker v2.3.0\nПрофесійний AI-інструмент детекції бітів та ритму для DaVinci Resolve Studio.\n\nСтворено за допомогою Google AI Studio та Gemini 2.5 Pro.",
        "dlg_adaptive_title": "Налаштування адаптивного режиму",
        "dlg_waveform_title": "Інтерактивний перегляд хвильової форми та спектрограми",
        "dlg_log_title": "Консоль виконання та логи",
        "dlg_batch_title": "Пакетний аналіз аудіофайлів",
        "dlg_short_video_title": "Генератор коротких відео",

        # Export
        "export_edl_filter": "EDL файли (*.edl)",
        "export_xml_filter": "FCPXML файли (*.xml)",
        "export_csv_filter": "CSV файли (*.csv)",
        "export_json_filter": "JSON файли (*.json)",
        "all_files_filter": "Всі файли (*.*)"
    },

    "ru": {
        # App & Window
        "app_title": "BitMaker — AI музыкальный анализ ритма для DaVinci Resolve",
        "menu_file": "Файл",
        "menu_export_edl": "Экспорт маркеров в EDL...",
        "menu_export_xml": "Экспорт маркеров в FCPXML (Premiere)...",
        "menu_export_csv": "Экспорт битов в CSV...",
        "menu_export_json": "Экспорт битов в JSON...",
        "menu_exit": "Выход",
        "menu_tools": "Инструменты",
        "menu_batch_analysis": "Пакетный анализ треков...",
        "menu_short_video": "Генератор коротких видео (TikTok/Reels/Shorts)...",
        "menu_waveform_viewer": "Интерактивная волна и спектрограмма...",
        "menu_view": "Вид",
        "menu_show_log": "Консоль и лог процессов",
        "menu_shortcuts": "Справка горячих клавиш",
        "menu_help": "Справка",
        "menu_about": "О программе BitMaker",
        "menu_about_ai": "Создано с помощью Google AI Studio",
        "menu_language": "Язык (Language)",

        # Header Panel
        "header_title": "BitMaker",
        "header_subtitle": "AI-инструмент разметки битов и ритма для видеомонтажеров",
        "status_connected": "Подключено к DaVinci Resolve Studio",
        "status_disconnected": "DaVinci Resolve не запущен",
        "project_prefix": "Проект:",
        "no_project": "нет подключения",
        "audio_not_found": "Файл не найден",
        "audio_none": "—",

        # Settings Panel
        "settings_title": "Параметры детекции и разметки",
        "label_timeline": "Таймлайн:",
        "label_track": "Аудиотрек:",
        "label_track_default": "(по умолч. A2)",
        "label_density": "Плотность склеек:",
        "label_color": "Цвет:",
        "label_target": "Таргет:",
        "target_clip": "clip",
        "target_timeline": "timeline",
        "target_locked_hint": "🔒 Только Timeline (монтаж аудио)",
        "adaptive_mode": "Адаптивный режим",
        "status_on": "[ ВКЛ ]",
        "status_off": "[ ВЫКЛ ]",
        "btn_configure": "Настроить...",
        "pace_info_fmt": "⏱️ Длина клипа: ~{clip_dur:.2f}с ({frames} кадров)  |  📊 Ожидаемо склеек: ~{expected_clips} клипов (при {bpm:.1f} BPM)",

        # Density presets
        "density_preset_m2": "Каждые 4 такта (Редкий / Панорамы)",
        "density_preset_m1": "Каждые 2 такта (Умеренный)",
        "density_preset_0": "Каждый такт (По умолчанию / Стандарт)",
        "density_preset_1": "Каждые 1/2 такта (Динамичный / Драйв)",
        "density_preset_2": "Каждый бит / удар (Экшен / Максимум)",

        # Results Panel
        "results_title": "Анализ аудио и метрики трека",
        "stat_bpm": "BPM (Темп)",
        "stat_beats": "Найдено долей",
        "stat_segments": "Музыкальные секции",
        "stat_placed": "Размечено маркеров",
        "stat_not_analyzed": "Не анализировалось",
        "stat_measuring": "Измерение...",
        "stat_analyzing": "Анализ...",
        "stat_none": "—",
        "stat_na": "Н/Д",

        # Actions Panel
        "btn_analyze": "⚡ 1. Анализировать аудиотрек",
        "btn_place_markers": "🎯 2. Разметить маркеры в DaVinci",
        "btn_clear_markers": "🗑 Очистить маркеры",
        "status_ready": "Готово",
        "shortcuts_hint": "Горячие клавиши: Space - Плей/Пауза | F5 - Обновить | Del - Удалить | Ctrl+Z - Undo | Ctrl+Y - Redo",

        # Timeline Panel
        "timeline_title": "Интерактивный таймлайн и форма волны",
        "btn_play": "▶ Воспроизвести",
        "btn_pause": "⏸ Пауза",
        "btn_stop": "⏹ Стоп",
        "label_zoom": "Масштаб:",
        "time_fmt": "Время: {current:.2f}с / {total:.2f}с",
        "no_data_hint": "Запустите анализ трека (⚡ Шаг 1) или нажмите Обновить (F5) для отображения",
        "ctx_edit_marker": "Редактировать маркер...",
        "ctx_delete_marker": "Удалить маркер (Del)",
        "ctx_add_marker": "Добавить маркер здесь",

        # Commands & Logs
        "cmd_place_markers": "Разметка маркеров ({color}, {target})",
        "cmd_clear_markers": "Очистка маркеров ({target})",
        "cmd_move_marker": "Перемещение маркера #{id} ({old_t:.2f}с -> {new_t:.2f}с)",
        "cmd_delete_marker": "Удаление маркера #{id} ({time:.2f}с)",
        "cmd_add_marker": "Добавление маркера ({time:.2f}с)",
        "log_phase1_start": "ФАЗА 1: Извлечение аудио и нейросетевой анализ ритма...",
        "log_phase2_start": "ФАЗА 2: Нанесение маркеров ({color}) на {target}...",
        "log_undo": "[Undo] Отмена действия: {desc}",
        "log_redo": "[Redo] Возврат действия: {desc}",
        "log_markers_cleared": "[Очистка] Удалено {count} маркеров на {target} ({color}).",
        "log_markers_remaining": "[Инфо] На шкале таймлайна осталось маркеров: {count} ({colors})",
        "log_success_markers": "[УСПЕХ] Маркеры успешно размещены в DaVinci Resolve!",
        "log_success_analyzed": "[УСПЕХ] Трек проанализирован: {bpm:.1f} BPM, найдено {count} долей.",
        "target_desc_clip": "клипах трека A{track}",
        "target_desc_timeline": "шкале таймлайна",

        # Dialogs
        "dlg_progress_title": "Обработка",
        "dlg_cancel": "Отмена",
        "dlg_close": "Закрыть",
        "dlg_save": "Сохранить",
        "dlg_reset": "Сбросить",
        "dlg_apply": "Применить",
        "dlg_export_success": "Экспорт успешно выполнен",
        "dlg_error": "Ошибка",
        "dlg_warning": "Предупреждение",
        "dlg_davinci_not_running": "DaVinci Resolve не запущен или нет активного проекта.",
        "dlg_no_analysis_data": "Сначала выполните анализ аудиотрека (Шаг 1).",
        "dlg_shortcuts_title": "Справка по горячим клавишам",
        "dlg_about_title": "О программе BitMaker",
        "dlg_about_text": "BitMaker v2.3.0\nПрофессиональный AI-инструмент детекции битов и ритма для DaVinci Resolve Studio.\n\nСоздано с помощью Google AI Studio и Gemini 2.5 Pro.",
        "dlg_adaptive_title": "Настройки адаптивного режима",
        "dlg_waveform_title": "Интерактивный просмотр формы волны и спектрограммы",
        "dlg_log_title": "Консоль выполнения и логи",
        "dlg_batch_title": "Пакетный анализ аудиофайлов",
        "dlg_short_video_title": "Генератор коротких видео",

        # Export
        "export_edl_filter": "EDL файлы (*.edl)",
        "export_xml_filter": "FCPXML файлы (*.xml)",
        "export_csv_filter": "CSV файлы (*.csv)",
        "export_json_filter": "JSON файлы (*.json)",
        "all_files_filter": "Все файлы (*.*)"
    }
}


def get_current_language() -> str:
    """Возвращает текущий код языка ('en', 'uk', 'ru')."""
    return _CURRENT_LANGUAGE


def set_language(lang_code: str) -> bool:
    """Установить активный язык и уведомить слушателей."""
    global _CURRENT_LANGUAGE
    if lang_code not in LANGUAGES:
        return False
    if _CURRENT_LANGUAGE == lang_code:
        return True
    _CURRENT_LANGUAGE = lang_code
    for callback in list(_LISTENERS):
        try:
            callback(_CURRENT_LANGUAGE)
        except Exception:
            pass
    return True


def register_language_listener(callback):
    """Зарегистрировать функцию обратного вызова при смене языка."""
    if callback not in _LISTENERS:
        _LISTENERS.append(callback)


def unregister_language_listener(callback):
    """Удалить функцию обратного вызова."""
    if callback in _LISTENERS:
        _LISTENERS.remove(callback)


def tr(key: str, **kwargs) -> str:
    """
    Получить локализованную строку по ключу.
    Если ключ отсутствует в текущем языке, используется 'en'.
    Поддерживает форматирование: tr("hello_user", name="Alex") -> "Hello, Alex".
    """
    lang_dict = TRANSLATIONS.get(_CURRENT_LANGUAGE, TRANSLATIONS["en"])
    text = lang_dict.get(key)
    if text is None:
        text = TRANSLATIONS["en"].get(key, key)
    
    if kwargs:
        try:
            return text.format(**kwargs)
        except Exception:
            return text
    return text
