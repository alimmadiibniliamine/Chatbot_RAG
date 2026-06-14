"""
============================================================
 Fichier : backend/database/db.py
 Rôle    : Fournir une connexion SQLite simple, thread-safe
           pour Flask. Chaque requête HTTP ouvre sa propre
           connexion (pattern recommandé pour SQLite + Flask).
============================================================
"""

import sqlite3
from backend.config import Config


def get_connection() -> sqlite3.Connection:
    """
    Ouvre une nouvelle connexion à la base SQLite.

    - `row_factory = sqlite3.Row` permet d'accéder aux colonnes
      par leur nom (ex: row["email"]) plutôt que par index.
    - `PRAGMA foreign_keys = ON` active les clés étrangères
      (désactivées par défaut dans SQLite).
    """
    conn = sqlite3.connect(Config.DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn