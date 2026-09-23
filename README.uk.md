# 🎵 BitMaker

[![Language: English](https://img.shields.io/badge/Language-English-blue)](README.md)
[![Language: Українська](https://img.shields.io/badge/Language-Українська-green)](README.uk.md)
[![Language: Русский](https://img.shields.io/badge/Language-Русский-blue)](README.ru.md)
[![Built with Google AI Studio](https://img.shields.io/badge/Built%20with-Google%20AI%20Studio-4285F4?style=flat-square&logo=google&logoColor=white)](https://aistudio.google.com/)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![DaVinci Resolve](https://img.shields.io/badge/DaVinci%20Resolve-Studio%2018%2F19%2F21-black)](https://www.blackmagicdesign.com/products/davinciresolve)

**BitMaker** — потужна та легка утиліта для автоматичного аналізу темпу музики, детекції бітів та розстановки маркерів на таймлайні або кліпах у **DaVinci Resolve Studio**.

Включає інтерактивний графічний інтерфейс із візуалізацією форми звукової хвилі (Waveform), вбудованим аудіоплеєром, ручним редагуванням маркерів та історією дій (Undo/Redo).

---

## ✨ Основні можливості

- 🎧 **Автоматичний аудіоаналіз**:
  - Точне визначення темпу (**BPM**).
  - Автовизначення музичного розміру (**3/4** та **4/4**).
  - Розрахунок RMS-огинаючої гучності та динаміки.
- 🎚️ **Гнучкі режими розмітки**:
  - Розмітка за тактовою сіткою: від 1 удару до 4 тактів на маркер.
  - **Адаптивний режим**: автоматичне перемикання частоти маркерів залежно від гучності (тихі / гучні частини треку).
- 🌊 **Інтерактивний таймлайн**:
  - Відображення форми хвилі звуку в реальному часі.
  - Потокове відтворення з плейхедом та клавішею `Space`.
  - Перетягування маркерів мишею (Drag & Drop) та магнітна прив'язка (`Snap`).
  - Додавання маркера клавішею `M` безпосередньо під час відтворення.
  - Повна підтримка скасування/повернення дій (**Undo / Redo** через `Ctrl+Z` / `Ctrl+Y`).
- 🎬 **Інтеграція з DaVinci Resolve**:
  - Нанесення маркерів будь-якого кольору напряму на таймлайн або аудіокліп через DaVinci Scripting API.
  - Автоматичне безпечне збирання та склеювання складних нарізок треків через вбудований FFmpeg.
  - Захист від збоїв при множинних фрагментах на кліпі.
- 💾 **Експорт та інтеграція**:
  - **Експорт маркерів в EDL (`.edl`)**: генерація стандартного файлу маркерів CMX 3600 для імпорту в будь-який існуючий таймлайн у **DaVinci Resolve** (*Timelines → Import → Timeline Markers from EDL...*).
  - **Експорт у Final Cut Pro 7 XML (`.xml`)**: генерація стандартного XML зі скомпільованим аудіофайлом та маркерами на кліпі/таймлайні для **Adobe Premiere Pro** та **Final Cut Pro 7**.
  - **Пряма інтеграція з DaVinci Resolve**: нанесення маркерів напряму в активний проєкт в один клік через вбудований DaVinci Scripting API (кнопка «📍 Розмітити в DaVinci»).
  - **Збереження в JSON**: вивантаження точних таймінгів та метаданих аналізу (`music-beats.json`).

---

## ⚙️ Налаштування DaVinci Resolve (Увімкнення Scripting API)

Для того щоб BitMaker міг автоматично підключатися до запущеного DaVinci Resolve та наносити маркери напряму:

1. У верхньому меню DaVinci Resolve відкрийте **Preferences...** (гарячі клавіші `Ctrl + ,`).
2. Перейдіть на вкладку **System** → розділ **General**.
3. У пункті **External scripting using** встановіть перемикач на **Local** (або **Network**).
4. Натисніть кнопку **Save**.

> 💡 **Примітка**: Увімкнення Scripting API потрібне для прямого керування маркерами за кнопкою «📍 Розмітити в DaVinci». Експорт у файли `.edl` та `.xml` працює автономно навіть без запуску DaVinci Resolve.

---

## 💻 Сумісність

- **DaVinci Resolve Studio**: протестовано на **DaVinci Resolve Studio 21.0.2.4** (сумісно з версіями 18, 19, 20, 21+) — пряме керування маркерами через API + імпорт маркерів з файлів `.edl`.
- **Adobe Premiere Pro & Final Cut Pro 7**: повна підтримка імпорту послідовності та маркерів через створювані файли `.xml` (FCP7 XML).
- **ОС**: Windows 10 / 11 (64-bit).

---

## 🚀 Встановлення та швидкий старт

### Варіант А: Готова збірка без встановлення Python (Portable EXE)
1. Перейдіть на сторінку **[Releases](https://github.com/Xamirp/DaVinci-tools/releases)** та завантажте архів `BitMaker-Windows-Portable.zip`.
2. Розархівуйте архів у зручне місце та запустіть `BitMaker.exe`.
   > Встановлення Python, Git та додаткових бібліотек у цьому режимі **не потрібне**.

---

### Варіант Б: Запуск із вихідного коду (Git / Python)

#### Вимоги:
- **Python**: 3.10 – 3.12 (рекомендується **[Python 3.12 для Windows](https://www.python.org/downloads/)**).
  > ⚠️ **Важливо під час встановлення Python**: обов'язково позначте прапорець **"Add python.exe to PATH"** на першому кроці інсталятора.
- **Git**: для клонування репозиторію. Якщо Git не встановлено, завантажте: **[Git for Windows](https://git-scm.com/download/win)**.
- **FFmpeg**: вбудований у папку `bin/` або доступний у системному `PATH`.

#### 1. Клонування репозиторію
Відкрийте термінал (PowerShell / Командний рядок) та виконайте:
```bash
git clone https://github.com/Xamirp/DaVinci-tools.git
cd DaVinci-tools
```

#### 2. Ініціалізація оточення
Запустіть скрипт автоматичного налаштування:
```bat
setup_env.bat
```
Або вручну:
```bash
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt
```

### 3. Запуск

#### Графічний інтерфейс (GUI):
Двічі клікніть по:
```bat
run_gui.bat
```
або виконайте в консолі:
```bash
.venv\Scripts\python main.py
```

#### Консольна утиліта (CLI):
```bat
run_cli.bat
```
або:
```bash
.venv\Scripts\python beat_marker.py --timeline intro --track-index 2 --frequency 0
```

---

## ⌨️ Гарячі клавіші в GUI

| Клавіша | Дія |
|---|---|
| `Space` | Відтворення / Пауза аудіоплеєра |
| `M` | Поставити маркер у поточній позиції плейхеда |
| `Delete` / `Backspace` | Видалити вибраний маркер |
| `S` | Увімкнути / вимкнути магнітну прив'язку (Snap) |
| `Ctrl + Z` | Скасувати останню дію (Undo) |
| `Ctrl + Y` / `Ctrl + Shift + Z` | Повернути скасовану дію (Redo) |
| `F5` | Оновити підключення до DaVinci Resolve |

---

## 📁 Структура проєкту

```
BitMaker/
├── bin/                   # Виконувані файли FFmpeg
│   ├── .gitkeep
│   ├── ffmpeg.exe
│   └── ffprobe.exe
├── gui/                   # Модулі інтерфейсу (tkinter / ttk)
│   ├── audio_player.py    # Потоковий плеєр (sounddevice)
│   ├── command_manager.py # Паттерн Command & Undo/Redo
│   ├── dialogs.py         # Діалоги налаштувань, логів та вікно прогресу
│   ├── i18n.py            # Модуль багатомовності (EN / UK / RU)
│   ├── panels.py          # Модульні панелі інтерфейсу
│   ├── theme.py           # Темна тема DaVinci Resolve Studio
│   └── timeline_panel.py  # Інтерактивний Waveform Canvas
├── beat_marker.py         # Ядро детекції бітів, ffmpeg та DaVinci API
├── beat_marker_gui.py     # Головне вікно GUI додатку
├── edl_exporter.py        # Експортер маркерів у CMX 3600 EDL
├── fcp_xml_exporter.py    # Експортер у Final Cut Pro 7 XML
├── main.py                # Точка входу
├── requirements.txt       # Залежності Python
├── run_gui.bat            # Скрипт запуску GUI
├── run_cli.bat            # Скрипт запуску CLI
├── setup_env.bat          # Скрипт швидкого встановлення оточення
├── LICENSE                # Apache 2.0 License
└── README.md              # Документація проєкту
```

---

## 🤝 Про проєкт та розробка

Проєкт спроєктовано та розроблено з використанням **[Google AI Studio](https://aistudio.google.com/)** & **Google Gemini**.

---

## 📄 Ліцензія

Проєкт розповсюджується під ліцензією [Apache License 2.0](LICENSE).
