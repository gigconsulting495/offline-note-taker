# PRD (v3.1) : Note Taker Offline — Transcription & Diarisation 100% Locale

- **Référence :** v3.1
- **Date :** 2026-04-03
- **Nom de l'application :** Note Taker Offline (anciennement « CR Reunion »)
- **Branding :** *Awesome Offline Note Taker by GiG Consulting*

---

## 1. Vision du Projet

Application macOS native (Python + CustomTkinter) permettant l'enregistrement et le traitement de réunions de longue durée (jusqu'à 3h), avec identification automatique des interlocuteurs, le tout fonctionnant **100% en local** et optimisé pour **Apple Silicon (M1/M2/M3)**.

L'application est distribuée sous forme d'installeur `.dmg` prêt à l'emploi (glisser-déposer vers `Applications`), sans nécessité d'installer Python ni aucune dépendance.

---

## 2. Objectifs Techniques

| Objectif | Solution |
| :--- | :--- |
| **Performance** | Framework **MLX** pour la transcription (GPU/Neural Engine Apple Silicon) |
| **Précision** | **Pyannote 3.1** pour la diarisation avec support **MPS** (Metal Performance Shaders) |
| **Robustesse** | Pipeline strictement séquentiel pour ne pas saturer la RAM unifiée |
| **Confidentialité** | Zéro appel API externe après l'installation initiale des modèles |
| **Distribution** | Application standalone `.app` via PyInstaller, installeur `.dmg` via `create-dmg` |

---

## 3. Spécifications Fonctionnelles

### F1 : Gestion de l'Audio (Enregistrement & Import)

- **Format d'entrée interne :** WAV 16kHz, Mono, PCM 16-bit.
- **Import :** Conversion automatique des formats audio déposés (MP3, M4A, OGG, FLAC, WMA, AAC) vers le format interne, via `pydub` / `ffmpeg`.
- **Contrôles d'enregistrement :** Démarrer, Pause, Reprendre, Terminer.
- **Sécurité :** Écriture par blocs (chunks de 5 secondes) pour éviter la corruption en cas d'arrêt brutal.

### F2 : Moteur de Diarisation (Speaker ID)

- **Modèle :** `pyannote/speaker-diarization-3.1`.
- **Paramètres :** Détection **automatique** native du nombre de locuteurs (pas de bornes strictes requises).
- **Sortie :** Segments temporels associés à des IDs anonymes (`SPEAKER_00`, `SPEAKER_01`, etc.).
- **Accélération :** MPS (Metal) si disponible, sinon fallback CPU.

### F3 : Moteur de Transcription (ASR)

- **Moteur :** `mlx-whisper` (optimisé Apple Silicon, GPU/ANE).
- **Modèle :** `large-v3` (version quantifiée 4-bit via `mlx-community/whisper-large-v3-mlx`).
  - *Empreinte mémoire < 1.5 Go, précision multilingue préservée.*
- **Langues :** Détection **automatique** par défaut. Possibilité de forcer manuellement (`fr`, `en`).
- **Important :** Tâche forcée à `task="transcribe"` pour éviter toute traduction fantôme vers l'anglais.

### F4 : Post-Processing Intelligent

- Filtrage automatique des mots d'hésitation isolés et des bruits.
- Fusion des segments consécutifs d'un même locuteur si la pause est inférieure à 2 secondes.
- Nettoyage du texte (espaces multiples, majuscules initiales).

### F5 : Export de Données

- **Double format :**
  - `transcript.json` : Fichier structuré avec métadonnées (idéal pour injection LLM).
  - `transcript.txt` : Fichier texte lisible (`[HH:MM:SS - HH:MM:SS] Speaker : Texte`).
- **Stockage centralisé :** Sous-dossier horodaté par réunion (`YYYY-MM-DD_HHhMM_Nom`) dans `~/Documents/CR_Reunions/`.
- **Conservation de l'audio :** Le fichier `.wav` de travail est déplacé dans le dossier de la réunion → triptyque complet (TXT, JSON, WAV).

