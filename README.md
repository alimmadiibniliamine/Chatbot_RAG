# 🤖 RAG Chatbot — Mémoire de fin d'études

Chatbot intelligent basé sur le **RAG (Retrieval-Augmented Generation)**,
développé avec **Flask + Streamlit + LangChain + ChromaDB + Ollama + SQLite**.

## ✨ Fonctionnalités

- 🔐 Authentification avec rôles `admin` / `user` (JWT + bcrypt)
- 💬 Conversations multiples par utilisateur (créer, renommer, supprimer)
- 📂 Upload et indexation de documents PDF / TXT (admin)
- 🧠 Pipeline RAG complet avec LangChain
- 🤖 Génération via Ollama (LLM 100 % local)
- 📚 Affichage des sources utilisées pour chaque réponse

## 🏗️ Architecture

```
Documents PDF/TXT
       │
       ▼
   Chunking (LangChain TextSplitter)
       │
       ▼
   Embeddings (HuggingFace all-MiniLM-L6-v2)
       │
       ▼
   ChromaDB (base vectorielle persistante)
       │
       ▼
   Retriever (similarité cosine, top-k)
       │
       ▼
   Prompt + Contexte
       │
       ▼
   Ollama (mistral / llama3 / phi3)
       │
       ▼
   Réponse en français
```

## 📦 Prérequis

- Python 3.10+
- [Ollama](https://ollama.com) installé localement
- 8 Go de RAM minimum recommandés

## 🚀 Installation

### 1. Cloner le projet et créer un environnement virtuel

```bash
git clone <votre-repo>
cd rag-chatbot

python -m venv venv
source venv/bin/activate              # Linux / macOS
# venv\Scripts\activate               # Windows


```

### 2. Installer Ollama et télécharger un modèle

```bash
# Linux / macOS
curl -fsSL https://ollama.com/install.sh | sh

# Windows : télécharger depuis https://ollama.com/download

# Choisir un modèle léger :
ollama pull mistral          # ~4 Go, polyvalent (recommandé)
# ollama pull llama3         # ~4.7 Go
# ollama pull phi3           # ~2.3 Go, très léger

# Vérifier
ollama list
```

Ollama démarre automatiquement un serveur sur `http://localhost:11434`.

### 3. Configurer les variables d'environnement

```bash
cp .env.example .env
# Éditez .env si nécessaire (modèle, mots de passe…)
génerer les clés avec la commande :  python -c "import secrets; print(secrets.token_hex(32))"  

```

### 4. Lancer le backend Flask

```bash
python -m backend.app
# → http://localhost:5000
```

### 5. Lancer le frontend Streamlit (autre terminal)

```bash
streamlit run frontend/streamlit_app.py
# → http://localhost:8501
```

## 👤 Compte administrateur par défaut

Créé automatiquement au premier démarrage :

- **Email** : `admin@kandorlab.com`
- **Mot de passe** : `admin123`

(modifiables via `.env`)

## 📂 Utilisation

1. Connectez-vous en tant qu'admin
2. Cliquez sur **⚙️ Espace administrateur**
3. Uploadez vos documents PDF / TXT → indexation automatique
4. Retournez au chat, créez une **➕ Nouvelle conversation**
5. Posez vos questions !

## 🚢 Déploiement

### Production avec Gunicorn

```bash
gunicorn -w 2 -b 0.0.0.0:5000 'backend.app:create_app()'
```

### Frontend distant

Pour faire communiquer un Streamlit distant avec votre backend Flask :

```bash
export BACKEND_URL=https://mon-backend.exemple.com
streamlit run frontend/streamlit_app.py --server.address 0.0.0.0
```

### Conseils par plateforme

- **VPS Linux** : utilisez `systemd` ou `supervisor` pour gérer les services
- **Render / Railway** : déployez backend et frontend comme deux services web séparés
- **Streamlit Community Cloud** : possible pour le frontend uniquement ; le backend doit être hébergé ailleurs
- **Ollama distant** : ajustez `OLLAMA_BASE_URL` dans `.env`

## 🧪 Tests rapides

```bash
# Backend
curl http://localhost:5000/health
# → {"status":"ok"}

# Ollama
curl http://localhost:11434
# → "Ollama is running"
```

## 📁 Structure du projet

```
rag-chatbot/
├── backend/         # Serveur Flask (API REST)
├── frontend/        # Application Streamlit
├── data/            # Documents sources (optionnel)
├── chroma_db/       # Base vectorielle (auto-créée)
├── uploads/         # Documents uploadés (auto-créé)
├── database.db      # Base SQLite (auto-créée)
└── requirements.txt
```

## ⚠️ Notes importantes

- La **première requête** est plus lente : le modèle d'embeddings se télécharge (~80 Mo)
- Ollama doit être lancé **AVANT** le backend Flask
- En cas de suppression de documents, utilisez la **« Réindexation complète »**

## 📚 Technologies

| Composant | Technologie |
|-----------|-------------|
| Backend API | Flask 3 |
| Frontend | Streamlit |
| RAG | LangChain |
| Base vectorielle | ChromaDB |
| Base relationnelle | SQLite |
| LLM | Ollama (mistral / llama3 / phi3) |
| Embeddings | HuggingFace `all-MiniLM-L6-v2` |
| Auth | JWT + bcrypt |