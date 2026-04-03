"""
Configuration globale de l'application CR Reunion.
Centralise tous les paramètres, chemins et constantes.
"""

import logging
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# ── Logging centralisé ──────────────────────────────────────────────
# En mode bundled (.app), les logs vont dans un fichier exploitable après coup.
# En mode dev, ils s'affichent aussi dans la console.
_log_format = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
_log_date_format = "%H:%M:%S"

logging.basicConfig(
    level=logging.INFO,
    format=_log_format,
    datefmt=_log_date_format,
    handlers=[logging.StreamHandler()],
)

# Fichier de log persistant dans ~/Documents/CR_Reunions/
_log_dir = Path.home() / "Documents" / "CR_Reunions"
_log_dir.mkdir(parents=True, exist_ok=True)
_file_handler = logging.FileHandler(_log_dir / "app.log", encoding="utf-8")
_file_handler.setFormatter(logging.Formatter(_log_format, datefmt=_log_date_format))
logging.getLogger().addHandler(_file_handler)

if getattr(sys, '_MEIPASS', None):
    # En mode bundled, les data files sont extraits dans _MEIPASS
    PROJECT_ROOT = Path(sys._MEIPASS)
    # Ajouter _MEIPASS au PATH pour que pydub/subprocess trouve ffmpeg
    os.environ["PATH"] = sys._MEIPASS + os.pathsep + os.environ.get("PATH", "")
    # Charger .env depuis le bundle ou depuis le home de l'utilisateur
    _env_bundle = PROJECT_ROOT / ".env"
    _env_home = Path.home() / ".env"
    if _env_bundle.exists():
        load_dotenv(_env_bundle)
    elif _env_home.exists():
        load_dotenv(_env_home)
else:
    PROJECT_ROOT = Path(__file__).resolve().parent.parent
    load_dotenv()

# Données temporaires d'exécution transférées dans le répertoire temp de l'OS
DATA_DIR = Path("/tmp/cr_reunion")
RAW_DIR = DATA_DIR / "raw"
CONVERTED_DIR = DATA_DIR / "converted"

# Le dossier cible global pour l'utilisateur
OUTPUT_DIR = Path.home() / "Documents" / "CR_Reunions"

# Création automatique des répertoires de données
for directory in [RAW_DIR, CONVERTED_DIR, OUTPUT_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# ── Audio ────────────────────────────────────────────────────────────
SAMPLE_RATE = 16_000          # Hz — requis par Whisper et Pyannote
CHANNELS = 1                  # Mono
AUDIO_FORMAT = "WAV"          # Format interne cible
SUBTYPE = "PCM_16"            # PCM 16-bit
CHUNK_DURATION_SEC = 5        # Durée des blocs d'écriture (enregistrement)

SUPPORTED_IMPORT_FORMATS = [".mp3", ".m4a", ".ogg", ".flac", ".wav", ".wma", ".aac"]

# ── Diarisation (Pyannote) ───────────────────────────────────────────
HF_TOKEN = os.getenv("HF_TOKEN")
DIARIZATION_MODEL = "pyannote/speaker-diarization-3.1"
MIN_SPEAKERS = None  # None pour détection automatique
MAX_SPEAKERS = None  # None pour détection automatique

# ── Transcription (Lightning Whisper MLX) ────────────────────────────
WHISPER_MODEL = "large-v3"  # Remplacé car distil-large-v3 est strictement anglophone
WHISPER_QUANT = "4bit"
WHISPER_BATCH_SIZE = 12
DEFAULT_LANGUAGE = None       # None pour auto-détection ("fr" ou "en" gérés par Whisper)

# ── Export ───────────────────────────────────────────────────────────
JSON_INDENT = 2               # Indentation du JSON de sortie
