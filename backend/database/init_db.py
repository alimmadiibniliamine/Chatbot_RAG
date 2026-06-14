"""
============================================================
 Fichier : backend/database/init_db.py
 Rôle    : Créer le schéma SQLite et un administrateur
           par défaut au tout premier démarrage du backend.

 Tables créées :
   - users         : comptes utilisateurs (admin / user)
   - conversations : conversations (1 utilisateur = N conversations)
   - messages      : messages (1 conversation = N messages)
   - documents    : documents uploadés par l'admin
============================================================
"""

from backend.database.db import get_connection
from backend.auth.auth_utils import hash_password
from backend.config import Config


# SQL exécuté UNE SEULE FOIS (les "IF NOT EXISTS" empêchent
# les erreurs lors des redémarrages suivants).
SCHEMA_SQL = """
-- Table des utilisateurs
CREATE TABLE IF NOT EXISTS users (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    email         TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role          TEXT NOT NULL CHECK(role IN ('admin','user')) DEFAULT 'user',
    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table des conversations
CREATE TABLE IF NOT EXISTS conversations (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id    INTEGER NOT NULL,
    title      TEXT NOT NULL DEFAULT 'Nouvelle conversation',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Table des messages (échanges utilisateur/assistant)
CREATE TABLE IF NOT EXISTS messages (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    conversation_id INTEGER NOT NULL,
    role            TEXT NOT NULL CHECK(role IN ('user','assistant')),
    content         TEXT NOT NULL,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(conversation_id) REFERENCES conversations(id) ON DELETE CASCADE
);

-- Table des documents indexés
CREATE TABLE IF NOT EXISTS documents (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    filename    TEXT NOT NULL,
    filepath    TEXT NOT NULL,
    indexed     INTEGER NOT NULL DEFAULT 0,  -- 1 = indexé dans ChromaDB
    uploaded_by INTEGER,
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(uploaded_by) REFERENCES users(id) ON DELETE SET NULL
);
"""


def init_db() -> None:
    """
    Crée les tables si elles n'existent pas, puis crée
    l'administrateur par défaut s'il n'existe pas encore.
    """
    conn = get_connection()
    cursor = conn.cursor()

    # 1) Création des tables
    cursor.executescript(SCHEMA_SQL)

    # 2) Création de l'admin par défaut (s'il n'existe pas déjà)
    cursor.execute(
        "SELECT id FROM users WHERE email = ?",
        (Config.DEFAULT_ADMIN_EMAIL,),
    )
    if cursor.fetchone() is None:
        cursor.execute(
            "INSERT INTO users (email, password_hash, role) "
            "VALUES (?, ?, 'admin')",
            (
                Config.DEFAULT_ADMIN_EMAIL,
                hash_password(Config.DEFAULT_ADMIN_PASSWORD),
            ),
        )
        print(f"[init_db] Admin par défaut créé : {Config.DEFAULT_ADMIN_EMAIL}")

    conn.commit()
    conn.close()
    print("[init_db] Base de données initialisée avec succès.")