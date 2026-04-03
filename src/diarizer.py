"""
Module Diarizer — Identification des locuteurs via Pyannote 3.1.

Exécute la diarisation sur un fichier WAV et retourne une liste de segments
avec les timestamps et les IDs des locuteurs.
Libère explicitement la mémoire GPU/MPS après traitement.
"""

import gc
import logging
import torch
from pathlib import Path

from pyannote.audio import Pipeline
from pyannote.audio.pipelines.utils.hook import ProgressHook

from src.config import (
    HF_TOKEN,
    DIARIZATION_MODEL,
    MIN_SPEAKERS,
    MAX_SPEAKERS,
)

logger = logging.getLogger(__name__)


def diarize(audio_path: str | Path, min_speakers: int | None = None, max_speakers: int | None = None) -> list[dict]:
    """
    Exécute la diarisation sur un fichier audio.

    Args:
        audio_path: Chemin vers le fichier WAV (16kHz, Mono).
        min_speakers: Nombre minimum de locuteurs (défaut: config).
        max_speakers: Nombre maximum de locuteurs (défaut: config).

    Returns:
        Liste de segments : [{"start": float, "end": float, "speaker": str}, ...]

    Raises:
        ValueError: Si le token HF n'est pas configuré.
    """
    audio_path = Path(audio_path)
    min_spk = min_speakers or MIN_SPEAKERS
    max_spk = max_speakers or MAX_SPEAKERS

    if not HF_TOKEN:
        raise ValueError(
            "Token Hugging Face non configuré. "
            "Renseignez HF_TOKEN dans le fichier .env\n"
            "Obtenez votre token ici : https://huggingface.co/settings/tokens"
        )

    logger.info("Chargement du modèle de diarisation (%s)...", DIARIZATION_MODEL)
    pipeline = Pipeline.from_pretrained(DIARIZATION_MODEL, token=HF_TOKEN)

    # Utiliser MPS (Metal) si disponible, sinon CPU
    if torch.backends.mps.is_available():
        pipeline.to(torch.device("mps"))
        logger.info("Accélération MPS (Metal) activée")
    else:
        logger.warning("MPS non disponible, utilisation du CPU")

    if min_spk and max_spk:
        logger.info("Diarisation en cours (%s-%s locuteurs attendus)...", min_spk, max_spk)
    else:
        logger.info("Diarisation en cours (nombre de locuteurs détecté automatiquement)...")

    with ProgressHook() as hook:
        diarization = pipeline(
            str(audio_path),
            min_speakers=min_spk,
            max_speakers=max_spk,
            hook=hook,
        )

    # Extraction des segments (compatible pyannote v3 et v4)
    segments = []

    # pyannote v4 : DiarizeOutput.speaker_diarization → Annotation
    # pyannote v3 : le résultat est directement une Annotation
    if hasattr(diarization, 'speaker_diarization'):
        annotation = diarization.speaker_diarization
    else:
        annotation = diarization

    for turn, _, speaker in annotation.itertracks(yield_label=True):
        segments.append({
            "start": round(turn.start, 3),
            "end": round(turn.end, 3),
            "speaker": speaker,
        })

    logger.info("%d segments identifiés pour %d locuteurs",
                len(segments), len(set(s['speaker'] for s in segments)))

    # ── Libération mémoire explicite ─────────────────────────────────
    del pipeline
    del diarization
    if torch.backends.mps.is_available():
        torch.mps.empty_cache()
    gc.collect()
    logger.info("Mémoire GPU/MPS libérée")

    return segments
