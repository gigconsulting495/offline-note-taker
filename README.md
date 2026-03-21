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

## 📦 Build de l'Application (PyInstaller)

Si vous souhaitez compiler l'application en un exécutable standalone `.app` ou `.dmg` macOS :

```bash
pyinstaller app.spec
```

L'exécutable sera généré dans le sous-dossier `dist/`.

## 📄 Documentation détaillée

Pour plus d'informations sur l'ingénierie du projet, consultez le cahier des charges et les spécifications :

- `PRD reunion.md`
- `Specifications systeme.md`
