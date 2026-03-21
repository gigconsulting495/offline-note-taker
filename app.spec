# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec — Note Taker Offline
Application macOS standalone (usage personnel uniquement).
"""

import os
import sys
from pathlib import Path
from PyInstaller.utils.hooks import collect_submodules, collect_data_files

block_cipher = None

PROJECT_ROOT = os.path.abspath('.')
VENV_SITE = os.path.join(PROJECT_ROOT, '.venv', 'lib')

# Trouver le répertoire site-packages dynamiquement
site_packages = None
for root, dirs, files in os.walk(VENV_SITE):
    if root.endswith('site-packages'):
        site_packages = root
        break

# Chemin vers customtkinter pour inclure ses assets (thèmes, JSON, etc.)
ctk_path = os.path.join(site_packages, 'customtkinter')

a = Analysis(
    ['src/main.py'],
    pathex=[PROJECT_ROOT],
    binaries=[
        # ffmpeg est nécessaire pour la conversion audio
        ('/opt/homebrew/bin/ffmpeg', '.'),
    ],
    datas=[
        # Assets du projet (logos)
        ('assets/logos', 'assets/logos'),
        # Fichier .env (token HF)
        ('.env', '.'),
        # CustomTkinter assets (thèmes, etc.) — requis pour le rendu GUI
        (ctk_path, 'customtkinter'),
        # Pyannote data files (config YAML requis au runtime)
        (os.path.join(site_packages, 'pyannote'), 'pyannote'),
        # Lightning data files
        (os.path.join(site_packages, 'lightning'), 'lightning'),
        (os.path.join(site_packages, 'lightning_fabric'), 'lightning_fabric'),
        (os.path.join(site_packages, 'pytorch_lightning'), 'pytorch_lightning'),
        (os.path.join(site_packages, 'torchcodec'), 'torchcodec'),
    ] + collect_data_files('mlx') + collect_data_files('mlx_whisper') + collect_data_files('torchcodec'),
    hiddenimports=[
        # === Torch & co ===
        'torch',
        'torch.utils',
        'torch.utils.data',
        'torchaudio',
        'torchaudio.backend',
        # === MLX ===
        'mlx',
        'mlx.core',
        'mlx.nn',
        'mlx_whisper',
    ] + collect_submodules('mlx') + collect_submodules('mlx_whisper') + [
        # === Pyannote ===
        'pyannote',
        'pyannote.audio',
        'pyannote.audio.pipelines',
        'pyannote.core',
        'pyannote.pipeline',
        'pyannote.database',
        'asteroid_filterbanks',
    ] + collect_submodules('torchcodec') + [
        # === Audio ===
        'sounddevice',
        'soundfile',
        'pydub',
        # === GUI ===
        'customtkinter',
        'PIL',
        'PIL.Image',
        'PIL.ImageTk',
        'tkinter',
        # === Lightning (requis par pyannote) ===
        'lightning',
        'lightning.fabric',
        'lightning_fabric',
        'pytorch_lightning',
        # === Divers ===
        'dotenv',
        'typer',
        'rich',
        'rich.console',
        'rich.panel',
        'audioop',
        'audioop_lts',
        # === Source du projet ===
        'src',
        'src.config',
        'src.pipeline',
        'src.gui',
        'src.audio_manager',
        'src.diarizer',
        'src.transcriber',
        'src.exporter',
        'src.post_processing',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    cipher=block_cipher,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='Note Taker Offline',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,       # Pas de console (mode windowed)
    disable_windowed_traceback=False,
    argv_emulation=True,  # Requis pour macOS .app
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='assets/AppIcon.icns',
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='Note Taker Offline',
)

app = BUNDLE(
    coll,
    name='Note Taker Offline.app',
    icon='assets/AppIcon.icns',
    bundle_identifier='com.gigconsulting.notetakeroffline',
    info_plist={
        'CFBundleName': 'Note Taker Offline',
        'CFBundleDisplayName': 'Note Taker Offline',
        'CFBundleVersion': '1.0.0',
        'CFBundleShortVersionString': '1.0.0',
        'NSMicrophoneUsageDescription': 'Cette application nécessite l\'accès au microphone pour enregistrer les réunions.',
        'NSHighResolutionCapable': True,
    },
)
