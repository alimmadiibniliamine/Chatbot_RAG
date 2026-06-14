"""
============================================================
 Fichier : backend/routes/chat_routes.py
 Rôle    : Endpoints de gestion des conversations et messages.

   GET    /chat/conversations            → liste mes conversations
   POST   /chat/conversations            → crée une conversation
   PUT    /chat/conversations/<id>       → renomme une conversation
   DELETE /chat/conversations/<id>       → supprime une conversation
   GET    /chat/conversations/<id>/messages  → liste les messages

 Toutes les routes sont protégées par @token_required.
============================================================
"""

from flask import Blueprint, request, jsonify

from backend.auth.auth_utils import token_required
from backend.models import conversation as conv_model
from backend.models import message as msg_model

chat_bp = Blueprint("chat", __name__, url_prefix="/chat")


@chat_bp.get("/conversations")
@token_required
def list_conversations():
    return jsonify(conv_model.list_conversations(request.user_id))


@chat_bp.post("/conversations")
@token_required
def create_conversation():
    data  = request.get_json() or {}
    title = data.get("title") or "Nouvelle conversation"
    cid   = conv_model.create_conversation(request.user_id, title)
    return jsonify({"id": cid, "title": title})


@chat_bp.put("/conversations/<int:cid>")
@token_required
def rename_conversation(cid):
    data      = request.get_json() or {}
    new_title = (data.get("title") or "").strip()
    if not new_title:
        return jsonify({"error": "Titre requis"}), 400
    if not conv_model.get_conversation(cid, request.user_id):
        return jsonify({"error": "Conversation introuvable"}), 404
    conv_model.rename_conversation(cid, request.user_id, new_title)
    return jsonify({"ok": True})


@chat_bp.delete("/conversations/<int:cid>")
@token_required
def delete_conversation(cid):
    if not conv_model.get_conversation(cid, request.user_id):
        return jsonify({"error": "Conversation introuvable"}), 404
    conv_model.delete_conversation(cid, request.user_id)
    return jsonify({"ok": True})


@chat_bp.get("/conversations/<int:cid>/messages")
@token_required
def get_messages(cid):
    if not conv_model.get_conversation(cid, request.user_id):
        return jsonify({"error": "Conversation introuvable"}), 404
    return jsonify(msg_model.list_messages(cid))