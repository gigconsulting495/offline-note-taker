# Note Taker Offline 🎙️

Application macOS 100% hors-ligne permettant d'enregistrer, de transcrire et de diariser (identifier qui parle) des réunions en toute confidentialité.

## ✨ Fonctionnalités

- **Confidentialité totale** : Tout est traité localement sur votre Mac. Aucune donnée vocale n'est traitée dans le Cloud.
- **Transcription sur Apple Silicon** : Utilise le modèle **Whisper Large-v3** (optimisé pour processeurs M1/M2/M3 via le framework MLX d'Apple).
- **Diarisation automatique** : Reconnaissance et séparation des différents interlocuteurs via **Pyannote 3.1**.
- **Interface graphique prête à l'emploi** : Application packagée simple d'utilisation, basée sur CustomTkinter.
- **Exports structurés** : Génération dynamique des transcriptions en fichiers `TXT` lisibles et en `JSON` structurés.

## 🚀 Installation locale (Développement)

### Prérequis

- Mac avec puce Apple Silicon (M1/M2/M3/M4)
- Python 3.10+
- `ffmpeg` installé sur le système (`brew install ffmpeg`)
- Un token Hugging Face valide (avec les accès acceptés pour Pyannote)

### Configuration

1. Clonez le dépôt GitHub :

   ```bash
   git clone https://github.com/gigconsulting495/offline-note-taker.git
   cd offline-note-taker
   ```

2. Créez un environnement virtuel et installez les dépendances :

   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

3. Créez un fichier `.env` à la racine et ajoutez votre token HuggingFace :

   ```env
   HF_TOKEN=votre_huggingface_token_ici
   ```

4. Lancez l'application :

   ```bash
   python src/main.py
   ```

*Notes techniques : Lors du tout premier lancement, l'application aura besoin d'une connexion internet pour télécharger discrètement les modèles IA (~ 4.5 Go) dans le cache de l'ordinateur. Elle fonctionnera ensuite de manière 100% hors-ligne.*

## 📦 Build de l'Application (macOS)

L'application est distribuée pour macOS sous forme d'image disque (.dmg) 100% encapsulée. Pour compiler l'application :

1. Construire l'exécutable avec PyInstaller :
```bash
pyinstaller app.spec --clean --noconfirm
```

2. Créer l'installeur `.dmg` macOS :
```bash
bash build_dmg.sh
```

L'exécutable sera généré dans `dist/` et le `.dmg` à la racine du projet.

## 📄 Documentation détaillée

Pour une compréhension totale de l'architecture logicielle, de nos choix d'infrastructures et des résolutions de bugs liés à Apple Silicon et macOS, notre Manuel Technique (100+ pages) généré par l'agent @docs-architect est disponible.

Consultez ces documents dans le sous-dossier `Documentation/` (ouverts dans n'importe quel éditeur, schémas Mermaid inclus) :

- [Manuel_Technique.md](Documentation/Manuel_Technique.md) : L'encyclopédie du projet.
- [CODE_REVIEW.md](Documentation/CODE_REVIEW.md) : Audit complet de la base de code Python.

La définition officielle des besoins (PRD) reste disponible à l'adresse :
- `PRD reunion.md`
