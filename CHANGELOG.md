<!-- markdownlint-disable MD024 MD032 MD022 -->
# Changelog

Toutes les modifications notables de ce projet seront documentées dans ce fichier.

Le format est basé sur [Keep a Changelog](https://keepachangelog.com/fr/1.1.0/),
et ce projet adhère au [Versionnage Sémantique](https://semver.org/lang/fr/).

---

## [Unreleased]

- Support optionnel de la vidéo (extraction de la piste audio).
- Renommage du locuteur par l'utilisateur dans l'interface.

---

## [2.1.0] - 2026-04-03

### Added

- **Documentation Technique** : Création du dossier `Documentation/` contenant un Manuel d'Architecture exhaustif (`Manuel_Technique.md`) généré par workflow docs-architect et la revue de code (`CODE_REVIEW.md`).

### Changed

- **Build macOS** : Sécurisation du build final via flag `--clean` et automatisation de l'éjection de volume pour le script `build_dmg.sh`.
- **Multiprocessing macOS** : Renforcement des verrous anti-spawn infinis causés par Pytorch dans `main.py` suite aux recommandations d'audit de l'architecture.

---

## [2.0.0] - 2026-03-21

### Added

- **Application standalone macOS** : Empaquetage complet via PyInstaller, produisant `Note Taker Offline.app`.
- **Installeur DMG** : Création d'un `.dmg` (~290 Mo) avec glisser-déposer vers le dossier Applications, via `create-dmg`.
- **Script `build_dmg.sh`** : Automatisation de la création du DMG.
- **Fichier `app.spec`** : Configuration complète de PyInstaller avec gestion des hidden imports, data files, et binaires bundlés.
- **Icône macOS native** : `assets/AppIcon.icns` générée depuis le logo du projet (toutes résolutions).
- **Logos personnalisés** : Intégration des logos GiG Consulting dans l'interface (accueil, barre de titre, icône Dock).
- **Détection du mode bundled** : `config.py` détecte `sys._MEIPASS` et ajuste `PROJECT_ROOT`, `PATH`, et le chargement du `.env`.

### Changed

- **Nom de l'application** : Renommé de « CR Reunion » à « Note Taker Offline ».
- **Titre de fenêtre** : « Awesome Offline Note Taker by GiG Consulting ».
- **Résolution des chemins d'assets** : `gui.py` utilise `config.PROJECT_ROOT` au lieu de `__file__` pour la compatibilité PyInstaller.

### Fixed

- **`ffmpeg` introuvable en mode bundled** : Ajout de `sys._MEIPASS` au `PATH` système dans `config.py`.
- **`mlx._reprlib_fix` manquant** : Résolu via `collect_submodules('mlx')` dans `app.spec`.
- **`.metallib` (shaders Metal) absents** : Résolu via `collect_data_files('mlx')` dans `app.spec`.
- **`AudioDecoder` non défini** : `torchcodec` ajouté explicitement au bundle (submodules + data files).
- **CustomTkinter cassé** : Inclusion du dossier complet `customtkinter` avec ses thèmes JSON.
- **Pyannote `config.yaml` manquant** : Inclusion du dossier complet `pyannote` dans le bundle.

---

## [1.2.1] - 2026-03-21

### Fixed

- **Restauration de l'Interface UI/UX** : Annulation de la refonte « Apple Philosophy » (v1.2.0) suite à des problèmes de stabilité. Restauration du système de vues par étapes, stable et fonctionnel.

---

## [1.2.0] - 2026-03-21

### Changed

- **Refonte UI/UX « Apple Philosophy »** : Abandon du système d'onglets pour un parcours linéaire par étapes (Accueil, Enregistrement, Lancement IA, Traitement, Succès).
- **Visualisations** : Remplacement des pop-ups bloquants par une barre de chargement intégrée.
- **Ergonomie** : Ouverture automatique du Finder à l'emplacement du rendu final.

---

## [1.1.0] - 2026-03-20

### Added

- **Post-processing intelligent** : Fusion des segments consécutifs par locuteur avec tolérance de silence et filtrage des mots parasites.
- **Dossier d'export centralisé** : Sous-dossier unique par réunion dans `~/Documents/CR_Reunions`.
- **Double format d'export** : `transcript.json` (format LLM) et `transcript.txt` (format humain).
- **Conservation de l'audio final** : Déplacement du `.wav` dans le dossier d'export.

### Fixed

- **Traductions fantômes Whisper** : Forçage de `task="transcribe"` pour empêcher l'anglicisation des sources françaises.

### Changed

- **Modèle Whisper** : Remplacement de `distil-large-v3` (anglophone uniquement) par `large-v3` (multilingue complet).
- **Stockage temporaire** : Fichiers audio de transit déplacés vers `/tmp/cr_reunion`.

---

## [1.0.0] - 2026-03-20

### Added

- **Interface Graphique (GUI)** complète en `customtkinter` (sélection de fichiers, enregistrement en direct, logs).
- **Détection automatique de la langue** : Whisper transcrit dans la langue originale (option « Auto »).
- **Détection automatique du nombre de locuteurs** : Pyannote analyse dynamiquement sans bornes min/max.
- Pipeline 100% fonctionnel et optimisé Apple Silicon (MPS pour Pyannote, MLX pour Whisper).
- Scripts de lancement `run.sh` et CLI robuste avec `Typer`.

---

## [0.1.0] - 2026-03-19

### Added

- Création du PRD reunion.md (v2.0 → v2.1).
- Création des Spécifications systeme.md.
- Création du CHANGELOG.md.
- Analyse de faisabilité validée.
- Plan d'implémentation détaillé rédigé.
