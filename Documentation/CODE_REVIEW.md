# Code Review — Note Taker Offline v2.0

**Date** : 3 avril 2026
**Scope** : Tous les fichiers `src/` + `app.spec` + `requirements.txt`
**Reviewer** : Claude (Opus 4.6)

---

## Verdict global

Le projet est bien structuré pour une app de ~1 260 lignes. La séparation en modules est claire et chaque fichier a une responsabilité unique. Le code est lisible, bien commenté en français, et les choix techniques (mlx-whisper, pyannote, séquentiel pour la RAM) sont pertinents pour la cible MacBook Air M3 16 Go.

**Points forts** : architecture modulaire, gestion mémoire explicite (gc.collect), pipeline séquentiel intelligent, bonne gestion des formats audio.

**Points à améliorer** : stabilité au lancement (le bug "double ouverture"), gestion d'erreurs dans la GUI, thread safety, et quelques fragilités dans le packaging.

---

## 1. BUG CRITIQUE — Stabilité au lancement (double ouverture)

### Diagnostic

Le problème de devoir ouvrir l'app deux fois est très probablement causé par la combinaison de **`argv_emulation=True`** dans `app.spec` (ligne 128) et du comportement de `main.py` (lignes 146-151) :

```python
if __name__ == "__main__":
    if len(sys.argv) == 1:
        from src.gui import launch_gui
        launch_gui()
    else:
        app()
```

**Ce qui se passe** : `argv_emulation=True` sur macOS intercepte les événements Apple (`odoc`, `oapp`) et les injecte dans `sys.argv`. Au premier lancement, macOS envoie un événement d'ouverture qui peut modifier `sys.argv`, faisant croire au code que des arguments CLI sont passés — ce qui lance `app()` (Typer) au lieu de `launch_gui()`. L'app Typer ne fait rien sans sous-commande et se ferme silencieusement.

### Correction recommandée

**Option A (rapide)** — Passer `argv_emulation=False` dans `app.spec` :
```python
exe = EXE(
    ...
    argv_emulation=False,  # ← Changement clé
    ...
)
```

**Option B (robuste)** — Rendre `main.py` plus défensif :
```python
if __name__ == "__main__":
    import sys
    # En mode bundled (.app), toujours lancer la GUI
    if getattr(sys, '_MEIPASS', None):
        from src.gui import launch_gui
        launch_gui()
    elif len(sys.argv) == 1:
        from src.gui import launch_gui
        launch_gui()
    else:
        app()
```

**Recommandation** : Appliquer les DEUX corrections. Option A supprime la source du problème, Option B ajoute une défense en profondeur.

### Facteur aggravant : chargement lourd au démarrage

Le `config.py` est importé au niveau module par `gui.py` (via `from src.config import PROJECT_ROOT`), ce qui déclenche à l'import :
- `load_dotenv()`
- Création de 3 répertoires (`mkdir`)
- Lecture des variables d'environnement

C'est rapide, mais si le `.env` est introuvable en mode bundled ou si la création de `/tmp/cr_reunion` échoue pour une raison quelconque, l'app peut mourir silencieusement (car `console=False` dans le spec).

---

## 2. Thread Safety — GUI & Pipeline

### Problème dans `gui.py`

Le traitement est lancé dans un thread séparé (ligne 274), ce qui est correct. Mais il y a un risque de race condition :

```python
def process_file_thread(self, file_path, lang):
    self.after(500, lambda: self.lbl_proc_status.configure(...))
```

Si l'utilisateur navigue vers une autre vue avant que le `self.after(500, ...)` ne se déclenche, `self.lbl_proc_status` n'existera plus → **crash `TclError`**.

### Correction recommandée

Ajouter un flag de contrôle :
```python
def process_file_thread(self, file_path, lang):
    self._processing = True
    self.after(500, lambda: self._safe_update_status("Analyse audio..."))
    try:
        output_path = run_pipeline(...)
        if self._processing:
            self.after(0, self.show_success_view, output_path)
    except Exception as e:
        if self._processing:
            self.after(0, self.show_error_view, str(e))

def _safe_update_status(self, text):
    if self._processing and hasattr(self, 'lbl_proc_status'):
        try:
            self.lbl_proc_status.configure(text=text)
        except Exception:
            pass
```

---

## 3. Gestion d'erreurs — Points faibles

### 3.1. `diarizer.py` — Token HF en mode bundled

Le `.env` est embarqué dans le bundle (ligne 38 du spec). C'est un **risque de sécurité** si l'app est distribuée : le token HuggingFace serait extractible du `.app`. Pour un usage personnel c'est acceptable, mais à noter.

### 3.2. `pipeline.py` — Pas de try/catch global

Si la diarisation échoue (modèle non téléchargé, pas de réseau pour le premier téléchargement), l'erreur remonte directement en traceback Python. En mode GUI, elle est capturée par `process_file_thread`, mais en mode CLI l'exception brute s'affiche avec tout le stack trace.

### 3.3. `audio_manager.py` — `stop()` sans vérification du stream

```python
def stop(self) -> Path:
    if not self.is_recording:
        raise RuntimeError("Aucun enregistrement en cours.")
```

