"""
============================================================
 Fichier : backend/routes/rag_routes.py
 Rôle    : Endpoints du chatbot.

   POST /rag/ask          → réponse complète (one-shot, JSON)
   POST /rag/ask/stream   → réponse en streaming (NDJSON)

 Format NDJSON : chaque ligne est un objet JSON séparé par "\n".
 Le frontend lit ligne par ligne et met à jour l'affichage en
 temps réel.
============================================================
"""

import json
from flask import Blueprint, request, jsonify, Response, stream_with_context

from backend.auth.auth_utils import token_required
from backend.models import conversation as conv_model
from backend.models import message as msg_model
from backend.rag.rag_chain import ask_question, ask_question_stream

rag_bp = Blueprint("rag", __name__, url_prefix="/rag")


# ------------------------------------------------------------
# MODE 1 : RÉPONSE COMPLÈTE
# ------------------------------------------------------------
@rag_bp.post("/ask")
@token_required
def ask():
    """Endpoint non-streaming, conservé pour compatibilité."""
    data     = request.get_json() or {}
    cid      = data.get("conversation_id")
    question = (data.get("question") or "").strip()

    if not cid or not question:
        return jsonify({"error": "conversation_id et question requis"}), 400
    if not conv_model.get_conversation(cid, request.user_id):
        return jsonify({"error": "Conversation introuvable"}), 404

    msg_model.add_message(cid, "user", question)
    try:
        answer, sources = ask_question(question)
    except Exception as e:
        return jsonify({"error": f"Erreur RAG : {e}"}), 500

    msg_model.add_message(cid, "assistant", answer)
    conv_model.touch_conversation(cid)
    return jsonify({"answer": answer, "sources": sources})


# ------------------------------------------------------------
# MODE 2 : STREAMING (NDJSON)
# ------------------------------------------------------------
@rag_bp.post("/ask/stream")
@token_required
def ask_stream():
    """
    Endpoint streaming : renvoie la réponse token par token.

    Format : chaque ligne est un JSON terminé par "\n"
       {"type":"token","content":"Bon"}
       {"type":"token","content":"jour"}
       {"type":"sources","data":[...]}
       {"type":"done"}
    """
    data     = request.get_json() or {}
    cid      = data.get("conversation_id")
    question = (data.get("question") or "").strip()
    user_id  = request.user_id   # capturé AVANT le générateur

    if not cid or not question:
        return jsonify({"error": "conversation_id et question requis"}), 400
    if not conv_model.get_conversation(cid, user_id):
        return jsonify({"error": "Conversation introuvable"}), 404

    # Sauvegarde immédiate de la question utilisateur
    msg_model.add_message(cid, "user", question)

    def generate():
        """
        Générateur qui produit les lignes NDJSON envoyées au client.
        On accumule la réponse complète au passage pour la sauvegarder
        en BDD à la fin.
        """
        full_answer_parts = []
        sources = []

        try:
            for event in ask_question_stream(question):
                # On garde la trace du texte complet pour la sauvegarde
                if event["type"] == "token":
                    full_answer_parts.append(event["content"])
                elif event["type"] == "sources":
                    sources = event["data"]

                # On envoie l'événement au client (format NDJSON)
                yield json.dumps(event, ensure_ascii=False) + "\n"

        except Exception as e:
            # En cas d'erreur, on envoie un événement d'erreur
            yield json.dumps({"type": "error", "message": str(e)}) + "\n"
            return

        # 🔒 Sauvegarde de la réponse complète en BDD (après le stream)
        full_answer = "".join(full_answer_parts).strip()
        if full_answer:
            msg_model.add_message(cid, "assistant", full_answer)
            conv_model.touch_conversation(cid)

    # stream_with_context : permet d'utiliser request dans le générateur
    return Response(
        stream_with_context(generate()),
        mimetype="application/x-ndjson",
    )