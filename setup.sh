#!/bin/bash
# ============================================================================
# setup.sh — Installation automatisée de l'environnement CR Reunion
# ============================================================================
set -e

PYTHON_MIN_VERSION="3.11"
VENV_DIR=".venv"
PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "╔══════════════════════════════════════════════════════════╗"
echo "║   CR Reunion — Setup de l'environnement                 ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""

# ── 1. Vérification de Python ────────────────────────────────────────
echo "▸ Vérification de Python..."
if ! command -v python3 &> /dev/null; then
    echo "✗ Python3 non trouvé. Installez-le via: brew install python@3.11"
    exit 1
fi

PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
echo "  Python $PYTHON_VERSION détecté ✓"

# ── 2. Vérification de ffmpeg ────────────────────────────────────────
echo "▸ Vérification de ffmpeg..."
if ! command -v ffmpeg &> /dev/null; then
    echo "  ffmpeg non trouvé. Installation via Homebrew..."
    if ! command -v brew &> /dev/null; then
        echo "✗ Homebrew non trouvé. Installez-le depuis https://brew.sh"
        exit 1
    fi
    brew install ffmpeg
    echo "  ffmpeg installé ✓"
else
    echo "  ffmpeg détecté ✓"
fi

# ── 3. Création de l'environnement virtuel ───────────────────────────
echo "▸ Création de l'environnement virtuel ($VENV_DIR)..."
if [ ! -d "$PROJECT_DIR/$VENV_DIR" ]; then
    python3 -m venv "$PROJECT_DIR/$VENV_DIR"
    echo "  Environnement virtuel créé ✓"
else
    echo "  Environnement virtuel existant détecté ✓"
fi

# Activation
source "$PROJECT_DIR/$VENV_DIR/bin/activate"
echo "  Environnement activé ✓"

# ── 4. Mise à jour de pip ────────────────────────────────────────────
echo "▸ Mise à jour de pip..."
pip install --upgrade pip --quiet

# ── 5. Installation des dépendances ─────────────────────────────────
echo "▸ Installation des dépendances (cela peut prendre plusieurs minutes)..."
pip install -r "$PROJECT_DIR/requirements.txt" --quiet
echo "  Dépendances installées ✓"

# ── 6. Création des répertoires de données ───────────────────────────
echo "▸ Vérification des répertoires de données..."
# Note : les fichiers temporaires sont dans /tmp/cr_reunion (créé au runtime)
# Les exports finaux sont dans ~/Documents/CR_Reunions/ (créé au runtime)
mkdir -p "$HOME/Documents/CR_Reunions"
echo "  Répertoire d'export ~/Documents/CR_Reunions/ prêt ✓"

# ── 7. Vérification du Token Hugging Face ────────────────────────────
echo "▸ Vérification du Token Hugging Face..."
if [ ! -f "$PROJECT_DIR/.env" ]; then
    echo ""
    echo "  ⚠  Le fichier .env n'existe pas."
    echo "  Pour utiliser Pyannote (diarisation), vous avez besoin d'un"
    echo "  token Hugging Face : https://huggingface.co/settings/tokens"
    echo ""
    read -p "  Entrez votre Token HF (ou appuyez sur Entrée pour passer) : " HF_TOKEN
    if [ -n "$HF_TOKEN" ]; then
        echo "HF_TOKEN=$HF_TOKEN" > "$PROJECT_DIR/.env"
        echo "  Token sauvegardé dans .env ✓"
    else
        echo "HF_TOKEN=" > "$PROJECT_DIR/.env"
        echo "  .env créé sans token (à renseigner plus tard) ⚠"
    fi
else
    echo "  Fichier .env existant détecté ✓"
fi

# ── 8. Vérifications finales ────────────────────────────────────────
echo ""
echo "▸ Vérifications finales..."
echo -n "  MPS (Metal) disponible : "
python3 -c "import torch; print('✓' if torch.backends.mps.is_available() else '✗ (fallback CPU)')"

echo -n "  MLX disponible : "
python3 -c "import mlx.core; print('✓')" 2>/dev/null || echo "✗"

echo ""
echo "╔══════════════════════════════════════════════════════════╗"
echo "║   Setup terminé !                                       ║"
echo "║                                                          ║"
echo "║   Pour activer l'environnement :                         ║"
echo "║   source .venv/bin/activate                              ║"
echo "║                                                          ║"
echo "║   Pour lancer l'application :                            ║"
echo "║   python src/main.py --help                              ║"
echo "╚══════════════════════════════════════════════════════════╝"
