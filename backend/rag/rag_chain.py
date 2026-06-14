"""
============================================================
 Fichier : backend/rag/rag_chain.py
 Rôle    : Chaîne RAG complète avec LangChain + Ollama.

 Deux modes d'exécution :
   - ask_question()        : réponse complète (one-shot)
   - ask_question_stream() : réponse token par token (streaming)

 Avant tout appel au LLM, on vérifie l'intention de l'utilisateur :
 si c'est une salutation, une question d'identité, etc., on répond
 directement sans solliciter ChromaDB ni Ollama.
============================================================
"""

from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser

from backend.config import Config
from backend.rag.indexer import get_vectorstore
from backend.rag.intents import detect_intent


# ------------------------------------------------------------
# PROMPT STRICT : interdit au LLM d'utiliser ses connaissances
# pré-entraînées. La réponse doit venir uniquement du contexte.
# ------------------------------------------------------------
PROMPT_TEMPLATE = """Tu es un assistant documentaire strict.
Ta SEULE source de vérité est le CONTEXTE fourni ci-dessous.

RÈGLES ABSOLUES :
1. Tu ne réponds QUE en utilisant les informations du CONTEXTE.
2. Il est INTERDIT d'utiliser tes connaissances générales.
3. Si la réponse n'est PAS dans le CONTEXTE, réponds EXACTEMENT :
   "Je ne trouve pas la réponse à cette question dans les documents disponibles."
4. Tu n'inventes rien, tu ne supposes rien.
5. Tu réponds en français, de manière claire et concise.

--- CONTEXTE ---
{context}
--- FIN DU CONTEXTE ---

Question : {question}

Réponse :"""


# Seuil de pertinence (distance L2). À ajuster empiriquement.
RELEVANCE_THRESHOLD = 1.5
DEBUG_RAG = False   # passer à True pour voir les scores dans les logs


# Singleton du LLM
_llm_instance = None


def get_llm() -> ChatOllama:
    """Retourne (et initialise au besoin) le client Ollama."""
    global _llm_instance
    if _llm_instance is None:
        _llm_instance = ChatOllama(
            model=Config.OLLAMA_MODEL,
            base_url=Config.OLLAMA_BASE_URL,
            temperature=0.0,   # déterministe, pas de créativité
        )
    return _llm_instance


def _format_docs(docs) -> str:
    """Concatène les chunks récupérés en une seule chaîne de contexte."""
    return "\n\n".join(d.page_content for d in docs)


def _retrieve_relevant_docs(question: str):
    """
    Récupère les chunks les plus proches dans Chroma, puis applique
    le filtre de pertinence. Retourne la liste des Documents pertinents.
    """
    vectorstore = get_vectorstore()
    docs_with_scores = vectorstore.similarity_search_with_score(
        question, k=Config.TOP_K
    )

    if DEBUG_RAG:
        print(f"\n[RAG] Question : {question!r}")
        for i, (doc, score) in enumerate(docs_with_scores, 1):
            preview = doc.page_content[:70].replace("\n", " ")
            print(f"  [{i}] score={score:.3f}  {preview}…")

    relevant_docs = [
        doc for doc, score in docs_with_scores
        if score <= RELEVANCE_THRESHOLD
    ]
    return relevant_docs


def _build_chain(relevant_docs):
    """Construit la chaîne LangChain (LCEL) à partir des docs pertinents."""
    prompt = ChatPromptTemplate.from_template(PROMPT_TEMPLATE)
    return (
        {
            "context": lambda _: _format_docs(relevant_docs),
            "question": RunnablePassthrough(),
        }
        | prompt
        | get_llm()
        | StrOutputParser()
    )


def _extract_sources(docs):
    """Construit la liste des sources à renvoyer au frontend."""
    return [
        {
            "source": d.metadata.get("source", "inconnu"),
            "page":   d.metadata.get("page", None),
        }
        for d in docs
    ]


# ============================================================
# MODE 1 : RÉPONSE COMPLÈTE (one-shot)
# ============================================================
def ask_question(question: str):
    """
    Exécute la chaîne RAG complète et retourne (answer, sources).
    Utilisé pour les sauvegardes en BDD côté backend.
    """
    # 1) Vérification d'intention (salutation, identité, etc.)
    intent_name, intent_response = detect_intent(question)
    if intent_response is not None:
        return intent_response, []

    # 2) Recherche dans Chroma + filtrage
    relevant_docs = _retrieve_relevant_docs(question)
    if not relevant_docs:
        return (
            "Je ne trouve pas la réponse à cette question "
            "dans les documents disponibles.",
            [],
        )

    # 3) Appel au LLM
    chain = _build_chain(relevant_docs)
    answer = chain.invoke(question)

    return answer, _extract_sources(relevant_docs)


# ============================================================
# MODE 2 : STREAMING (token par token)
# ============================================================
def ask_question_stream(question: str):
    """
    Générateur qui produit la réponse token par token.

    À chaque "yield", on émet un dict :
       {"type": "token",   "content": "..."}   ← un fragment de texte
       {"type": "sources", "data":   [...]}    ← liste des sources (à la fin)
       {"type": "done"}                         ← marque la fin du flux

    Le frontend Streamlit consomme ces dicts au fur et à mesure
    pour afficher la réponse en temps réel.
    """
    # 1) Vérification d'intention
    intent_name, intent_response = detect_intent(question)
    if intent_response is not None:
        # On streame quand même la réponse (par groupes de mots)
        # pour avoir l'effet "machine à écrire" visible côté frontend
        for chunk in _chunk_text(intent_response):
            yield {"type": "token", "content": chunk}
        yield {"type": "sources", "data": []}
        yield {"type": "done"}
        return

    # 2) Recherche dans Chroma + filtrage
    relevant_docs = _retrieve_relevant_docs(question)
    if not relevant_docs:
        fallback = ("Je ne trouve pas la réponse à cette question "
                    "dans les documents disponibles.")
        for chunk in _chunk_text(fallback):
            yield {"type": "token", "content": chunk}
        yield {"type": "sources", "data": []}
        yield {"type": "done"}
        return

    # 3) STREAMING via Ollama
    chain = _build_chain(relevant_docs)
    # chain.stream() retourne un générateur de tokens
    for token in chain.stream(question):
        yield {"type": "token", "content": token}

    # 4) En fin de flux : les sources
    yield {"type": "sources", "data": _extract_sources(relevant_docs)}
    yield {"type": "done"}


def _chunk_text(text: str, words_per_chunk: int = 2):
    """
    Découpe un texte en petits morceaux pour simuler le streaming
    sur les réponses prédéfinies (intentions, fallback).
    """
    words = text.split(" ")
    for i in range(0, len(words), words_per_chunk):
        yield " ".join(words[i:i + words_per_chunk]) + " "