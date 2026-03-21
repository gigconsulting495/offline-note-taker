"""
Module Audio Manager — Enregistrement et conversion de fichiers audio.

Fournit :
- AudioRecorder : enregistrement micro avec Start/Pause/Resume/Stop (écriture par chunks)
- convert_to_wav() : conversion automatique de tout format supporté vers WAV 16kHz Mono PCM 16-bit
"""

import gc
import numpy as np
import sounddevice as sd
import soundfile as sf
from pathlib import Path
from pydub import AudioSegment

from src.config import (
    SAMPLE_RATE,
    CHANNELS,
    SUBTYPE,
    CHUNK_DURATION_SEC,
    RAW_DIR,
    CONVERTED_DIR,
    SUPPORTED_IMPORT_FORMATS,
)


class AudioRecorder:
    """Enregistrement audio en temps réel avec gestion Start/Pause/Resume/Stop."""

    def __init__(self, filename: str = "recording.wav"):
        self.filepath = RAW_DIR / filename
        self.is_recording = False
        self.is_paused = False
        self._stream = None
        self._file = None
        self._chunk_buffer = []

    def start(self):
        """Démarre l'enregistrement."""
        if self.is_recording:
            raise RuntimeError("Enregistrement déjà en cours.")

        self._file = sf.SoundFile(
            str(self.filepath),
            mode="w",
            samplerate=SAMPLE_RATE,
            channels=CHANNELS,
            subtype=SUBTYPE,
        )

        self.is_recording = True
        self.is_paused = False

        self._stream = sd.InputStream(
            samplerate=SAMPLE_RATE,
            channels=CHANNELS,
            dtype="int16",
            callback=self._audio_callback,
            blocksize=int(SAMPLE_RATE * CHUNK_DURATION_SEC),
        )
        self._stream.start()
        return self.filepath

    def pause(self):
        """Met l'enregistrement en pause."""
        if self.is_recording and not self.is_paused:
            self.is_paused = True

    def resume(self):
        """Reprend l'enregistrement après une pause."""
        if self.is_recording and self.is_paused:
            self.is_paused = False

    def stop(self) -> Path:
        """Arrête l'enregistrement et sauvegarde le fichier."""
        if not self.is_recording:
            raise RuntimeError("Aucun enregistrement en cours.")

        self.is_recording = False
        self.is_paused = False

        if self._stream is not None:
            self._stream.stop()
            self._stream.close()
            self._stream = None

        if self._file is not None:
            self._file.close()
            self._file = None

        return self.filepath

    def _audio_callback(self, indata, frames, time_info, status):
        """Callback appelé par sounddevice à chaque chunk audio."""
        if status:
            print(f"  ⚠ Audio callback status: {status}")

        if self.is_recording and not self.is_paused:
            if self._file is not None:
                self._file.write(indata.copy())


def convert_to_wav(input_path: str | Path) -> Path:
    """
    Convertit un fichier audio vers WAV 16kHz Mono PCM 16-bit.

    Args:
        input_path: Chemin vers le fichier audio source (MP3, M4A, etc.)

    Returns:
        Path vers le fichier WAV converti dans data/converted/

    Raises:
        ValueError: Si le format n'est pas supporté.
        FileNotFoundError: Si le fichier source n'existe pas.
    """
    input_path = Path(input_path)

    if not input_path.exists():
        raise FileNotFoundError(f"Fichier non trouvé : {input_path}")

    suffix = input_path.suffix.lower()
    if suffix not in SUPPORTED_IMPORT_FORMATS:
        raise ValueError(
            f"Format '{suffix}' non supporté. "
            f"Formats acceptés : {', '.join(SUPPORTED_IMPORT_FORMATS)}"
        )

    output_filename = f"{input_path.stem}_converted.wav"
    output_path = CONVERTED_DIR / output_filename

    # Si c'est déjà un WAV au bon format, vérifier les paramètres
    if suffix == ".wav":
        info = sf.info(str(input_path))
        if (
            info.samplerate == SAMPLE_RATE
            and info.channels == CHANNELS
            and info.subtype == SUBTYPE
        ):
            # Déjà au bon format, copier simplement
            import shutil
            shutil.copy2(str(input_path), str(output_path))
            return output_path

    # Conversion via pydub (utilise ffmpeg en backend)
    audio = AudioSegment.from_file(str(input_path))
    audio = audio.set_frame_rate(SAMPLE_RATE)
    audio = audio.set_channels(CHANNELS)
    audio = audio.set_sample_width(2)  # 16-bit = 2 octets

    audio.export(str(output_path), format="wav")

    # Libération mémoire
    del audio
    gc.collect()

    return output_path
