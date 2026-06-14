"""
============================================================
 Fichier : frontend/api_client.py
 Rôle    : Wrapper léger autour de `requests` pour appeler le
           backend Flask depuis Streamlit.

 Le token JWT est stocké dans st.session_state.token et envoyé
 automatiquement dans le header "Authorization: Bearer ...".
============================================================
"""

import os
import requests
import streamlit as st
import json

# URL du backend (configurable pour le déploiement distant)
API_URL = os.getenv("BACKEND_URL", "http://localhost:5000")


def _auth_headers() -> dict:
    """Construit le header Authorization à partir du token en session."""
    token = st.session_state.get("token")
    return {"Authorization": f"Bearer {token}"} if token else {}


# ------------------------------------------------------------
# AUTHENTIFICATION
# ------------------------------------------------------------
def login(email: str, password: str):
    r = requests.post(
        f"{API_URL}/auth/login",
        json={"email": email, "password": password},
    )
    return r.json(), r.status_code


def register(email: str, password: str):
    r = requests.post(
        f"{API_URL}/auth/register",
        json={"email": email, "password": password},
    )
    return r.json(), r.status_code


# ------------------------------------------------------------
# CONVERSATIONS
# ------------------------------------------------------------
def list_conversations():
    r = requests.get(f"{API_URL}/chat/conversations", headers=_auth_headers())
    return r.json() if r.ok else []


def create_conversation(title: str = "Nouvelle conversation"):
    r = requests.post(
        f"{API_URL}/chat/conversations",
        json={"title": title},
        headers=_auth_headers(),
    )
    return r.json()


def rename_conversation(cid: int, title: str):
    return requests.put(
        f"{API_URL}/chat/conversations/{cid}",
        json={"title": title},
        headers=_auth_headers(),
    ).json()


def delete_conversation(cid: int):
    return requests.delete(
        f"{API_URL}/chat/conversations/{cid}",
        headers=_auth_headers(),
    ).json()


def get_messages(cid: int):
    r = requests.get(
        f"{API_URL}/chat/conversations/{cid}/messages",
        headers=_auth_headers(),
    )
    return r.json() if r.ok else []


# ------------------------------------------------------------
# RAG (chatbot)
# ------------------------------------------------------------
def ask_question(cid: int, question: str):
    # Timeout long car Ollama peut prendre du temps sur un PC modeste
    r = requests.post(
        f"{API_URL}/rag/ask",
        json={"conversation_id": cid, "question": question},
        headers=_auth_headers(),
        timeout=300,
    )
    return r.json(), r.status_code




def ask_question_stream(cid: int, question: str):
    """
    Générateur qui consomme l'endpoint /rag/ask/stream du backend.

    À chaque ligne reçue, on parse le JSON et on yield un dict :
       {"type": "token",   "content": "..."}
       {"type": "sources", "data":   [...]}
       {"type": "done"}
       {"type": "error",   "message": "..."}

    Côté Streamlit, on consomme ce générateur pour afficher
    la réponse au fur et à mesure.
    """
    r = requests.post(
        f"{API_URL}/rag/ask/stream",
        json={"conversation_id": cid, "question": question},
        headers=_auth_headers(),
        stream=True,            # ⬅️ ESSENTIEL : on ne bufferise pas
        timeout=600,
    )

    if not r.ok:
        # Erreur HTTP : on essaie d'extraire un message
        try:
            err = r.json().get("error", f"Erreur HTTP {r.status_code}")
        except Exception:
            err = f"Erreur HTTP {r.status_code}"
        yield {"type": "error", "message": err}
        return

    # On lit le flux ligne par ligne
    for raw_line in r.iter_lines(decode_unicode=True):
        if not raw_line:
            continue
        try:
            event = json.loads(raw_line)
        except json.JSONDecodeError:
            continue   # ligne corrompue, on saute
        yield event
# ------------------------------------------------------------
# ADMIN
# ------------------------------------------------------------
def list_documents():
    r = requests.get(f"{API_URL}/admin/documents", headers=_auth_headers())
    return r.json() if r.ok else []


def upload_document(file):
    files = {"file": (file.name, file.getvalue())}
    r = requests.post(
        f"{API_URL}/admin/documents",
        files=files,
        headers=_auth_headers(),
    )
    return r.json(), r.status_code


def delete_document(doc_id: int):
    return requests.delete(
        f"{API_URL}/admin/documents/{doc_id}",
        headers=_auth_headers(),
    ).json()


def reindex():
    return requests.post(
        f"{API_URL}/admin/reindex",
        headers=_auth_headers(),
        timeout=600,
    ).json()