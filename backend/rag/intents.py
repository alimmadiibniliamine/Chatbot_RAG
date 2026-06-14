"""
============================================================
 Fichier : backend/rag/intents.py
 Rôle    : Détecter les "intentions" simples qui n'ont pas
           besoin d'aller chercher dans les documents :
              - salutations  (bonjour, salut, hello…)
              - identité     (qui es-tu, c'est quoi ton nom…)
              - remerciement (merci, thanks…)
              - au revoir    (bye, ciao, à bientôt…)

 Avantage : on évite d'appeler ChromaDB + Ollama pour ce type
 de message → réponse instantanée, économie de ressources.
============================================================
"""

import re
import random


# ------------------------------------------------------------
# DICTIONNAIRES D'INTENTIONS
# Chaque intention contient :
#   - une liste de mots-clés (matchés en début de question)
#   - une liste de réponses possibles (choisies aléatoirement)
# ------------------------------------------------------------

INTENTS = {
    "salutation": {
        "patterns": [
            r"^(bonjour|bonsoir|salut|hello|hi|hey|coucou|yo|bjr|slt|cc)\b",
        ],
        "responses": [
            "Bonjour ! 👋 Je suis votre assistant documentaire. "
            "Posez-moi une question sur les documents disponibles.",
            "Salut ! 😊 Comment puis-je vous aider aujourd'hui ?",
            "Bonjour ! Je suis à votre disposition pour répondre "
            "à vos questions à partir des documents indexés.",
        ],
    },

    "identite": {
        "patterns": [
            r"\b(qui (es[- ]?tu|êtes[- ]?vous|est[- ]?ce que tu es))\b",
            r"\b(c'est quoi ton nom|comment tu t'appelles|ton nom)\b",
            r"\b(tu es qui|t'es qui|vous êtes qui)\b",
            r"\b(présente[- ]?toi|présentez[- ]?vous)\b",
            r"\b(que (sais|peux)[- ]?tu faire|à quoi sers[- ]?tu)\b",
        ],
        "responses": [
            "Je suis un **chatbot intelligent basé sur le RAG** "
            "(Retrieval-Augmented Generation). 🤖\n\n"
            "Mon rôle est de répondre à vos questions en m'appuyant "
            "sur les documents indexés par l'administrateur. "
            "Je combine une recherche dans une base vectorielle "
            "(ChromaDB) avec un modèle de langage local (Ollama) "
            "pour vous fournir des réponses fiables et sourcées.",
        ],
    },

    "remerciement": {
        "patterns": [
            r"^(merci|thanks|thank you|thx|mci)\b",
        ],
        "responses": [
            "Avec plaisir ! 🙂 N'hésitez pas si vous avez d'autres questions.",
            "De rien ! Je suis là si besoin.",
            "Je vous en prie ! 👍",
        ],
    },

    "au_revoir": {
        "patterns": [
            r"^(au revoir|adieu|bye|ciao|à bientôt|à plus|a\+|tchao)\b",
        ],
        "responses": [
            "Au revoir ! 👋 À bientôt.",
            "À bientôt ! Passez une excellente journée.",
        ],
    },
}


def detect_intent(question: str):
    """
    Analyse la question et retourne (intent_name, response) si une
    intention simple est détectée, sinon (None, None).

    On normalise la question (minuscules, espaces nettoyés) puis on
    teste chaque pattern regex défini dans INTENTS.
    """
    if not question:
        return None, None

    # Normalisation : minuscules, suppression des espaces parasites
    normalized = question.lower().strip()
    normalized = re.sub(r"\s+", " ", normalized)

    # On parcourt chaque intention
    for intent_name, intent_data in INTENTS.items():
        for pattern in intent_data["patterns"]:
            if re.search(pattern, normalized):
                # On choisit une réponse aléatoirement (plus naturel)
                response = random.choice(intent_data["responses"])
                return intent_name, response

    return None, None