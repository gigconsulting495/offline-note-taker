# Tâches — Note Taker Offline

## Phases accomplies

- [x] **Phase 1 (Setup)** : Environnement virtuel, dépendances, gestion `.env` pour le token HF.
- [x] **Phase 2 (Audio & Recorder)** : Enregistrement micro (`sounddevice`), conversion de formats (`pydub`/`ffmpeg`).
- [x] **Phase 3 (Diarisation)** : Pyannote 3.1, détection automatique des locuteurs, accélération MPS.
- [x] **Phase 4 (Transcription)** : `mlx-whisper` (large-v3, 4-bit), auto-détection de la langue, forçage `task="transcribe"`.
- [x] **Phase 5 (Pipeline & UI)** : Orchestrateur séquentiel, GUI CustomTkinter (thème sombre, vues par étapes), post-processing intelligent, double export JSON/TXT.
- [x] **Phase 6 (Déploiement)** : Application standalone `.app` via PyInstaller, installeur `.dmg` via `create-dmg`.
  - [x] Création de l'icône macOS `.icns`
  - [x] Adaptation de `config.py` et `gui.py` pour le mode bundled (`sys._MEIPASS`)
  - [x] Résolution des dépendances cachées (MLX metallib, torchcodec, pyannote YAML, ffmpeg PATH)
  - [x] Intégration des logos GiG Consulting
  - [x] Build et tests de l'application standalone
  - [x] Création du DMG avec drag & drop vers Applications

## Tâches restantes / Améliorations futures

- [ ] Support de la vidéo (extraction automatique de la piste audio).
- [ ] Renommage des locuteurs dans l'interface graphique.
- [ ] Glisser-déposer de fichiers audio directement sur la fenêtre (via `tkinterdnd2`).
- [ ] Stabilisation de l'application et préparation pour des tests M1/M2 si distribution élargie.
