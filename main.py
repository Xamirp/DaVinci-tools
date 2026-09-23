#!/usr/bin/env python3
"""BitMaker — точка входа в приложение.
"""

import sys
import os
import subprocess
from pathlib import Path

# Автоматический перезапуск в локальном .venv если запущен глобальный Python
if not getattr(sys, "frozen", False):
    SCRIPT_DIR = Path(__file__).parent.resolve()
    _VENV_PYTHON = SCRIPT_DIR / ".venv" / "Scripts" / "python.exe"
    if not _VENV_PYTHON.exists():
        _VENV_PYTHON = SCRIPT_DIR / ".venv" / "bin" / "python"

    if _VENV_PYTHON.exists():
        try:
            current_exe = Path(sys.executable).resolve()
            target_exe = _VENV_PYTHON.resolve()
            if current_exe != target_exe:
                # Re-launch under .venv python
                sys.exit(subprocess.call([str(target_exe)] + sys.argv))
        except Exception:
            pass

from beat_marker_gui import main

if __name__ == "__main__":
    main()
