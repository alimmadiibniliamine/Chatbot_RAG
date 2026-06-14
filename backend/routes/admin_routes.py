"""
============================================================
 Fichier : backend/routes/admin_routes.py
 Rôle    : Endpoints réservés à l'administrateur.

   GET    /admin/documents          → liste des documents
   POST   /admin/documents          → upload + indexation incrémentale
   DELETE /admin/documents/<id>     → suppression d'un document
   POST   /admin/reindex            → réindexation complète

 Toutes les routes sont protégées par @admin_required.
============================================================
"""

import os
from werkzeug.utils import secure_filename
from flask import Blueprint, request, jsonify

from backend.auth.auth_utils import admin_required
from backend.config import Config
from backend.models import document as doc_model
from backend.rag.indexer import index_file, reindex_all

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")

# Extensions autorisées pour l'upload
ALLOWED_EXTENSIONS = {".pdf", ".txt"}


@admin_bp.get("/documents")
@admin_required
def list_documents():
    return jsonify(doc_model.list_documents())


@admin_bp.post("/documents")
@admin_required
def upload_document():
    """Upload d'un document + indexation immédiate dans ChromaDB."""
    if "file" not in request.files:
        return jsonify({"error": "Aucun fichier fourni"}), 400

    file = request.files["file"]
    if not file.filename:
        return jsonify({"error": "Nom de fichier manquant"}), 400

    # Vérification de l'extension
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        return jsonify({"error": "Formats autorisés : PDF, TXT"}), 400

    # Sauvegarde physique du fichier (nom sécurisé)
    safe_name = secure_filename(file.filename)
    filepath  = os.path.join(Config.UPLOAD_FOLDER, safe_name)
    file.save(filepath)

    # Enregistrement en BDD
    doc_id = doc_model.add_document(safe_name, filepath, request.user_id)

    # Indexation incrémentale
    try:
        chunks = index_file(filepath)
    except Exception as e:
        return jsonify({
            "error": f"Indexation échouée : {e}",
            "id": doc_id,
        }), 500

    return jsonify({
        "id":       doc_id,
        "filename": safe_name,
        "chunks":   chunks,
    })


@admin_bp.delete("/documents/<int:doc_id>")
@admin_required
def delete_document(doc_id):
    """
    Supprime un document :
      - de la BDD
      - du disque
    NB : pour le retirer aussi de ChromaDB, il faut lancer
    "Réindexation complète" depuis l'interface admin.
    """
    doc = doc_model.delete_document(doc_id)
    if not doc:
        return jsonify({"error": "Document introuvable"}), 404

    # Suppression du fichier physique
    try:
        if os.path.exists(doc["filepath"]):
            os.remove(doc["filepath"])
    except Exception as e:
        print(f"[admin] Erreur suppression fichier : {e}")

    return jsonify({
        "ok": True,
        "note": "Pensez à relancer la réindexation complète pour purger l'index vectoriel.",
    })


@admin_bp.post("/reindex")
@admin_required
def reindex():
    """Reconstruit entièrement ChromaDB à partir du dossier uploads/."""
    try:
        chunks = reindex_all()
        doc_model.mark_all_indexed()
    except Exception as e:
        return jsonify({"error": f"Échec : {e}"}), 500
    return jsonify({"ok": True, "chunks": chunks})