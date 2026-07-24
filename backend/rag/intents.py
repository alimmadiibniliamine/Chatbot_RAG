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



"""
Intentions du chatbot - Application Chantier CUMA
Ce chatbot aide les utilisateurs (adhérents, chauffeurs, gestionnaires)
à s'informer sur les chantiers, le matériel et les documents CUMA.
"""


# Salutation exacte à renvoyer selon le mot utilisé par l'utilisateur.
# Ex : l'utilisateur dit "Bonsoir" -> le bot répond "Bonsoir".
SALUTATION_REPLIES = {
    "bonjour": "Bonjour",
    "bonsoir": "Bonsoir",
    "salut": "Salut",
    "hello": "Hello",
    "hi": "Hello",
    "hey": "Hey",
    "coucou": "Coucou",
    "yo": "Yo",
    "bjr": "Bonjour",
    "slt": "Salut",
    "cc": "Coucou",
}


def get_salutation_response(user_message: str) -> str:
    """
    Détecte la salutation utilisée par l'utilisateur (bonjour, bonsoir, salut...)
    et construit la réponse avec la même salutation.
    """
    pattern = INTENTS["salutation"]["patterns"][0]
    match = re.search(pattern, user_message.lower().strip())
    mot_utilise = match.group(1) if match else "bonjour"
    salutation = SALUTATION_REPLIES.get(mot_utilise, "Bonjour")

    return (
        f"{salutation} ! 👋 Je suis l'assistant de l'application Chantier CUMA. "
        "Posez-moi une question sur vos chantiers, votre matériel ou vos documents."
    )


INTENTS = {
    "salutation": {
        "patterns": [
            r"^(bonjour|bonsoir|salut|hello|hi|hey|coucou|yo|bjr|slt|cc)\b",
        ],
        # Ces réponses par défaut ne servent que si get_salutation_response()
        # n'est pas utilisée. En pratique, pour l'intention "salutation",
        # appeler get_salutation_response(message_utilisateur) à la place.
        "responses": [
            "Bonjour ! 👋 Je suis l'assistant de l'application Chantier CUMA. "
            "Posez-moi une question sur vos chantiers, votre matériel ou vos documents.",
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
            "Je suis l'**assistant virtuel de l'application Chantier CUMA**. \n\n"
            "Je m'appuie sur les documents et données de votre coopérative "
            "(plannings de chantiers, matériel, comptes-rendus) pour répondre "
            "à vos questions et vous accompagner dans votre travail au quotidien.",
        ],
    },

    "aide": {
        "patterns": [
            r"\b(aide|besoin d'aide|comment (faire|ça marche)|mode d'emploi)\b",
            r"\b(je suis perdu|je ne comprends pas)\b",
        ],
        "responses": [
            "Bien sûr, je peux vous renseigner sur :\n"
            "- l'état d'avancement d'un chantier\n"
            "- la disponibilité du matériel\n"
            "- les documents liés à votre CUMA\n\n"
            "N'hésitez pas à me poser votre question directement.",
        ],
    },

    "remerciement": {
        "patterns": [
            r"^(merci|thanks|thank you|thx|mci)\b",
        ],
        "responses": [
            "Avec plaisir ! N'hésitez pas si vous avez d'autres questions concernant vos chantiers.",
            "Je vous en prie, je reste à votre disposition.",
            "De rien, bonne continuation dans vos travaux !",
        ],
    },

    "au_revoir": {
        "patterns": [
            r"^(au revoir|adieu|bye|ciao|à bientôt|à plus|a\+|tchao)\b",
        ],
        "responses": [
            "Au revoir ! Bonne journée et bon chantier. 👋",
            "À bientôt, n'hésitez pas à revenir si besoin d'informations sur vos chantiers.",
        ],
    },
}


# --- Exemple d'utilisation dans le code qui gère les intentions ---
# if intent_detectee == "salutation":
#     reponse = get_salutation_response(message_utilisateur)
# else:
#     reponse = random.choice(INTENTS[intent_detectee]["responses"])


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