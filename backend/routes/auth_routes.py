"""
============================================================
 Fichier : backend/routes/auth_routes.py
 Rôle    : Endpoints d'authentification.

   POST /auth/register   → inscription
   POST /auth/login      → connexion
   (la déconnexion se fait simplement en supprimant le token côté client)
============================================================
"""

from flask import Blueprint, request, jsonify

from backend.models.user import get_user_by_email, create_user
from backend.auth.auth_utils import (
    hash_password, verify_password, generate_token,
)

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


@auth_bp.post("/register")
def register():
    """Inscription d'un nouvel utilisateur (rôle 'user' par défaut)."""
    data = request.get_json() or {}
    email    = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    # Validations
    if not email or not password:
        return jsonify({"error": "Email et mot de passe requis"}), 400
    if len(password) < 6:
        return jsonify({"error": "Mot de passe trop court (min 6 caractères)"}), 400
    if get_user_by_email(email):
        return jsonify({"error": "Cet email est déjà utilisé"}), 409

    # Création
    user_id = create_user(email, hash_password(password), role="user")
    token = generate_token(user_id, "user")

    return jsonify({
        "token": token,
        "user": {"id": user_id, "email": email, "role": "user"},
    })


@auth_bp.post("/login")
def login():
    """Connexion : vérifie email + mot de passe et retourne un JWT."""
    data = request.get_json() or {}
    email    = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    user = get_user_by_email(email)
    if not user or not verify_password(password, user["password_hash"]):
        return jsonify({"error": "Identifiants invalides"}), 401

    token = generate_token(user["id"], user["role"])
    return jsonify({
        "token": token,
        "user": {
            "id":    user["id"],
            "email": user["email"],
            "role":  user["role"],
        },
    })