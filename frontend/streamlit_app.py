"""
============================================================
 Fichier : frontend/streamlit_app.py
 Rôle    : Application Streamlit complète.

 Lancement :
     streamlit run frontend/streamlit_app.py
============================================================
"""

# ------------------------------------------------------------
# IMPORTANT : on ajoute la racine du projet au sys.path pour
# pouvoir importer le module `frontend` en absolu.
# Streamlit n'ajoute que le dossier du fichier lancé, pas la racine.
# ------------------------------------------------------------
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import streamlit as st
from frontend import api_client as api


# ============================================================
# CONFIGURATION DE LA PAGE
# ============================================================
st.set_page_config(
    page_title="RAG Chatbot",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# INITIALISATION DE L'ÉTAT DE SESSION
# ============================================================
# Streamlit recharge tout le script à chaque interaction,
# donc on utilise st.session_state pour conserver l'état.
DEFAULT_STATE = {
    "token": None,         # JWT renvoyé par le backend
    "user": None,          # { id, email, role }
    "current_conv": None,  # id de la conversation active
    "messages": [],        # messages de la conversation active
    "view": "chat",        # vue active : "chat" ou "admin"
}
for key, value in DEFAULT_STATE.items():
    if key not in st.session_state:
        st.session_state[key] = value


def logout():
    """Réinitialise la session (déconnexion)."""
    for key in ["token", "user", "current_conv", "messages"]:
        st.session_state[key] = [] if key == "messages" else None
    st.session_state["view"] = "chat"


# ============================================================
# VUE 1 : LOGIN / REGISTER
# ============================================================
def render_login():
    """Affiche les onglets Connexion / Inscription."""
    st.title("🤖 RAG Chatbot")
    st.caption("Mémoire de fin d'études — chatbot intelligent basé sur le RAG")

    tab_login, tab_register = st.tabs(["🔑 Connexion", "✍️ Inscription"])

    # ---- Connexion ----
    with tab_login:
        with st.form("login_form"):
            email    = st.text_input("Email")
            password = st.text_input("Mot de passe", type="password")
            submit   = st.form_submit_button("Se connecter", use_container_width=True)

        if submit:
            data, code = api.login(email, password)
            if code == 200:
                st.session_state.token = data["token"]
                st.session_state.user  = data["user"]
                st.rerun()
            else:
                st.error(data.get("error", "Erreur inconnue"))

    # ---- Inscription ----
    with tab_register:
        with st.form("register_form"):
            email    = st.text_input("Email", key="reg_email")
            password = st.text_input(
                "Mot de passe (6 caractères min.)",
                type="password",
                key="reg_pwd",
            )
            submit   = st.form_submit_button("Créer le compte", use_container_width=True)

        if submit:
            data, code = api.register(email, password)
            if code == 200:
                st.session_state.token = data["token"]
                st.session_state.user  = data["user"]
                st.success("Compte créé avec succès !")
                st.rerun()
            else:
                st.error(data.get("error", "Erreur inconnue"))


# ============================================================
# VUE 2 : CHAT (UTILISATEUR)
# ============================================================
def render_chat():
    """Page principale : sidebar avec conversations + zone de chat."""

    # ----- SIDEBAR -----
    with st.sidebar:
        st.markdown(f"### 👤 {st.session_state.user['email']}")
        st.caption(f"Rôle : `{st.session_state.user['role']}`")

        # Bouton "Nouvelle conversation"
        if st.button("➕ Nouvelle conversation", use_container_width=True):
            new_conv = api.create_conversation()
            st.session_state.current_conv = new_conv["id"]
            st.session_state.messages = []
            st.rerun()

        st.divider()
        st.markdown("#### 💬 Mes conversations")

        # Liste des conversations existantes
        conversations = api.list_conversations()
        for c in conversations:
            # 3 colonnes : nom / renommer / supprimer
            col_name, col_edit, col_del = st.columns([5, 1, 1])

            # Tronquer le titre s'il est trop long
            label = c["title"][:28] + ("…" if len(c["title"]) > 28 else "")
            is_active = (st.session_state.current_conv == c["id"])
            prefix = "🟢 " if is_active else "💬 "

            if col_name.button(prefix + label,
                               key=f"conv_{c['id']}",
                               use_container_width=True):
                st.session_state.current_conv = c["id"]
                st.session_state.messages     = api.get_messages(c["id"])
                st.rerun()

            if col_edit.button("✏️", key=f"rename_{c['id']}", help="Renommer"):
                st.session_state[f"renaming_{c['id']}"] = True

            if col_del.button("🗑️", key=f"delete_{c['id']}", help="Supprimer"):
                api.delete_conversation(c["id"])
                if st.session_state.current_conv == c["id"]:
                    st.session_state.current_conv = None
                    st.session_state.messages = []
                st.rerun()

            # Formulaire de renommage (inline)
            if st.session_state.get(f"renaming_{c['id']}"):
                with st.form(f"rename_form_{c['id']}"):
                    new_title = st.text_input("Nouveau titre", value=c["title"])
                    if st.form_submit_button("OK"):
                        api.rename_conversation(c["id"], new_title)
                        st.session_state[f"renaming_{c['id']}"] = False
                        st.rerun()

        st.divider()

        # Accès admin (uniquement pour les admins)
        if st.session_state.user["role"] == "admin":
            if st.button("⚙️ Espace administrateur", use_container_width=True):
                st.session_state.view = "admin"
                st.rerun()

        # Déconnexion
        if st.button("🚪 Se déconnecter", use_container_width=True):
            logout()
            st.rerun()

    # ----- ZONE PRINCIPALE : CHAT -----
    st.title("🤖 Chatbot RAG")

    if st.session_state.current_conv is None:
        st.info("👈 Sélectionnez ou créez une conversation pour commencer.")
        return

    # Affichage de l'historique
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    
    # Zone de saisie
    if prompt := st.chat_input("Posez votre question…"):
        # 1) Affichage immédiat du message utilisateur
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # 2) Affichage de la réponse en STREAMING
        with st.chat_message("assistant"):
            # Placeholder qui se remplit au fur et à mesure
            placeholder = st.empty()
            full_answer = ""
            sources = []
            error = None

            # On consomme le générateur de l'API
            for event in api.ask_question_stream(
                st.session_state.current_conv, prompt
            ):
                etype = event.get("type")

                if etype == "token":
                    # Ajout du nouveau token et rafraîchissement du markdown
                    full_answer += event["content"]
                    # Le "▌" simule le curseur d'écriture (effet ChatGPT)
                    placeholder.markdown(full_answer + "▌")

                elif etype == "sources":
                    sources = event["data"]

                elif etype == "error":
                    error = event["message"]
                    break

                elif etype == "done":
                    break

            # Affichage final (sans le curseur)
            if error:
                placeholder.error(f"Erreur : {error}")
            else:
                placeholder.markdown(full_answer)

                # Affichage des sources
                if sources:
                    with st.expander("📚 Sources utilisées"):
                        for s in sources:
                            page = (f" (page {s['page']})"
                                    if s.get("page") is not None else "")
                            st.write(f"- `{s['source']}`{page}")

                # On sauvegarde la réponse dans la session locale
                st.session_state.messages.append(
                    {"role": "assistant", "content": full_answer}
                )


# ============================================================
# VUE 3 : ADMIN (GESTION DOCUMENTS)
# ============================================================
def render_admin():
    """Page admin : upload, liste, suppression, réindexation."""

    # ----- SIDEBAR -----
    with st.sidebar:
        st.markdown(f"### 👤 {st.session_state.user['email']}")
        st.caption("Mode administrateur")

        if st.button("💬 Retour au chat", use_container_width=True):
            st.session_state.view = "chat"
            st.rerun()
        if st.button("🚪 Se déconnecter", use_container_width=True):
            logout()
            st.rerun()

    # ----- ZONE PRINCIPALE -----
    st.title("⚙️ Espace administrateur")
    st.caption("Gestion des documents et de l'indexation RAG")

    # --- 1) Upload ---
    st.subheader("📤 Ajouter un document")
    uploaded_file = st.file_uploader(
        "Choisir un fichier PDF ou TXT",
        type=["pdf", "txt"],
    )
    if uploaded_file and st.button("Téléverser et indexer", type="primary"):
        with st.spinner("Indexation en cours…"):
            data, code = api.upload_document(uploaded_file)
        if code == 200:
            st.success(f"✅ {data['filename']} indexé ({data['chunks']} chunks)")
            st.rerun()
        else:
            st.error(data.get("error", "Erreur lors de l'upload"))

    st.divider()

    # --- 2) Liste des documents ---
    st.subheader("📂 Documents indexés")
    documents = api.list_documents()
    if not documents:
        st.info("Aucun document. Ajoutez-en un ci-dessus.")
    for d in documents:
        col_name, col_date, col_del = st.columns([5, 2, 1])
        col_name.write(f"📄 **{d['filename']}**")
        col_date.caption(f"Ajouté : {d['created_at']}")
        if col_del.button("🗑️", key=f"del_doc_{d['id']}"):
            api.delete_document(d["id"])
            st.rerun()

    st.divider()

    # --- 3) Réindexation complète ---
    st.subheader("🔄 Réindexation complète")
    st.caption(
        "Reconstruit entièrement la base vectorielle ChromaDB "
        "à partir des fichiers présents dans `uploads/`. "
        "À utiliser après une suppression de document."
    )
    if st.button("Lancer la réindexation", type="secondary"):
        with st.spinner("Réindexation en cours… (peut prendre quelques minutes)"):
            result = api.reindex()
        if result.get("ok"):
            st.success(f"✅ Réindexation terminée : {result['chunks']} chunks")
        else:
            st.error(result.get("error", "Erreur"))


# ============================================================
# ROUTEUR PRINCIPAL
# ============================================================
if not st.session_state.token:
    render_login()
elif st.session_state.view == "admin" and st.session_state.user["role"] == "admin":
    render_admin()
else:
    render_chat()