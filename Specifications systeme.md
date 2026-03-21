# Spécifications Système — MacBook Air (Machine Cible)

## Informations Matérielles

| Spécification | Valeur |
| :--- | :--- |
| **Modèle** | MacBook Air (13 pouces, M3, 2024) |
| **Processeur (Puce)** | Apple M3 (8 cœurs CPU, 10 cœurs GPU, 16 cœurs Neural Engine) |
| **Mémoire (RAM)** | 16 Go (RAM unifiée partagée CPU/GPU) |
| **Numéro de série** | `CRFXQMWVK1` |

## Informations Logicielles

| Spécification | Valeur |
| :--- | :--- |
| **Système d'exploitation** | macOS 26.3.1 (Build 25D2128) |
| **Python** | 3.14.x (via Homebrew) |
| **Architecture** | arm64 (Apple Silicon natif) |

## Capacités IA Exploitées

| Capacité | Utilisation dans l'application |
| :--- | :--- |
| **MLX (GPU/Neural Engine)** | Transcription via `mlx-whisper` (modèle large-v3, quantifié 4-bit) |
| **MPS (Metal Performance Shaders)** | Diarisation via `pyannote.audio` |
| **RAM Unifiée** | Pipeline séquentiel pour maintenir l'usage < 6 Go |

## Contraintes Identifiées

- **RAM unifiée :** La RAM est partagée entre CPU et GPU. Le pipeline **doit** être séquentiel avec libération mémoire explicite (`gc.collect()`, `torch.mps.empty_cache()`) entre chaque étape pour éviter les saturations.
- **PyInstaller + MLX :** Les fichiers `.metallib` (shaders GPU Metal) ne sont pas détectés automatiquement par PyInstaller. Ils doivent être inclus manuellement via `collect_data_files('mlx')`.
- **PyInstaller + Pyannote :** Les fichiers YAML de configuration de Pyannote et la bibliothèque `torchcodec` (décodeur audio interne) doivent être bundlés explicitement.
- **PyInstaller + ffmpeg :** Le binaire `ffmpeg` est appelé en subprocess par `pydub`. En mode bundled, le dossier `_MEIPASS` contenant `ffmpeg` doit être ajouté au `PATH` système pour que les subprocesses le trouvent.
- **Modèles IA :** Les modèles Whisper (~1.5 Go) et Pyannote (~600 Mo) sont téléchargés depuis Hugging Face au premier lancement et mis en cache dans `~/.cache/huggingface/hub/`. Connexion internet requise uniquement au premier lancement.

---

> **Note :** Ce document sert de référence pour les contraintes matérielles et logicielles de la machine cible. Ces spécifications influencent directement les choix techniques du projet (pipeline séquentiel, quantification 4-bit, libération mémoire explicite).
