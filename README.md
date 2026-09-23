# 🎵 BitMaker

[![Language: English](https://img.shields.io/badge/Language-English-green)](README.md)
[![Language: Українська](https://img.shields.io/badge/Language-Українська-blue)](README.uk.md)
[![Language: Русский](https://img.shields.io/badge/Language-Русский-blue)](README.ru.md)
[![Built with Google AI Studio](https://img.shields.io/badge/Built%20with-Google%20AI%20Studio-4285F4?style=flat-square&logo=google&logoColor=white)](https://aistudio.google.com/)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![DaVinci Resolve](https://img.shields.io/badge/DaVinci%20Resolve-Studio%2018%2F19%2F21-black)](https://www.blackmagicdesign.com/products/davinciresolve)

**BitMaker** is a powerful and lightweight AI-driven tool designed for video editors to automatically analyze musical rhythm, detect beats, and place markers on timelines or audio clips in **DaVinci Resolve Studio**.

It includes an interactive graphical interface with real-time waveform visualization, a built-in audio player, drag-and-drop marker editing, magnetic snapping, and a full Undo/Redo history stack.

---

## ✨ Key Features

- 🎧 **Automatic AI Audio Analysis**:
  - Accurate tempo detection (**BPM**).
  - Time signature recognition (**3/4** and **4/4**).
  - RMS volume envelope and musical dynamic segmentation.
- 🎚️ **Flexible Marker Density**:
  - Beat-grid synchronization: from every hit (1 beat) up to every 4 bars.
  - **Adaptive Mode**: dynamic marker frequency adjustment based on loudness (quiet vs. loud/climax sections).
- 🌊 **Interactive Waveform Timeline**:
  - Real-time audio waveform rendering with high-speed Level-of-Detail (LOD) optimization.
  - Streaming audio playback with playhead tracking and `Space` hotkey control.
  - Drag-and-drop marker relocation with magnetic beat snapping (`Snap`).
  - Add markers on the fly with the `M` key during playback.
  - Full Undo / Redo support (`Ctrl+Z` / `Ctrl+Y`).
- 🎬 **Seamless DaVinci Resolve Integration**:
  - One-click direct marker placement via the official DaVinci Resolve Scripting API.
  - Robust automated audio assembly and seamless baking for multi-clip and sliced track montages via embedded FFmpeg.
  - Target selection: place markers on clip items or directly onto the timeline ruler.
  - Universal marker cleaning by target across all marker colors.
- 💾 **Export & Cross-Platform Compatibility**:
  - **EDL Marker Export (`.edl`)**: generate industry-standard CMX 3600 marker lists to import markers into any timeline in **DaVinci Resolve** (*Timelines → Import → Timeline Markers from EDL...*).
  - **Final Cut Pro 7 XML Export (`.xml`)**: export sequences and clip/timeline markers for **Adobe Premiere Pro** and **Final Cut Pro 7**.
  - **JSON Beat Export**: export clean timestamps and metadata (`music-beats.json`).
- 🌐 **Multi-Language Interface (i18n)**:
  - Full support for **English**, **Ukrainian**, and **Russian**.
  - Instant language switching directly from the top bar and menu.

---

## ⚙️ DaVinci Resolve Setup (Enabling Scripting API)

To allow BitMaker to automatically connect to a running DaVinci Resolve Studio instance and place markers directly:

1. In DaVinci Resolve, open **Preferences...** (shortcut: `Ctrl + ,`).
2. Navigate to the **System** tab → **General** section.
3. In the **External scripting using** setting, select **Local** (or **Network**).
4. Click **Save**.

> 💡 **Note**: Enabling the Scripting API is required for direct one-click marker placement via the "🎯 Place Markers in DaVinci" button. Exporting to `.edl`, `.xml`, and `.json` works autonomously even without DaVinci Resolve running.

---

## 💻 Compatibility

- **DaVinci Resolve Studio**: Tested on **DaVinci Resolve Studio 21.0.2.4** (compatible with versions 18, 19, 20, 21+) — direct API integration + EDL marker import.
- **Adobe Premiere Pro & Final Cut Pro 7**: Full support for sequence and marker import via generated `.xml` (FCP7 XML) files.
- **Operating System**: Windows 10 / 11 (64-bit).

---

## 🚀 Installation & Quick Start

### Option A: Portable Standalone Build (No Python installation required)
1. Go to the **[Releases](https://github.com/Xamirp/DaVinci-tools/releases)** page and download `BitMaker-Windows-Portable.zip`.
2. Extract the archive to any folder and launch `BitMaker.exe`.
   > No Python, Git, or third-party package installation is required in this mode.

---

### Option B: Running from Source (Git / Python)

#### Requirements:
- **Python**: 3.10 – 3.12 (Recommended: **[Python 3.12 for Windows](https://www.python.org/downloads/)**).
  > ⚠️ **Important during Python installation**: Check the box **"Add python.exe to PATH"** on the first setup screen.
- **Git**: To clone the repository. If not installed, download: **[Git for Windows](https://git-scm.com/download/win)**.
- **FFmpeg**: Bundled inside `bin/` or available in system `PATH`.

#### 1. Clone the Repository
Open a terminal (PowerShell / Command Prompt) and run:
```bash
git clone https://github.com/Xamirp/DaVinci-tools.git
cd DaVinci-tools
```

#### 2. Initialize Environment
Run the automatic setup script:
```bat
setup_env.bat
```
Or set up manually:
```bash
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt
```

### 3. Launching

#### Graphical User Interface (GUI):
Double-click:
```bat
run_gui.bat
```
Or run via console:
```bash
.venv\Scripts\python main.py
```

#### Command Line Interface (CLI):
```bat
run_cli.bat
```
Or:
```bash
.venv\Scripts\python beat_marker.py --timeline intro --track-index 2 --frequency 0
```

---

## ⌨️ Keyboard Shortcuts

| Shortcut | Action |
|---|---|
| `Space` | Play / Pause Audio Player |
| `M` | Add Marker at Playhead Position |
| `Delete` / `Backspace` | Delete Selected Marker |
| `S` | Toggle Magnetic Snap |
| `Ctrl + Z` | Undo Last Action |
| `Ctrl + Y` / `Ctrl + Shift + Z` | Redo Action |
| `F5` | Refresh DaVinci Connection |

---

## 📁 Project Structure

```
BitMaker/
├── bin/                   # Bundled FFmpeg binaries
│   ├── .gitkeep
│   ├── ffmpeg.exe
│   └── ffprobe.exe
├── gui/                   # GUI modules (tkinter / ttk)
│   ├── audio_player.py    # Streaming audio player (sounddevice)
│   ├── command_manager.py # Command pattern & Undo/Redo stack
│   ├── dialogs.py         # Settings, logs, and progress dialogs
│   ├── i18n.py            # Multi-language translation system (EN / UK / RU)
│   ├── panels.py          # Modular UI panels
│   ├── theme.py           # DaVinci Resolve Studio dark theme
│   └── timeline_panel.py  # Interactive Waveform Canvas
├── beat_marker.py         # AI beat detection core, FFmpeg & DaVinci API
├── beat_marker_gui.py     # Main GUI application window
├── edl_exporter.py        # CMX 3600 EDL marker exporter
├── fcp_xml_exporter.py    # Final Cut Pro 7 XML exporter
├── main.py                # Main entrypoint
├── requirements.txt       # Python dependencies
├── run_gui.bat            # GUI launcher script
├── run_cli.bat            # CLI launcher script
├── setup_env.bat          # Automatic environment setup script
├── LICENSE                # Apache 2.0 License
├── README.md              # English documentation (default)
├── README.uk.md           # Ukrainian documentation
└── README.ru.md           # Russian documentation
```

---

## 🤝 Credits & Acknowledgements

Designed and developed with the assistance of **[Google AI Studio](https://aistudio.google.com/)** & **Google Gemini**.

---

## 📄 License

This project is licensed under the [Apache License 2.0](LICENSE).