Si le stream audio a crashé pendant l'enregistrement (débranchement du micro, par ex.), `self.is_recording` est toujours `True`, mais `self._stream` pourrait être dans un état incohérent. Ajouter un try/except autour du `stop()`/`close()` serait plus sûr.

### 3.4. `config.py` — Chemins hardcodés

```python
DATA_DIR = Path("/tmp/cr_reunion")
```

Utiliser `tempfile.mkdtemp()` ou `Path(tempfile.gettempdir()) / "cr_reunion"` serait plus portable (même si l'app cible uniquement macOS aujourd'hui).

---

## 4. Performance — Alignement O(n×m)

Dans `pipeline.py`, `align_segments()` a une complexité O(n × m) où n = segments de transcription et m = segments de diarisation :

```python
for t_seg in transcription_segments:       # n
    for d_seg in diarization_segments:     # m
        ...
```

Pour une réunion de 3h, ça peut représenter des milliers de segments de chaque côté. Ce n'est probablement pas un bottleneck face au temps de diarisation/transcription, mais c'est optimisable avec un tri + balayage linéaire si nécessaire.

---

## 5. Architecture — Points positifs et suggestions

### Ce qui est bien fait

- **Pipeline séquentiel** avec libération mémoire entre chaque étape → intelligent pour 16 Go RAM
- **Séparation claire** : chaque module a une responsabilité unique
- **Post-processing** : la fusion des segments consécutifs du même speaker est bien implémentée
- **Export dual** (JSON + TXT) : le JSON est LLM-ready, le TXT est lisible
- **Dégradation gracieuse** : icônes, logos (try/except pass)
- **Compatibilité pyannote v3/v4** : le check `hasattr(diarization, 'speaker_diarization')` est prévoyant

### Suggestions d'amélioration

**Logging** : Tout passe par `print()`. Remplacer par le module `logging` de Python permettrait de différencier les niveaux (INFO, WARNING, ERROR) et de capturer les logs en fichier — très utile pour diagnostiquer des crashs en mode `.app` où il n'y a pas de console.

**Type hints** : Les fonctions principales ont des type hints (bien), mais les méthodes de `CRReunionApp` dans `gui.py` n'en ont pas (ex: `show_home_view`, `toggle_recording`). Consistance à améliorer.

**Tests** : Aucun test unitaire n'est présent. Les modules `post_processing.py`, `exporter.py`, et `align_segments()` dans `pipeline.py` sont des candidats idéaux pour des tests — ce sont des fonctions pures sans dépendance hardware.

---

## 6. Packaging PyInstaller — Observations

### `app.spec` — Points d'attention

- **`.env` embarqué** (ligne 38) : contient le `HF_TOKEN`. Acceptable pour usage personnel, risqué si distribué.
- **ffmpeg hardcodé** : `'/opt/homebrew/bin/ffmpeg'` — ne marchera pas sur une machine x86 Mac (Intel) où Homebrew est dans `/usr/local/bin/`.
- **`block_cipher = None`** et `cipher=block_cipher` : le cipher PyInstaller est deprecated dans les versions récentes. À supprimer pour nettoyer.
- **`argv_emulation=True`** : Comme discuté, probablement la cause du bug de double ouverture.
- **Version incohérente** : `info_plist` dit `1.0.0` mais la doc mentionne `v2.0.0`.

### `requirements.txt` — Manque `Pillow`

`gui.py` importe `from PIL import Image as PILImage, ImageTk` mais `Pillow` n'est pas dans les requirements. Ça fonctionne parce que c'est une dépendance transitive, mais ça devrait être explicite.

---

## 7. Résumé des priorités

| Priorité | Issue | Fichier | Effort |
|----------|-------|---------|--------|
| **P0** | Bug double ouverture (`argv_emulation` + détection `_MEIPASS`) | `app.spec` + `main.py` | 15 min |
| **P1** | Thread safety dans la GUI (TclError potentiel) | `gui.py` | 30 min |
| **P1** | Remplacer `print()` par `logging` (diagnostic des crashs) | Tous les `src/` | 1h |
| **P2** | Ajouter Pillow aux requirements explicites | `requirements.txt` | 2 min |
| **P2** | Version incohérente dans `info_plist` | `app.spec` | 2 min |
| **P2** | Try/except autour de `stream.stop()` / `stream.close()` | `audio_manager.py` | 10 min |
| **P3** | Ajouter des tests unitaires (post_processing, exporter, align) | Nouveau `tests/` | 2-3h |
| **P3** | Optimiser `align_segments` en O(n+m) | `pipeline.py` | 30 min |
| **P3** | Rendre ffmpeg path dynamique dans le spec | `app.spec` | 15 min |

---

## 8. Skills Antigravity recommandées

Pour compléter cette revue et intégrer des revues automatiques dans ton workflow Antigravity, voici les skills du repo `sickn33/antigravity-awesome-skills` les plus pertinentes :

- **`architect-review`** — Pour valider l'architecture globale et les patterns
- **`code-review`** — Pour des revues de code PR par PR
- **`debug`** (si disponible) — Pour investiguer le bug de stabilité avec plus de contexte runtime

Installation :
```bash
npx antigravity-awesome-skills --antigravity
```

Cela installera les skills dans ton workspace Antigravity, utilisables ensuite comme commandes slash dans l'IDE.
