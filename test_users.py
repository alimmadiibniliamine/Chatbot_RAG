"""Petit utilitaire pour voir les utilisateurs en base."""
import sqlite3

conn = sqlite3.connect("database.db")
conn.row_factory = sqlite3.Row
rows = conn.execute("SELECT id, email, role, created_at FROM users").fetchall()
conn.close()

if not rows:
    print("Aucun utilisateur en base.")
else:
    print(f"{len(rows)} utilisateur(s) trouvé(s) :")
    for r in rows:
        print(f"  - id={r['id']}  email={r['email']}  role={r['role']}  créé={r['created_at']}")