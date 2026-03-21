"""
Module Exporter — Génération du fichier JSON structuré.

Produit un fichier JSON contenant les métadonnées de la réunion
et la liste des segments alignés (horodatage, locuteur, texte).
"""

import json
from datetime import datetime
from pathlib import Path

from src.config import OUTPUT_DIR, JSON_INDENT


def export_files(
    conversation: list[dict],
    run_folder: Path,
    source_file: str,
    language: str,
) -> Path:
    """
    Exporte la conversation fluide dans des fichiers JSON et TXT structurés.

    Args:
        conversation: Liste de blocs [{speaker, start, end, timestamp, content}, ...]
        run_folder: Dossier de sortie dédié pour cette réunion.
        source_file: Nom du fichier audio source (pour les métadonnées).
        language: Code langue utilisé ("fr" ou "en").

    Returns:
        Path vers le fichier JSON créé.
    """
    json_path = run_folder / "transcript.json"
    txt_path = run_folder / "transcript.txt"

    # Calcul des métadonnées
    total_duration: float = max((c["end"] for c in conversation), default=0.0)
    unique_speakers = sorted(set(c["speaker"] for c in conversation))

    # --- 1. EXPORT JSON ---
    data = {
        "metadata": {
            "source_file": source_file,
            "language": language,
            "processed_at": datetime.now().isoformat(),
            "duration_seconds": round(total_duration, 2),
            "num_blocks": len(conversation),
            "speakers": unique_speakers,
            "num_speakers": len(unique_speakers),
        },
        "conversation": conversation,
    }

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=JSON_INDENT)

    # --- 2. EXPORT TXT ---
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write(f"Réunion : {source_file}\n")
        f.write(f"Date de traitement : {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
        f.write("=" * 50 + "\n\n")
        
        for block in conversation:
            speaker = block["speaker"]
            timestamp = block["timestamp"]
            content = block["content"]
            f.write(f"[{timestamp}] {speaker} :\n{content}\n\n")

    print(f"  Exports terminés dans : {run_folder.name} ✓")
    print(f"  Fichiers créés : transcript.json, transcript.txt")
    print(f"  Durée de conversation : {_format_duration(total_duration)}")
    print(f"  Locuteurs identifiés : {', '.join(unique_speakers)}")

    return json_path


def _format_duration(seconds: float) -> str:
    """Formate une durée en secondes vers HH:MM:SS."""
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    if h > 0:
        return f"{h}h{m:02d}m{s:02d}s"
    return f"{m}m{s:02d}s"
