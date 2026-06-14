"""
============================================================
 Fichier : backend/rag/loader.py
 Rôle    : Charger des fichiers PDF / TXT en objets
           "Document" LangChain (texte + métadonnées).

 Pipeline RAG — étape 1 :
   [FICHIER PDF/TXT]  ──►  [LangChain Documents]
============================================================
"""

import os
from langchain_community.document_loaders import PyPDFLoader, TextLoader


def load_file(filepath: str):
    """
    Charge un fichier (PDF ou TXT) et retourne une liste de
    Documents LangChain.

    - Pour un PDF : 1 Document = 1 page (avec metadata "page")
    - Pour un TXT : 1 Document = tout le fichier
    """
    ext = os.path.splitext(filepath)[1].lower()

    if ext == ".pdf":
        # PyPDFLoader découpe automatiquement par page.
        loader = PyPDFLoader(filepath)
    elif ext == ".txt":
        loader = TextLoader(filepath, encoding="utf-8")
    else:
        raise ValueError(f"Format non supporté : {ext}")

    return loader.load()


def load_directory(directory: str):
    """
    Charge TOUS les fichiers PDF/TXT d'un dossier.
    Utilisé lors de la réindexation complète.
    """
    documents = []
    for filename in os.listdir(directory):
        filepath = os.path.join(directory, filename)
        if not os.path.isfile(filepath):
            continue
        if not filename.lower().endswith((".pdf", ".txt")):
            continue
        try:
            documents.extend(load_file(filepath))
        except Exception as e:
            # On loggue mais on n'interrompt pas tout le pipeline
            print(f"[loader] Erreur sur {filename} : {e}")
    return documents