### F6 : Interface Graphique (GUI)

- Framework : `CustomTkinter` (thème sombre, look natif macOS).
- Parcours utilisateur linéaire : **Accueil → Enregistrement → Fichier Prêt → Traitement → Succès**.
- Barre de progression indéterminée pendant le traitement.
- Ouverture automatique du Finder à la fin du traitement.
- Logos personnalisés GiG Consulting intégrés (accueil + icône Dock).

---

## 4. Architecture Logicielle

### Arborescence du projet

```text
CR reunion/
├── Documentation/
│   ├── Manuel_Technique.md  # Architecture, Design Decisions, Core Components
│   └── CODE_REVIEW.md       # Audit de code
├── src/
│   ├── main.py              # Point d'entrée (GUI si aucun arg, CLI sinon)
│   ├── config.py            # Configuration centralisée + détection PyInstaller
│   ├── gui.py               # Interface graphique CustomTkinter
│   ├── pipeline.py          # Orchestrateur séquentiel du traitement
│   ├── audio_manager.py     # Enregistrement micro + conversion audio
│   ├── diarizer.py          # Identification des locuteurs (Pyannote)
│   ├── transcriber.py       # Transcription audio (mlx-whisper)
│   ├── exporter.py          # Export JSON + TXT
│   └── post_processing.py   # Fusion, filtrage, nettoyage du transcript
├── assets/
│   ├── logos/                # logo_gi_green_icon.png, logo_gi_gold.png, logo_gig_consulting.png
│   └── AppIcon.icns          # Icône macOS native (toutes résolutions)
├── app.spec                  # Configuration PyInstaller
├── build_dmg.sh              # Script de création du .dmg
├── requirements.txt          # Dépendances Python
├── setup.sh                  # Installation automatisée de l'environnement dev
├── run.sh                    # Lancement rapide en mode développement
└── .env                      # Token Hugging Face (HF_TOKEN)
```

### Table des composants

| Composant | Technologie | Rôle |
| :--- | :--- | :--- |
| **Interface** | `CustomTkinter` (GUI) & `Typer` (CLI) | Interaction utilisateur (thème sombre, vues en étapes) |
| **Audio I/O** | `sounddevice`, `soundfile`, `pydub` & `ffmpeg` | Capture micro, conversion de formats |
| **Inférence ASR** | `mlx-whisper` | Transcription accélérée via GPU/ANE (modèle 4-bit) |
| **Diarisation** | `pyannote.audio` | Segmentation des locuteurs via MPS |
| **Orchestrateur** | `pipeline.py` | Exécution séquentielle (Conversion → Diarisation → Transcription → Alignement → Post-processing → Export) |
| **Packaging** | `PyInstaller` + `create-dmg` | Application standalone `.app` et installeur `.dmg` |

---

## 5. Contraintes de Performance (Cibles M3 / 16 Go)

- **Transcription :** Ratio ≤ 0.05x grâce à la version quantifiée 4-bit.
- **Diarisation :** Ratio < 0.15x.
- **Consommation RAM :** Garantie < 6 Go au pic (pipeline séquentiel + libération mémoire entre étapes).

---

## 6. Packaging & Distribution (Phase 6)

### 6.1 Stratégie de bundling

L'application est empaquetée via **PyInstaller** en mode `onedir` (un répertoire contenant l'exécutable et toutes les dépendances), puis enveloppée dans un `.app` macOS.

**Éléments bundlés dans le `.app` :**

| Élément | Raison |
| :--- | :--- |
| `ffmpeg` binaire | Conversion audio via `pydub` (subprocess) |
| `customtkinter` (dossier complet) | Contient les thèmes JSON/assets requis au runtime |
| `pyannote` (dossier complet) | Fichiers YAML de configuration (ex: `telemetry/config.yaml`) |
| `lightning`, `pytorch_lightning` | Dépendances runtime de Pyannote |
| `torchcodec` (dossier + libs) | Décodeur audio utilisé en interne par Pyannote (`AudioDecoder`) |
| `mlx` (data files) | Fichiers `.metallib` (shaders Metal pour GPU Apple Silicon) |
| `.env` | Token Hugging Face |
| `assets/logos/` | Logos de l'application |

