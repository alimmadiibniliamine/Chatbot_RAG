"""
============================================================
 Fichier : backend/models/message.py
 Rôle    : CRUD sur la table `messages`.
           Un message a un rôle 'user' (question) ou
           'assistant' (réponse générée par Ollama).
============================================================
"""

from backend.database.db import get_connection


def add_message(conversation_id: int, role: str, content: str) -> int:
    """Ajoute un message à une conversation."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO messages (conversation_id, role, content) "
        "VALUES (?, ?, ?)",
        (conversation_id, role, content),
    )
    conn.commit()
    mid = cur.lastrowid
    conn.close()
    return mid


def list_messages(conversation_id: int) -> list:
    """Liste tous les messages d'une conversation, dans l'ordre chronologique."""
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM messages "
        "WHERE conversation_id = ? "
        "ORDER BY id ASC",
        (conversation_id,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]