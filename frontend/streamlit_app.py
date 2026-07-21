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
    page_icon=":material/agriculture:",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# STYLE GLOBAL
# ------------------------------------------------------------
# Palette inspirée du monde agricole (vert CUMA) sur fond neutre,
# typographie soignée, boutons arrondis, cartes pour les listes.
# ============================================================
CUSTOM_CSS = """
<style>
    :root {
        --primary: #2E7D32;
        --primary-light: #E8F5E9;
        --primary-dark: #1B5E20;
        --surface: #FFFFFF;
        --border: #E0E0E0;
        --text-muted: #6B7280;
    }

    /* Typographie générale */
    html, body, [class*="css"] {
        font-family: "Segoe UI", "Inter", -apple-system, sans-serif;
    }

    /* Titres */
    h1 {
        font-weight: 700 !important;
        color: var(--primary-dark) !important;
        letter-spacing: -0.5px;
    }
    h1 .material-symbols-outlined,
    h3 .material-symbols-outlined,
    h4 .material-symbols-outlined {
        vertical-align: -4px;
        color: var(--primary);
        margin-right: 6px;
    }

    /* Bandeau d'introduction sur la page de connexion */
    .hero-card {
        background: linear-gradient(135deg, var(--primary-light) 0%, #FFFFFF 100%);
        border: 1px solid var(--border);
        border-radius: 16px;
        padding: 28px 32px;
        margin-bottom: 28px;
    }
    .hero-card p {
        color: #374151;
        line-height: 1.6;
        margin-bottom: 0;
    }

    /* Boutons */
    .stButton > button {
        border-radius: 10px !important;
        border: 1px solid var(--border) !important;
        font-weight: 500 !important;
        transition: all 0.15s ease-in-out;
    }
    .stButton > button:hover {
        border-color: var(--primary) !important;
        color: var(--primary-dark) !important;
        background-color: var(--primary-light) !important;
    }
    .stButton > button[kind="primary"] {
        background-color: var(--primary) !important;
        border-color: var(--primary) !important;
    }
    .stButton > button[kind="primary"]:hover {
        background-color: var(--primary-dark) !important;
    }

    /* Sidebar */
    section[data-testid="stSidebar"] {
        background-color: #FAFAFA;
        border-right: 1px solid var(--border);
    }

    /* Carte "utilisateur connecté" en haut de sidebar */
    .user-card {
        display: flex;
        align-items: center;
        gap: 10px;
        background-color: var(--surface);
        border: 1px solid var(--border);
        border-radius: 12px;
        padding: 10px 14px;
        margin-bottom: 12px;
    }
    .user-card .avatar {
        width: 34px;
        height: 34px;
        border-radius: 50%;
        background: var(--primary);
        color: white;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: 600;
        font-size: 14px;
        flex-shrink: 0;
    }
    .user-card .email {
        font-weight: 600;
        font-size: 14px;
        color: #111827;
    }
    .user-card .role {
        font-size: 12px;
        color: var(--text-muted);
    }

    /* Badge de rôle */
    .role-badge {
        display: inline-block;
        background-color: var(--primary-light);
        color: var(--primary-dark);
        border-radius: 999px;
        padding: 2px 10px;
        font-size: 11px;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.4px;
    }

    /* Séparateurs de section dans la liste des documents */
    div[data-testid="stExpander"] {
        border-radius: 10px !important;
        border: 1px solid var(--border) !important;
    }
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


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


def render_user_card():
    """Petite carte affichant l'utilisateur connecté dans la sidebar."""
    email = st.session_state.user["email"]
    role = st.session_state.user["role"]
    initial = email[0].upper() if email else "?"
    st.markdown(
        f"""
        <div class="user-card">
            <div class="avatar">{initial}</div>
            <div>
                <div class="email">{email}</div>
                <span class="role-badge">{role}</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ============================================================
# VUE 1 : LOGIN / REGISTER
# ============================================================
def render_login():
    """Affiche les onglets Connexion / Inscription."""
    st.title(":material/agriculture: Assistant Intelligent Chantiers CUMA")

    st.markdown(
        """
        <div class="hero-card">
            <p><b>Bienvenue sur l'Assistant Intelligent Chantiers CUMA.</b></p>
            <p>Développé dans le cadre d'un mémoire de fin d'études en partenariat avec
            <b>Kandorlab</b>, ce chatbot exploite la technologie
            <b>Retrieval-Augmented Generation (RAG)</b> afin d'offrir une assistance
            intelligente aux utilisateurs de la plateforme <b>Chantiers</b>.</p>
            <p>Grâce à une recherche sémantique dans la documentation officielle,
            il fournit des réponses fiables, rapides et contextualisées pour accompagner
            les adhérents, salariés et gestionnaires dans leurs activités quotidiennes.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    tab_login, tab_register = st.tabs([
        ":material/login: Connexion",
        ":material/person_add: Inscription",
    ])

    # ---- Connexion ----
    with tab_login:
        with st.form("login_form"):
            email    = st.text_input("Email")
            password = st.text_input("Mot de passe", type="password")
            submit   = st.form_submit_button(
                "Se connecter", type="primary",
                icon=":material/login:", use_container_width=True,
            )

        if submit:
            data, code = api.login(email, password)
            if code == 200:
                st.session_state.token = data["token"]
                st.session_state.user  = data["user"]
                st.rerun()
            else:
                st.error(data.get("error", "Erreur inconnue"), icon=":material/error:")

    # ---- Inscription ----
    with tab_register:
        with st.form("register_form"):
            email    = st.text_input("Email", key="reg_email")
            password = st.text_input(
                "Mot de passe (6 caractères min.)",
                type="password",
                key="reg_pwd",
            )
            submit   = st.form_submit_button(
                "Créer le compte", type="primary",
                icon=":material/person_add:", use_container_width=True,
            )

        if submit:
            data, code = api.register(email, password)
            if code == 200:
                st.session_state.token = data["token"]
                st.session_state.user  = data["user"]
                st.success("Compte créé avec succès !", icon=":material/check_circle:")
                st.rerun()
            else:
                st.error(data.get("error", "Erreur inconnue"), icon=":material/error:")


# ============================================================
# VUE 2 : CHAT (UTILISATEUR)
# ============================================================
def render_chat():
    """Page principale : sidebar avec conversations + zone de chat."""

    # ----- SIDEBAR -----
    with st.sidebar:
        render_user_card()

        # Bouton "Nouvelle conversation"
        if st.button(
            "Nouvelle conversation", icon=":material/add_circle:",
            type="primary", use_container_width=True,
        ):
            new_conv = api.create_conversation()
            st.session_state.current_conv = new_conv["id"]
            st.session_state.messages = []
            st.rerun()

        st.divider()
        st.markdown("#### :material/forum: Mes conversations")

        # Liste des conversations existantes
        conversations = api.list_conversations()
        for c in conversations:
            # 3 colonnes : nom / renommer / supprimer
            col_name, col_edit, col_del = st.columns([5, 1, 1])

            # Tronquer le titre s'il est trop long
            label = c["title"][:28] + ("…" if len(c["title"]) > 28 else "")
            is_active = (st.session_state.current_conv == c["id"])
            icon = ":material/chat_bubble:" if is_active else ":material/chat_bubble_outline:"

            if col_name.button(label, icon=icon,
                               key=f"conv_{c['id']}",
                               use_container_width=True):
                st.session_state.current_conv = c["id"]
                st.session_state.messages     = api.get_messages(c["id"])
                st.rerun()

            if col_edit.button("", icon=":material/edit:", key=f"rename_{c['id']}", help="Renommer"):
                st.session_state[f"renaming_{c['id']}"] = True

            if col_del.button("", icon=":material/delete:", key=f"delete_{c['id']}", help="Supprimer"):
                api.delete_conversation(c["id"])
                if st.session_state.current_conv == c["id"]:
                    st.session_state.current_conv = None
                    st.session_state.messages = []
                st.rerun()

            # Formulaire de renommage (inline)
            if st.session_state.get(f"renaming_{c['id']}"):
                with st.form(f"rename_form_{c['id']}"):
                    new_title = st.text_input("Nouveau titre", value=c["title"])
                    if st.form_submit_button("OK", icon=":material/check:"):
                        api.rename_conversation(c["id"], new_title)
                        st.session_state[f"renaming_{c['id']}"] = False
                        st.rerun()

        st.divider()

        # Accès admin (uniquement pour les admins)
        if st.session_state.user["role"] == "admin":
            if st.button(
                "Espace administrateur", icon=":material/settings:",
                use_container_width=True,
            ):
                st.session_state.view = "admin"
                st.rerun()

        # Déconnexion
        if st.button("Se déconnecter", icon=":material/logout:", use_container_width=True):
            logout()
            st.rerun()

    # ----- ZONE PRINCIPALE : CHAT -----
    st.title(":material/smart_toy: Chatbot RAG")

    if st.session_state.current_conv is None:
        st.info(
            "Sélectionnez ou créez une conversation pour commencer.",
            icon=":material/arrow_back:",
        )
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
                    # Le curseur simule l'effet d'écriture (style ChatGPT)
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
                placeholder.error(f"Erreur : {error}", icon=":material/error:")
            else:
                placeholder.markdown(full_answer)

                # Affichage des sources
                if sources:
                    with st.expander(":material/menu_book: Sources utilisées"):
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
        render_user_card()
        st.caption("Mode administrateur")

        if st.button("Retour au chat", icon=":material/arrow_back:", use_container_width=True):
            st.session_state.view = "chat"
            st.rerun()
        if st.button("Se déconnecter", icon=":material/logout:", use_container_width=True):
            logout()
            st.rerun()

    # ----- ZONE PRINCIPALE -----
    st.title(":material/settings: Espace administrateur")
    st.caption("Gestion des documents et de l'indexation RAG")

    # --- 1) Upload ---
    st.subheader(":material/upload_file: Ajouter un document")
    uploaded_file = st.file_uploader(
        "Choisir un fichier PDF ou TXT",
        type=["pdf", "txt"],
    )
    if uploaded_file and st.button(
        "Téléverser et indexer", type="primary", icon=":material/cloud_upload:",
    ):
        with st.spinner("Indexation en cours…"):
            data, code = api.upload_document(uploaded_file)
        if code == 200:
            st.success(
                f"{data['filename']} indexé ({data['chunks']} chunks)",
                icon=":material/check_circle:",
            )
            st.rerun()
        else:
            st.error(data.get("error", "Erreur lors de l'upload"), icon=":material/error:")

    st.divider()

    # --- 2) Liste des documents ---
    st.subheader(":material/folder_open: Documents indexés")
    documents = api.list_documents()
    if not documents:
        st.info("Aucun document. Ajoutez-en un ci-dessus.", icon=":material/info:")
    for d in documents:
        col_name, col_date, col_del = st.columns([5, 2, 1])
        col_name.markdown(f":material/description: **{d['filename']}**")
        col_date.caption(f"Ajouté : {d['created_at']}")
        if col_del.button("", icon=":material/delete:", key=f"del_doc_{d['id']}"):
            api.delete_document(d["id"])
            st.rerun()

    st.divider()

    # --- 3) Réindexation complète ---
    st.subheader(":material/sync: Réindexation complète")
    st.caption(
        "Reconstruit entièrement la base vectorielle ChromaDB "
        "à partir des fichiers présents dans `uploads/`. "
        "À utiliser après une suppression de document."
    )
    if st.button("Lancer la réindexation", icon=":material/refresh:", type="secondary"):
        with st.spinner("Réindexation en cours… (peut prendre quelques minutes)"):
            result = api.reindex()
        if result.get("ok"):
            st.success(
                f"Réindexation terminée : {result['chunks']} chunks",
                icon=":material/check_circle:",
            )
        else:
            st.error(result.get("error", "Erreur"), icon=":material/error:")


# ============================================================
# ROUTEUR PRINCIPAL
# ============================================================
if not st.session_state.token:
    render_login()
elif st.session_state.view == "admin" and st.session_state.user["role"] == "admin":
    render_admin()
else:
    render_chat()