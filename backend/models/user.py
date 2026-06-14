"""
============================================================
 Fichier : backend/models/user.py
 Rôle    : Opérations CRUD sur la table `users`.
           On expose des fonctions simples (pas de classe ORM)
           car SQLite reste très lisible avec du SQL pur.
============================================================
"""

from backend.database.db import get_connection


def create_user(email: str, password_hash: str, role: str = "user") -> int:
    """Insère un nouvel utilisateur et retourne son id."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO users (email, password_hash, role) VALUES (?, ?, ?)",
        (email, password_hash, role),
    )
    conn.commit()
    new_id = cursor.lastrowid
    conn.close()
    return new_id


def get_user_by_email(email: str):
    """Retourne un utilisateur par email, ou None."""
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM users WHERE email = ?", (email,)
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def get_user_by_id(user_id: int):
    """Retourne un utilisateur par id, ou None."""
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM users WHERE id = ?", (user_id,)
    ).fetchone()
    conn.close()
    return dict(row) if row else None