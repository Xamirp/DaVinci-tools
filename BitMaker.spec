# -*- mode: python ; coding: utf-8 -*-

from PyInstaller.utils.hooks import collect_data_files, collect_dynamic_libs

datas = collect_data_files('librosa')
datas += collect_data_files('soundfile')
binaries = collect_dynamic_libs('soundfile')
binaries += collect_dynamic_libs('sounddevice')

hiddenimports = [
    'librosa',
    'scipy',
    'scipy.signal',
    'scipy.fft',
    'sounddevice',
    'soundfile',
    'numba',
    'soxr',
    'sklearn',
    'lazy_loader',
    'gui',
    'gui.theme',
    'gui.panels',
    'gui.dialogs',
    'gui.audio_player',
    'gui.command_manager',
    'gui.timeline_panel',
    'beat_marker',
    'beat_marker_gui'
]

a = Analysis(
    ['main.py'],
    pathex=['.'],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='BitMaker',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='BitMaker',
)
