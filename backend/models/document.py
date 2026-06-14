"""
============================================================
 Fichier : backend/models/document.py
 Rôle    : CRUD sur la table `documents`.
           Garde la trace des fichiers PDF/TXT uploadés par
           l'administrateur et de leur statut d'indexation.
============================================================
"""

from backend.database.db import get_connection


def add_document(filename: str, filepath: str, uploaded_by: int) -> int:
    """Enregistre un document dans la base."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO documents (filename, filepath, uploaded_by, indexed) "
        "VALUES (?, ?, ?, 1)",
        (filename, filepath, uploaded_by),
    )
    conn.commit()
    doc_id = cur.lastrowid
    conn.close()
    return doc_id


def list_documents() -> list:
    """Liste tous les documents (les plus récents en premier)."""
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM documents ORDER BY created_at DESC"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def delete_document(doc_id: int):
    """Supprime un document de la base et retourne ses infos (pour effacer le fichier physique)."""
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM documents WHERE id = ?", (doc_id,)
    ).fetchone()
    if row:
        conn.execute("DELETE FROM documents WHERE id = ?", (doc_id,))
        conn.commit()
    conn.close()
    return dict(row) if row else None


def mark_all_indexed() -> None:
    """Marque tous les documents comme indexés (après une réindexation complète)."""
    conn = get_connection()
    conn.execute("UPDATE documents SET indexed = 1")
    conn.commit()
    conn.close()