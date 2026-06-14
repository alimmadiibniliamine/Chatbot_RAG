#!/usr/bin/env bash
# ============================================================
# Lance le frontend Streamlit.
# Le backend doit être démarré au préalable (port 5000).
# ============================================================
[ -d "venv" ] && source venv/bin/activate
streamlit run frontend/streamlit_app.py