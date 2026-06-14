"""
============================================================
 Fichier : backend/models/conversation.py
 Rôle    : CRUD sur la table `conversations`.
           Toutes les fonctions filtrent par user_id pour
           garantir qu'un utilisateur ne voit QUE SES
           PROPRES conversations.
============================================================
"""

from backend.database.db import get_connection


def create_conversation(user_id: int, title: str = "Nouvelle conversation") -> int:
    """Crée une conversation vide pour un utilisateur."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO conversations (user_id, title) VALUES (?, ?)",
        (user_id, title),
    )
    conn.commit()
    cid = cur.lastrowid
    conn.close()
    return cid


def list_conversations(user_id: int) -> list:
    """Liste les conversations d'un utilisateur (les plus récentes en premier)."""
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM conversations "
        "WHERE user_id = ? "
        "ORDER BY updated_at DESC",
        (user_id,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_conversation(conv_id: int, user_id: int):
    """Récupère UNE conversation, en s'assurant qu'elle appartient à user_id."""
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM conversations WHERE id = ? AND user_id = ?",
        (conv_id, user_id),
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def rename_conversation(conv_id: int, user_id: int, new_title: str) -> None:
    """Renomme une conversation (et met à jour `updated_at`)."""
    conn = get_connection()
    conn.execute(
        "UPDATE conversations "
        "SET title = ?, updated_at = CURRENT_TIMESTAMP "
        "WHERE id = ? AND user_id = ?",
        (new_title, conv_id, user_id),
    )
    conn.commit()
    conn.close()


def delete_conversation(conv_id: int, user_id: int) -> None:
    """Supprime une conversation. Les messages sont supprimés en cascade."""
    conn = get_connection()
    conn.execute(
        "DELETE FROM conversations WHERE id = ? AND user_id = ?",
        (conv_id, user_id),
    )
    conn.commit()
    conn.close()


def touch_conversation(conv_id: int) -> None:
    """Met à jour `updated_at` à maintenant (utile après un nouvel échange)."""
    conn = get_connection()
    conn.execute(
        "UPDATE conversations SET updated_at = CURRENT_TIMESTAMP WHERE id = ?",
        (conv_id,),
    )
    conn.commit()
    conn.close()