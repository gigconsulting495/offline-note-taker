"""
Module Pipeline — Orchestrateur séquentiel du traitement.

Enchaîne de manière strictement séquentielle :
1. Conversion audio (si nécessaire)
2. Diarisation (puis libération RAM)
3. Transcription (puis libération RAM)
4. Alignement temporel (fusion diarisation + transcription)
5. Export JSON
"""

import time
from pathlib import Path

from datetime import datetime
from src.config import CONVERTED_DIR, SUPPORTED_IMPORT_FORMATS, OUTPUT_DIR
from src.audio_manager import convert_to_wav
from src.diarizer import diarize
from src.transcriber import transcribe
from src.exporter import export_files


def align_segments(
    diarization_segments: list[dict],
    transcription_segments: list[dict],
) -> list[dict]:
    """
    Aligne les segments de diarisation (speaker) avec les segments
    de transcription (texte) par correspondance temporelle.

    Méthode : pour chaque segment de transcription, on cherche le segment
    de diarisation qui a le plus grand chevauchement temporel.

    Args:
        diarization_segments: [{start, end, speaker}, ...]
        transcription_segments: [{start, end, text}, ...]

    Returns:
        Liste alignée : [{start, end, speaker, text}, ...]
    """
    aligned = []

    for t_seg in transcription_segments:
        t_start = t_seg["start"]
        t_end = t_seg["end"]

        # Trouver le meilleur speaker par chevauchement maximal
        best_speaker = "UNKNOWN"
        best_overlap = 0.0

        for d_seg in diarization_segments:
            # Calcul du chevauchement
            overlap_start = max(t_start, d_seg["start"])
            overlap_end = min(t_end, d_seg["end"])
            overlap = max(0.0, overlap_end - overlap_start)

            if overlap > best_overlap:
                best_overlap = overlap
                best_speaker = d_seg["speaker"]

        aligned.append({
            "start": t_start,
            "end": t_end,
            "speaker": best_speaker,
            "text": t_seg["text"],
        })

    return aligned


def run_pipeline(
    input_path: str | Path,
    language: str | None = None,
    output_name: str | None = None,
    min_speakers: int | None = None,
    max_speakers: int | None = None,
) -> Path:
    """
    Exécute le pipeline complet de traitement d'une réunion.

    Déroulement séquentiel :
    1. Conversion audio → WAV 16kHz Mono
    2. Diarisation → segments speakers → libération RAM
    3. Transcription → segments texte → libération RAM
    4. Alignement temporel
    5. Export JSON

    Args:
        input_path: Chemin vers le fichier audio (tout format supporté).
        language: Code langue ("fr" ou "en").
        output_name: Nom du fichier JSON de sortie (sans extension).
        min_speakers: Nombre minimum de locuteurs.
        max_speakers: Nombre maximum de locuteurs.

    Returns:
        Path vers le fichier JSON de sortie.
    """
    input_path = Path(input_path)
    start_time = time.time()

    print("╔══════════════════════════════════════════════════════════╗")
    print("║   CR Reunion — Pipeline de traitement                   ║")
    print("╚══════════════════════════════════════════════════════════╝")
    print(f"  Fichier : {input_path.name}")
    print(f"  Langue  : {language if language else 'Auto-détection'}")
    print("")

    # ── Étape 1 : Conversion audio ───────────────────────────────────
    print("━━━ Étape 1/5 : Conversion audio ━━━")
    suffix = input_path.suffix.lower()
    if suffix in SUPPORTED_IMPORT_FORMATS:
        wav_path = convert_to_wav(input_path)
        print(f"  Fichier converti : {wav_path.name} ✓")
    else:
        raise ValueError(f"Format non supporté : {suffix}")
    print("")

    # ── Étape 2 : Diarisation ────────────────────────────────────────
    print("━━━ Étape 2/5 : Diarisation ━━━")
    diarization_segments = diarize(wav_path, min_speakers, max_speakers)
    print("")

    # ── Étape 3 : Transcription ──────────────────────────────────────
    print("━━━ Étape 3/5 : Transcription ━━━")
    transcription_segments = transcribe(wav_path, language)
    print("")

    # ── Étape 4 : Alignement ─────────────────────────────────────────
    print("━━━ Étape 4/5 : Alignement temporel ━━━")
    aligned_segments = align_segments(diarization_segments, transcription_segments)
    print(f"  {len(aligned_segments)} segments bruts alignés ✓")
    print("")

    # ── Étape 4.5 : Post-processing ──────────────────────────────────
    from src.post_processing import process_transcript
    print("━━━ Étape 4.5/5 : Post-processing (Fluide) ━━━")
    processed_conversation = process_transcript(aligned_segments)
    print(f"  {len(processed_conversation)} blocs de conversation continus générés ✓")
    print("")

    # ── Étape 5 : Export ─────────────────────────────────────────────
    print("━━━ Étape 5/5 : Export (JSON & TXT) ━━━")
    
    # Création du dossier horodaté de la réunion
    timestamp_str = datetime.now().strftime("%Y-%m-%d_%Hh%M")
    base_name = output_name or input_path.stem
    folder_name = f"{timestamp_str}_{base_name}"
    run_folder = OUTPUT_DIR / folder_name
    run_folder.mkdir(parents=True, exist_ok=True)

    output_path = export_files(
        conversation=processed_conversation,
        run_folder=run_folder,
        source_file=input_path.name,
        language=language,
    )

    # ── Sauvegarde de l'Audio ─────────────────────────────────────────
    import shutil
    print("")
    print("━━━ Conservation de l'Audio ━━━")
    
    if wav_path.exists():
        final_audio_path = run_folder / wav_path.name
        # On déplace l'audio de travail de /tmp vers le dossier de la réunion
        shutil.move(str(wav_path), str(final_audio_path))
        print(f"  Fichier audio conservé : {final_audio_path.name} ✓")
    else:
        print("  Aucun fichier audio de transit trouvé ✓")

    elapsed = time.time() - start_time
    print("")
    print("╔══════════════════════════════════════════════════════════╗")
    print(f"║   Traitement terminé en {elapsed:.1f}s")
    print(f"║   Dossier de sortie : {run_folder}")
    print("╚══════════════════════════════════════════════════════════╝")

    return output_path
