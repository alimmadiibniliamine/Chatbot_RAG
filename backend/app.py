"""
============================================================
 Fichier : backend/app.py
 Rôle    : Point d'entrée du backend Flask.

 Lancement en développement :
     python -m backend.app

 Lancement en production (avec Gunicorn) :
     gunicorn -w 2 -b 0.0.0.0:5000 'backend.app:create_app()'
============================================================
"""

from flask import Flask, jsonify
from flask_cors import CORS

from backend.config import Config
from backend.database.init_db import init_db
from backend.routes.auth_routes  import auth_bp
from backend.routes.chat_routes  import chat_bp
from backend.routes.rag_routes   import rag_bp
from backend.routes.admin_routes import admin_bp


def create_app() -> Flask:
    """
    Factory pattern : crée et configure l'application Flask.
    Avantage : permet de créer plusieurs instances (utile pour les tests)
    et facilite l'utilisation avec Gunicorn.
    """
    app = Flask(__name__)
    app.config.from_object(Config)

    # CORS : autorise le frontend Streamlit à appeler le backend
    # (le navigateur Streamlit tourne sur un port différent).
    CORS(app)

    # Initialisation de la base SQLite au démarrage
    init_db()

    # Routes de santé (utiles pour le déploiement)
    @app.get("/")
    def home():
        return jsonify({
            "status":  "ok",
            "service": "rag-chatbot-backend",
        })

    @app.get("/health")
    def health():
        return jsonify({"status": "ok"})

    # Enregistrement des Blueprints (regroupements de routes)
    app.register_blueprint(auth_bp)
    app.register_blueprint(chat_bp)
    app.register_blueprint(rag_bp)
    app.register_blueprint(admin_bp)

    return app


# Permet le lancement direct : python -m backend.app
if __name__ == "__main__":
    application = create_app()
    application.run(host="0.0.0.0", port=5000, debug=True)