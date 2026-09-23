# 🎵 BitMaker

[![Language: English](https://img.shields.io/badge/Language-English-blue)](README.md)
[![Language: Українська](https://img.shields.io/badge/Language-Українська-blue)](README.uk.md)
[![Language: Русский](https://img.shields.io/badge/Language-Русский-green)](README.ru.md)
[![Built with Google AI Studio](https://img.shields.io/badge/Built%20with-Google%20AI%20Studio-4285F4?style=flat-square&logo=google&logoColor=white)](https://aistudio.google.com/)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![DaVinci Resolve](https://img.shields.io/badge/DaVinci%20Resolve-Studio%2018%2F19%2F21-black)](https://www.blackmagicdesign.com/products/davinciresolve)

**BitMaker** — мощная и легкая утилита для автоматического анализа темпа музыки, детекции битов и расстановки маркеров на таймлайне или клипах в **DaVinci Resolve Studio**.

Включает интерактивный графический интерфейс с визуализацией формы звуковой волны (Waveform), встроенным аудиоплеером, ручным редактированием маркеров и историей действий (Undo/Redo).

---

## ✨ Основные возможности

- 🎧 **Автоматический аудиоанализ**:
  - Точное определение темпа (**BPM**).
  - Автоопределение музыкального размера (**3/4** и **4/4**).
  - Расчет RMS-огибающей громкости и динамики.
- 🎚️ **Гибкие режимы разметки**:
  - Разметка по тактовой сетке: от 1 удара до 4 тактов на маркер.
  - **Адаптивный режим**: автоматическое переключение частоты маркеров в зависимости от громкости (тихие / громкие части трека).
- 🌊 **Интерактивный таймлайн**:
  - Отображение огибающей звука в реальном времени.
  - Потоковое воспроизведение с плейхедом и клавишей `Space`.
  - Перетаскивание маркеров мышью (Drag & Drop) и магнитная привязка (`Snap`).
  - Добавление маркера клавишей `M` прямо во время воспроизведения.
  - Полная поддержка отмены/повтора действий (**Undo / Redo** через `Ctrl+Z` / `Ctrl+Y`).
- 🎬 **Интеграция с DaVinci Resolve**:
  - Нанесение маркеров любого цвета напрямую на таймлайн или аудиоклип через DaVinci Scripting API.
  - Автоматическая безопасная сборка и склейка сложных нарезок треков через встроенный FFmpeg.
  - Защита от сбоев при множественных фрагментах на клипе.
- 💾 **Экспорт и интеграция**:
  - **Экспорт маркеров в EDL (`.edl`)**: генерация стандартного файла маркеров CMX 3600 для импорта в любой существующий таймлайн в **DaVinci Resolve** (*Timelines → Import → Timeline Markers from EDL...*).
  - **Экспорт в Final Cut Pro 7 XML (`.xml`)**: генерация стандартного XML со скомпилированным аудиофайлом и маркерами на клипе/таймлайне для **Adobe Premiere Pro** и **Final Cut Pro 7**.
  - **Прямая интеграция с DaVinci Resolve**: нанесение маркеров напрямую в активный проект в один клик через встроенный DaVinci Scripting API (кнопка «📍 Разметить в DaVinci»).
  - **Сохранение в JSON**: выгрузка точных таймингов и метаданных анализа (`music-beats.json`).

---

## ⚙️ Настройка DaVinci Resolve (Включение Scripting API)

Для того чтобы BitMaker мог автоматически подключаться к запущенному DaVinci Resolve и наносить маркеры напрямую:

1. В верхнем меню DaVinci Resolve откройте **Preferences...** (горячие клавиши `Ctrl + ,`).
2. Перейдите во вкладку **System** → раздел **General**.
3. В пункте **External scripting using** установите переключатель на **Local** (или **Network**).
4. Нажмите кнопку **Save**.

> 💡 **Примечание**: Включение Scripting API требуется для прямого управления маркерами по кнопке «📍 Разметить в DaVinci». Экспорт в файлы `.edl` и `.xml` работает автономно даже без запуска DaVinci Resolve.

---

## 💻 Совместимость

- **DaVinci Resolve Studio**: протестировано на **DaVinci Resolve Studio 21.0.2.4** (совместимо с версиями 18, 19, 20, 21+) — прямое управление маркерами через API + импорт маркеров из файлов `.edl`.
- **Adobe Premiere Pro & Final Cut Pro 7**: полная поддержка импорта последовательности и маркеров через создаваемые файлы `.xml` (FCP7 XML).
- **ОС**: Windows 10 / 11 (64-bit).

---

## 🚀 Установка и быстрый старт

### Вариант А: Готовая сборка без установки Python (Portable EXE)
1. Перейдите на страницу **[Releases](https://github.com/Xamirp/DaVinci-tools/releases)** и скачайте архив `BitMaker-Windows-Portable.zip`.
2. Распакуйте архив в удобное место и запустите `BitMaker.exe`.
   > Установка Python, Git и дополнительных библиотек в этом режиме **не требуется**.

---

### Вариант Б: Запуск из исходного кода (Git / Python)

#### Требования:
- **Python**: 3.10 – 3.12 (рекомендуется **[Python 3.12 для Windows](https://www.python.org/downloads/)**).
  > ⚠️ **Важно при установке Python**: обязательно отметьте галочку **"Add python.exe to PATH"** на первом шаге инсталлятора.
- **Git**: для клонирования репозитория. Если Git не установлен, скачайте: **[Git for Windows](https://git-scm.com/download/win)**.
- **FFmpeg**: встроен в папку `bin/` или доступен в системном `PATH`.

#### 1. Клонирование репозитория
Откройте терминал (PowerShell / Командная строка) и выполните:
```bash
git clone https://github.com/Xamirp/DaVinci-tools.git
cd DaVinci-tools
```

#### 2. Инициализация окружения
Запустите скрипт автоматической настройки:
```bat
setup_env.bat
```
Или вручную:
```bash
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt
```

### 3. Запуск

#### Графический интерфейс (GUI):
Дважды кликните по:
```bat
run_gui.bat
```
или выполните в консоли:
```bash
.venv\Scripts\python main.py
```

#### Консольная утилита (CLI):
```bat
run_cli.bat
```
или:
```bash
.venv\Scripts\python beat_marker.py --timeline intro --track-index 2 --frequency 0
```

---

## ⌨️ Горячие клавиши в GUI

| Клавиша | Действие |
|---|---|
| `Space` | Воспроизведение / Пауза аудиоплеера |
| `M` | Поставить маркер в текущей позиции плейхеда |
| `Delete` / `Backspace` | Удалить выбранный маркер |
| `S` | Включить / выключить магнитную привязку (Snap) |
| `Ctrl + Z` | Отменить последнее действие (Undo) |
| `Ctrl + Y` / `Ctrl + Shift + Z` | Повторить отмененное действие (Redo) |
| `F5` | Обновить подключение к DaVinci Resolve |

---

## 📁 Структура проекта

```
BitMaker/
├── bin/                   # Исполняемые файлы FFmpeg
│   ├── .gitkeep
│   ├── ffmpeg.exe
│   └── ffprobe.exe
├── gui/                   # Модули интерфейса (tkinter / ttk)
│   ├── audio_player.py    # Потоковый плеер (sounddevice)
│   ├── command_manager.py # Паттерн Command & Undo/Redo
│   ├── dialogs.py         # Диалоги настроек, логов и окно прогресса
│   ├── i18n.py            # Модуль мультиязычности (EN / UK / RU)
│   ├── panels.py          # Модульные панели интерфейса
│   ├── theme.py           # Темная тема DaVinci Resolve Studio
│   └── timeline_panel.py  # Интерактивный Waveform Canvas
├── beat_marker.py         # Ядро детекции битов, ffmpeg и DaVinci API
├── beat_marker_gui.py     # Главное окно GUI приложения
├── edl_exporter.py        # Экспортер маркеров в CMX 3600 EDL
├── fcp_xml_exporter.py    # Экспортер в Final Cut Pro 7 XML
├── main.py                # Точка входа
├── requirements.txt       # Зависимости Python
├── run_gui.bat            # Скрипт запуска GUI
├── run_cli.bat            # Скрипт запуска CLI
├── setup_env.bat          # Скрипт быстрой установки окружения
├── LICENSE                # Apache 2.0 License
└── README.md              # Документация проекта
```

---

## 🤝 О проекте и разработка

Проект спроектирован и разработан с использованием **[Google AI Studio](https://aistudio.google.com/)** & **Google Gemini**.

---

## 📄 Лицензия

Проект распространяется под лицензией [Apache License 2.0](LICENSE).
