"""
============================================================
 Fichier      : backend/config.py
 Rôle         : Configuration centralisée du projet.
                Toutes les valeurs sensibles ou ajustables sont
                ici, chargées depuis les variables d'environnement
                ou un fichier .env à la racine.
 Avantage     : modifier la configuration ne nécessite AUCUNE
                modification du code source.
============================================================
"""

import os
from dotenv import load_dotenv

# Charge automatiquement le fichier .env (s'il existe) dans les
# variables d'environnement du processus Python.
load_dotenv()

# Chemin racine du projet (le dossier qui contient backend/, frontend/, etc.)
BASE_DIR = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))


class Config:
    """Classe de configuration utilisée par Flask et le pipeline RAG."""

    # -------- Flask --------
    # Clé utilisée par Flask en interne (sessions, signatures, etc.)
    SECRET_KEY = os.getenv("SECRET_KEY", "change-me-in-production")

    # -------- JWT (authentification) --------
    JWT_SECRET = os.getenv("JWT_SECRET", "change-me-jwt")
    JWT_EXPIRATION_HOURS = 24   # Durée de validité du token : 24h

    # -------- Stockage --------
    DATABASE_PATH = os.path.join(BASE_DIR, "database.db")    # SQLite
    UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")        # Documents uploadés
    CHROMA_DIR    = os.path.join(BASE_DIR, "chroma_db")      # Base vectorielle
    DATA_DIR      = os.path.join(BASE_DIR, "data")           # Données optionnelles

    # -------- Ollama (LLM local) --------
    # Modèle à utiliser : mistral / llama3 / phi3
    # Mistral  cloud est un bon compromis : 4 Go, rapide, multilingue.
    OLLAMA_MODEL    = os.getenv("OLLAMA_MODEL", "minimax-m2.5:cloud")
    OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

    # -------- Embeddings (HuggingFace local) --------
    # paraphrase-multilingual-MiniLM-L12-v2 : très petit (80 Mo), rapide, multilingue acceptable.
    EMBEDDING_MODEL = os.getenv(
        "EMBEDDING_MODEL",
        "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
    )

    # -------- Paramètres RAG --------
    CHUNK_SIZE    = 800   # Taille d'un chunk en caractères
    CHUNK_OVERLAP = 150   # Chevauchement entre chunks (préserve le contexte)
    TOP_K         = 6    # Nombre de chunks récupérés par requête

    # -------- Admin par défaut --------
    # Créé automatiquement au premier démarrage.
    DEFAULT_ADMIN_EMAIL    = os.getenv("DEFAULT_ADMIN_EMAIL", "[email protected]")
    DEFAULT_ADMIN_PASSWORD = os.getenv("DEFAULT_ADMIN_PASSWORD", "admin123")


# ------------------------------------------------------------
# Création automatique des dossiers nécessaires au démarrage.
# Évite les erreurs "dossier introuvable" lors du premier run.
# ------------------------------------------------------------
for directory in [Config.UPLOAD_FOLDER, Config.CHROMA_DIR, Config.DATA_DIR]:
    os.makedirs(directory, exist_ok=True)