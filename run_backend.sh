#!/usr/bin/env bash
# ============================================================
# Lance le backend Flask en mode développement.
# Active automatiquement l'environnement virtuel s'il existe.
# ============================================================
[ -d "venv" ] && source venv/bin/activate
python -m backend.app