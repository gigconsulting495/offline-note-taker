"""
Module Transcriber — Transcription audio via mlx-whisper.

Utilise le modèle distil-large-v3 via mlx-whisper,
optimisé pour Apple Silicon (GPU/ANE via le framework MLX).
La langue est forcée par l'utilisateur ("fr" ou "en").
"""

import gc
from pathlib import Path

import mlx_whisper

from src.config import (
    WHISPER_MODEL,
    DEFAULT_LANGUAGE,
)

# Mapping des noms de modèles vers les repos Hugging Face MLX
MLX_MODEL_REPOS = {
    "distil-large-v3": "mlx-community/distil-whisper-large-v3",
    "large-v3": "mlx-community/whisper-large-v3-mlx",
    "large-v2": "mlx-community/whisper-large-v2-mlx",
    "medium": "mlx-community/whisper-medium-mlx",
    "small": "mlx-community/whisper-small-mlx",
    "base": "mlx-community/whisper-base-mlx",
    "tiny": "mlx-community/whisper-tiny-mlx",
}


def transcribe(audio_path: str | Path, language: str | None = None) -> list[dict]:
    """
    Transcrit un fichier audio en texte.

    Args:
        audio_path: Chemin vers le fichier WAV (16kHz, Mono).
        language: Code langue forcé ("fr" ou "en"). Défaut: config.

    Returns:
        Liste de segments : [{"start": float, "end": float, "text": str}, ...]
    """
    audio_path = Path(audio_path)
    lang = language or DEFAULT_LANGUAGE
    model_repo = MLX_MODEL_REPOS.get(WHISPER_MODEL, f"mlx-community/{WHISPER_MODEL}")

    print(f"▸ Chargement du modèle de transcription ({WHISPER_MODEL})...")
    print(f"  Repo MLX : {model_repo}")
    
    if lang is not None:
        print(f"▸ Transcription en cours (langue forcée : {lang})...")
        transcribe_kwargs = {"language": lang, "task": "transcribe"}
    else:
        print(f"▸ Transcription en cours (détection automatique de la langue)...")
        transcribe_kwargs = {"task": "transcribe"}

    result = mlx_whisper.transcribe(
        str(audio_path),
        path_or_hf_repo=model_repo,
        word_timestamps=False,
        verbose=False,
        **transcribe_kwargs
    )

    # Extraction des segments avec timestamps
    segments = []
    if "segments" in result:
        for seg in result["segments"]:
            segments.append({
                "start": round(seg.get("start", 0.0), 3),
                "end": round(seg.get("end", 0.0), 3),
                "text": seg.get("text", "").strip(),
            })
    else:
        # Fallback : texte brut sans segmentation
        segments.append({
            "start": 0.0,
            "end": 0.0,
            "text": result.get("text", "").strip(),
        })

    print(f"  {len(segments)} segments transcrits ✓")

    # ── Libération mémoire explicite ─────────────────────────────────
    del result
    gc.collect()
    print("  Mémoire MLX libérée ✓")

    return segments
