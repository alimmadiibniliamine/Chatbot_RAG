"""
============================================================
 Fichier : backend/auth/auth_utils.py
 Rôle    : Centraliser tous les outils d'authentification :
   - hashage des mots de passe avec bcrypt
   - génération / vérification de tokens JWT
   - décorateurs Flask pour protéger les routes
============================================================
"""

import datetime
from functools import wraps

import bcrypt
import jwt
from flask import request, jsonify

from backend.config import Config


# ============================================================
# 1) GESTION DES MOTS DE PASSE (BCRYPT)
# ============================================================
# bcrypt est un algorithme de hashage lent (résistant au brute-force).
# Il génère automatiquement un "salt" différent pour chaque mot de passe.

def hash_password(password: str) -> str:
    """Transforme un mot de passe en clair en hash bcrypt sécurisé."""
    return bcrypt.hashpw(
        password.encode("utf-8"),
        bcrypt.gensalt(),
    ).decode("utf-8")


def verify_password(password: str, hashed: str) -> bool:
    """Compare un mot de passe en clair à un hash bcrypt stocké."""
    return bcrypt.checkpw(
        password.encode("utf-8"),
        hashed.encode("utf-8"),
    )


# ============================================================
# 2) GESTION DES JETONS JWT (SESSIONS STATELESS)
# ============================================================
# Un JWT est un jeton signé contenant des informations (id utilisateur,
# rôle, date d'expiration). Côté serveur, on n'a RIEN à stocker :
# on vérifie simplement la signature à chaque requête.

def generate_token(user_id: int, role: str) -> str:
    """Crée un JWT signé contenant l'id utilisateur et son rôle."""
    payload = {
        "user_id": user_id,
        "role": role,
        # Date d'expiration absolue
        "exp": datetime.datetime.utcnow()
               + datetime.timedelta(hours=Config.JWT_EXPIRATION_HOURS),
    }
    return jwt.encode(payload, Config.JWT_SECRET, algorithm="HS256")


def decode_token(token: str):
    """
    Vérifie et décode un JWT.
    Retourne le payload (dict) si valide, sinon None.
    """
    try:
        return jwt.decode(token, Config.JWT_SECRET, algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        return None     # Token expiré
    except jwt.InvalidTokenError:
        return None     # Token invalide / corrompu


# ============================================================
# 3) DÉCORATEURS POUR PROTÉGER LES ROUTES FLASK
# ============================================================

def token_required(f):
    """
    Décorateur : exige un JWT valide pour accéder à la route.
    Le token doit être passé en header : "Authorization: Bearer <token>".
    On expose ensuite request.user_id et request.user_role pour la vue.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return jsonify({"error": "Token manquant"}), 401

        token = auth_header.split(" ", 1)[1]
        payload = decode_token(token)
        if payload is None:
            return jsonify({"error": "Token invalide ou expiré"}), 401

        # On rend l'info disponible dans la vue Flask
        request.user_id = payload["user_id"]
        request.user_role = payload["role"]
        return f(*args, **kwargs)
    return decorated


def admin_required(f):
    """
    Décorateur : exige un JWT valide ET le rôle 'admin'.
    """
    @wraps(f)
    @token_required
    def decorated(*args, **kwargs):
        if request.user_role != "admin":
            return jsonify({"error": "Accès réservé à l'administrateur"}), 403
        return f(*args, **kwargs)
    return decorated