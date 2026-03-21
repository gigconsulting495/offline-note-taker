"""
Module Post Processing — Nettoyage et formattage fluide du transcript.

Convertit une série de chunks bruts (issus de l'alignement Diarisation+Transcription)
en de longs blocs de conversation fluides, avec filtrage des bruits et formatage.
"""

import re

def format_timestamp(start: float, end: float) -> str:
    """Formate des temps en secondes vers 'HH:MM:SS - HH:MM:SS'."""
    def format_time(seconds: float) -> str:
        h = int(seconds // 3600)
        m = int((seconds % 3600) // 60)
        s = int(seconds % 60)
        return f"{h:02d}:{m:02d}:{s:02d}"

    return f"{format_time(start)} - {format_time(end)}"

def clean_text(text: str) -> str:
    """Nettoie le texte (espaces doubles, majuscule initiale)."""
    # Espaces multiples -> simple espace
    text = re.sub(r'\s+', ' ', text).strip()
    # Majuscule au début si non vide
    if text:
        text = text[0].upper() + text[1:]
    return text

def process_transcript(raw_chunks: list[dict], max_pause: float = 2.0) -> list[dict]:
    """
    Fusionne les segments consécutifs d'un même speaker s'il n'y a pas
    de pause trop longue, filtre les bruits et les silences.
    """
    processed_conversation = []
    current_block = None

    for chunk in raw_chunks:
        text = chunk.get("text", "").strip()
        speaker = chunk.get("speaker", "UNKNOWN")
        
        # 1. FILTRAGE PRÉVENTIF (Ignorer le bruit)
        if not text or (len(text) < 2 and text in "!?,.;"):
            continue
        if speaker == "UNKNOWN" and len(text.split()) < 2:
            continue # Retire les mots d'hésitation courts et non attribués
            
        # 2. LOGIQUE DE FUSION OU CRÉATION
        if current_block is None:
            # Premier bloc
            current_block = {
                "speaker": speaker,
                "start_raw": chunk["start"],
                "end_raw": chunk["end"],
                "content": text
            }
        else:
            time_gap = chunk["start"] - current_block["end_raw"]
            is_same_speaker = current_block["speaker"] == speaker
            
            # Si même locuteur ET la pause est acceptable on fusionne
            if is_same_speaker and time_gap <= max_pause:
                current_block["content"] += " " + text
                current_block["end_raw"] = chunk["end"] # Mise à jour de la fin
            else:
                # Sinon on valide le bloc actuel et on en démarre un nouveau
                processed_conversation.append({
                    "speaker": current_block["speaker"],
                    "start": round(current_block["start_raw"], 2),
                    "end": round(current_block["end_raw"], 2),
                    "timestamp": format_timestamp(current_block["start_raw"], current_block["end_raw"]),
                    "content": clean_text(current_block["content"])
                })
                current_block = {
                    "speaker": speaker,
                    "start_raw": chunk["start"],
                    "end_raw": chunk["end"],
                    "content": text
                }
                
    # N'oublions pas le tout dernier bloc
    if current_block:
        processed_conversation.append({
            "speaker": current_block["speaker"],
            "start": round(current_block["start_raw"], 2),
            "end": round(current_block["end_raw"], 2),
            "timestamp": format_timestamp(current_block["start_raw"], current_block["end_raw"]),
            "content": clean_text(current_block["content"])
        })
        
    return processed_conversation