### 6.2 Adaptations du code pour le mode bundled

Le fichier `config.py` détecte si l'application tourne dans un bundle PyInstaller via `sys._MEIPASS` :

- **`PROJECT_ROOT`** pointe vers `_MEIPASS` (dossier temporaire d'extraction) au lieu du dossier du projet.
- **`PATH` système** est enrichi avec `_MEIPASS` pour que `pydub` trouve `ffmpeg` en subprocess.
- **`.env`** est chargé depuis le bundle ou depuis `~/.env` en fallback.

### 6.3 Modèles d'IA — stratégie de cache

Les modèles (mlx-whisper, pyannote) **ne sont pas** inclus dans le `.app` :

- Ils sont téléchargés automatiquement depuis Hugging Face au premier lancement.
- Ils sont mis en cache dans `~/.cache/huggingface/hub/` (~2-3 Go).
- Cela maintient le `.dmg` à une taille raisonnable (~290 Mo).

### 6.4 Pièges PyInstaller identifiés et résolus

| Problème rencontré | Cause | Solution |
| :--- | :--- | :--- |
| `No module named 'mlx._reprlib_fix'` | PyInstaller ne détecte pas les sous-modules internes de `mlx` | `collect_submodules('mlx')` dans le spec |
| `Failed to load the default metallib` | Fichiers `.metallib` (shaders GPU Metal) non inclus | `collect_data_files('mlx')` dans le spec |
| `name 'AudioDecoder' is not defined` | `torchcodec` non bundlé (dépendance indirecte de Pyannote) | Ajout explicite de `torchcodec` (dossier + submodules + data) |
| `No such file or directory: 'ffmpeg'` | `pydub` appelle `ffmpeg` via subprocess, mais `_MEIPASS` n'est pas dans le `PATH` | `os.environ["PATH"] = sys._MEIPASS + ...` dans `config.py` |
| CustomTkinter blanc/cassé | Thèmes JSON et assets manquants | Inclusion du dossier `customtkinter` complet |

### 6.5 Commandes de build

```bash
# 1. Compiler l'application
.venv/bin/pyinstaller app.spec --noconfirm

# 2. Créer l'installeur DMG
bash build_dmg.sh
```

**Résultat :**

- `dist/Note Taker Offline.app` (~750 Mo)
- `Note Taker Offline.dmg` (~290 Mo, compression 68%)

---

## 7. Prérequis Système

- **Matériel :** Mac avec puce Apple Silicon (M1/M2/M3/M4).
- **OS :** macOS 13+ (Ventura ou supérieur).
- **RAM :** 16 Go recommandés.
- **Stockage :** ~3 Go au total (application + cache modèles après premier lancement).
- **Réseau :** Requis uniquement au premier lancement (téléchargement des modèles). Entièrement offline ensuite.
- **Token Hugging Face :** Requis pour pyannote. À obtenir sur <https://huggingface.co/settings/tokens> et accepter les conditions d'utilisation du modèle `pyannote/speaker-diarization-3.1`.

---

## 8. Roadmap d'Implémentation

1. **Phase 1 (Setup) : ✅** Configuration de l'environnement, installation des dépendances, gestion du `.env`.
2. **Phase 2 (Audio & Recorder) : ✅** Enregistrement micro, conversion de formats.
3. **Phase 3 (Diarization) : ✅** Identification des voix avec détection automatique du nombre de locuteurs.
4. **Phase 4 (Transcription) : ✅** `mlx-whisper` avec auto-détection de la langue.
5. **Phase 5 (Pipeline & UI) : ✅** Orchestrateur séquentiel, interface graphique CustomTkinter.
6. **Phase 6 (Déploiement) : ✅** Application standalone `Note Taker Offline.app` via PyInstaller, installeur `.dmg` via `create-dmg`.
