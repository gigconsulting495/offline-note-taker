"""
Script de test — Génère un fichier audio synthétique avec plusieurs
"locuteurs" simulés (tons de voix différents) pour valider le pipeline.
"""

import numpy as np
import soundfile as sf
from pathlib import Path

# Configuration
SAMPLE_RATE = 16000
OUTPUT_DIR = Path(__file__).resolve().parent.parent / "data" / "raw"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_FILE = OUTPUT_DIR / "test_reunion.wav"

# Simulation de 3 "locuteurs" avec des fréquences fondamentales différentes
# Chaque locuteur parle pendant quelques secondes avec des pauses entre eux
segments = [
    # (fréquence Hz, durée secondes, description)
    {"freq": 150, "duration": 4.0, "speaker": "Voix grave (Speaker 1)"},
    {"freq": 0,   "duration": 1.0, "speaker": "Silence"},
    {"freq": 280, "duration": 3.5, "speaker": "Voix médium (Speaker 2)"},
    {"freq": 0,   "duration": 0.8, "speaker": "Silence"},
    {"freq": 420, "duration": 3.0, "speaker": "Voix aiguë (Speaker 3)"},
    {"freq": 0,   "duration": 1.0, "speaker": "Silence"},
    {"freq": 150, "duration": 3.5, "speaker": "Voix grave (Speaker 1)"},
    {"freq": 0,   "duration": 0.5, "speaker": "Silence"},
    {"freq": 280, "duration": 4.0, "speaker": "Voix médium (Speaker 2)"},
    {"freq": 0,   "duration": 0.8, "speaker": "Silence"},
    {"freq": 420, "duration": 2.5, "speaker": "Voix aiguë (Speaker 3)"},
    {"freq": 0,   "duration": 1.0, "speaker": "Silence"},
    {"freq": 150, "duration": 3.0, "speaker": "Voix grave (Speaker 1)"},
]

def generate_speech_like_tone(freq: float, duration: float, sr: int) -> np.ndarray:
    """Génère un signal quasi-vocal (fondamentale + harmoniques + bruit)."""
    t = np.linspace(0, duration, int(sr * duration), endpoint=False)

    if freq == 0:
        # Silence avec un léger bruit de fond
        return np.random.randn(len(t)) * 0.001

    # Fondamentale + harmoniques pour simuler une voix
    signal = np.sin(2 * np.pi * freq * t) * 0.4
    signal += np.sin(2 * np.pi * freq * 2 * t) * 0.2    # 2e harmonique
    signal += np.sin(2 * np.pi * freq * 3 * t) * 0.1    # 3e harmonique
    signal += np.sin(2 * np.pi * freq * 4 * t) * 0.05   # 4e harmonique

    # Modulation d'amplitude (simule le rythme de parole)
    mod = 0.5 + 0.5 * np.sin(2 * np.pi * 3.5 * t)  # ~3.5 Hz = rythme syllabique
    signal *= mod

    # Ajout de bruit (respiration, bruit de salle)
    noise = np.random.randn(len(t)) * 0.02
    signal += noise

    # Normalisation
    signal = signal / np.max(np.abs(signal)) * 0.7

    return signal


def main():
    print("▸ Génération du fichier audio de test...")
    print(f"  Sortie : {OUTPUT_FILE}")
    print()

    all_audio = []
    time_cursor = 0.0

    for seg in segments:
        audio = generate_speech_like_tone(seg["freq"], seg["duration"], SAMPLE_RATE)
        all_audio.append(audio)
        end = time_cursor + seg["duration"]
        print(f"  [{time_cursor:6.1f}s → {end:6.1f}s] {seg['speaker']}")
        time_cursor = end

    # Concaténation
    full_audio = np.concatenate(all_audio)

    # Conversion en int16
    full_audio_int16 = (full_audio * 32767).astype(np.int16)

    # Écriture WAV
    sf.write(str(OUTPUT_FILE), full_audio_int16, SAMPLE_RATE, subtype="PCM_16")

    print(f"\n  ✓ Fichier généré : {OUTPUT_FILE.name}")
    print(f"  ✓ Durée totale : {time_cursor:.1f}s")
    print(f"  ✓ Format : WAV 16kHz Mono PCM 16-bit")


if __name__ == "__main__":
    main()
