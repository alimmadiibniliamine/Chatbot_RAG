"""
============================================================
 Fichier : backend/rag/indexer.py
 Rôle    : Pipeline d'indexation complet.

 Pipeline RAG — étapes 2, 3, 4 :

   [Documents LangChain]
        │
        ▼
   ┌──────────────┐
   │   CHUNKING   │  (RecursiveCharacterTextSplitter)
   └──────────────┘
        │
        ▼
   ┌────────────────┐
   │   EMBEDDINGS   │  (HuggingFace all-MiniLM-L6-v2)
   └────────────────┘
        │
        ▼
   ┌──────────────┐
   │  ChromaDB    │  (persistant sur disque)
   └──────────────┘

 Pourquoi HuggingFace plutôt qu'Ollama pour les embeddings ?
   - Plus rapide à charger (~80 Mo vs plusieurs Go)
   - Stable et déterministe
   - Gratuit et offline
============================================================
"""

import os
import shutil

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma

from backend.config import Config
from backend.rag.loader import load_file, load_directory


# ------------------------------------------------------------
# SINGLETON : on ne charge le modèle d'embeddings qu'UNE seule
# fois en mémoire. Sinon, chaque requête prendrait plusieurs
# secondes pour recharger ~80 Mo.
# ------------------------------------------------------------
_embeddings_instance = None


def get_embeddings():
    """Retourne (et initialise au besoin) le modèle d'embeddings."""
    global _embeddings_instance
    if _embeddings_instance is None:
        print("[indexer] Chargement du modèle d'embeddings (1ère fois)…")
        _embeddings_instance = HuggingFaceEmbeddings(
            model_name=Config.EMBEDDING_MODEL,
            model_kwargs={"device": "cpu"},        # CPU = compatible partout
            encode_kwargs={"normalize_embeddings": True},
        )
    return _embeddings_instance


def get_vectorstore() -> Chroma:
    """
    Retourne le vector store ChromaDB persistant.
    Toutes les données sont stockées dans Config.CHROMA_DIR.
    """
    return Chroma(
        persist_directory=Config.CHROMA_DIR,
        embedding_function=get_embeddings(),
        collection_name="rag_documents",
    )


def _get_text_splitter() -> RecursiveCharacterTextSplitter:
    """
    Splitter récursif :
    essaie de couper sur "\\n\\n", puis "\\n", puis " ", etc.
    Cela préserve la structure (paragraphes, phrases) autant que possible.
    """
    return RecursiveCharacterTextSplitter(
        chunk_size=Config.CHUNK_SIZE,
        chunk_overlap=Config.CHUNK_OVERLAP,
    )


def index_file(filepath: str) -> int:
    """
    Indexe UN seul fichier dans ChromaDB (ajout incrémental).

    Étapes :
       1. Charger le fichier en Documents LangChain
       2. Découper en chunks
       3. Ajouter au vector store (qui calcule les embeddings)

    Retourne le nombre de chunks ajoutés.
    """
    docs = load_file(filepath)
    if not docs:
        return 0

    chunks = _get_text_splitter().split_documents(docs)
    get_vectorstore().add_documents(chunks)
    return len(chunks)


def reindex_all() -> int:
    """
    Réindexation COMPLÈTE :
      - supprime entièrement la base Chroma existante
      - recharge tous les fichiers du dossier uploads/
      - reconstruit la base à partir de zéro

    À utiliser après une suppression de document ou des modifications massives.
    """
    global _embeddings_instance

    # 1) Suppression complète de l'ancien index
    if os.path.exists(Config.CHROMA_DIR):
        shutil.rmtree(Config.CHROMA_DIR)
    os.makedirs(Config.CHROMA_DIR, exist_ok=True)

    # 2) Rechargement de tous les fichiers
    docs = load_directory(Config.UPLOAD_FOLDER)
    if not docs:
        return 0

    # 3) Chunking + indexation
    chunks = _get_text_splitter().split_documents(docs)
    get_vectorstore().add_documents(chunks)
    return len(chunks)