"""
BrixHub Admin Panel — flat version (no subfolders, templates embedded)
Run: python panel_app.py
"""

import os
import sys

# Make sure db/config are importable from same folder
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask, request, redirect, url_for, session, Response
import db
from config import PANEL_SECRET

app = Flask(__name__)
app.secret_key = PANEL_SECRET

# ──────────────────────────────────────────────
# EMBEDDED TEMPLATES (no /templates folder needed)
# ──────────────────────────────────────────────

CSS = """
<style>
* { margin:0; padding:0; box-sizing:border-box; }
body { background:#0d1117; color:#e6edf3; font-family:'Segoe UI',sans-serif; }
.sidebar { position:fixed; top:0; left:0; width:210px; height:100vh; background:#161b22;
  border-right:1px solid #30363d; padding:24px 14px; }
.sidebar h2 { color:#58a6ff; font-size:15px; margin-bottom:28px; }
.sidebar a { display:block; color:#8b949e; text-decoration:none; padding:8px 12px;
  border-radius:6px; font-size:13px; margin-bottom:4px; }
.sidebar a:hover { background:#21262d; color:#e6edf3; }
.sidebar .logout { margin-top:40px; color:#f85149 !important; }
.main { margin-left:210px; padding:32px; }
h1 { font-size:20px; margin-bottom:24px; }
table { width:100%; border-collapse:collapse; background:#161b22;
  border-radius:10px; overflow:hidden; }
th { background:#21262d; padding:11px 14px; text-align:left; font-size:11px;
  color:#8b949e; text-transform:uppercase; letter-spacing:.5px; }
td { padding:11px 14px; font-size:13px; border-top:1px solid #21262d; }
tr:hover td { background:#1c2128; }
.badge { display:inline-block; padding:2px 10px; border-radius:20px;
  font-size:11px; font-weight:600; }
.bp { background:#1f3d1f; color:#3fb950; }
.bf { background:#1f2428; color:#8b949e; }
.bo { background:#1f2e1f; color:#3fb950; }
.bc { background:#2a1f1f; color:#f85149; }
.btn { display:inline-block; padding:4px 11px; border-radius:6px;
  font-size:12px; font-weight:600; text-decoration:none; }
.bg { background:#238636; color:#fff; margin-right:5px; }
.bg:hover { background:#2ea043; }
.br { background:#6e2226; color:#fff; }
.br:hover { background:#b62324; }
.stat-grid { display:grid; grid-template-columns:repeat(3,1fr); gap:14px; margin-bottom:28px; }
.stat-card { background:#161b22; border:1px solid #30363d; border-radius:10px; padding:18px; }
.stat-card .num { font-size:30px; font-weight:700; color:#58a6ff; }
.stat-card .lbl { font-size:12px; color:#8b949e; margin-top:4px; }
/* login */
.center { display:flex; align-items:center; justify-content:center; height:100vh; }
.card { background:#161b22; border:1px solid #30363d; border-radius:12px; padding:36px; width:340px; }
.card h1 { color:#58a6ff; font-size:20px; margin-bottom:6px; }
.card p { color:#8b949e; font-size:13px; margin-bottom:22px; }
input { width:100%; background:#0d1117; border:1px solid #30363d; border-radius:7px;
  padding:9px 13px; color:#e6edf3; font-size:14px; outline:none; margin-bottom:14px; }
input:focus { border-color:#58a6ff; }
button { width:100%; background:#238636; border:none; border-radius:7px;
  padding:10px; color:#fff; font-size:14px; font-weight:600; cursor:pointer; }
button:hover { background:#2ea043; }
.err { color:#f85149; font-size:13px; margin-bottom:11px; }
code { background:#21262d; padding:1px 6px; border-radius:4px; font-size:12px; }
</style>
"""

SIDEBAR = """
<div class="sidebar">
  <h2>🔷 BrixHub Panel</h2>
  <a href="/">📊 Dashboard</a>
  <a href="/users">👥 Users</a>
  <a href="/tickets">🎫 Tickets</a>
  <a href="/logout" class="logout">🚪 Logout</a>
</div>
"""

def page(title: str, body: str) -> str:
    return f"""<!DOCTYPE html><html lang="fr"><head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title} — BrixHub Panel</title>{CSS}</head>
<body>{SIDEBAR}<div class="main">{body}</div></body></html>"""


def login_page(error: str = "") -> str:
    err_html = f'<div class="err">{error}</div>' if error else ""
    return f"""<!DOCTYPE html><html lang="fr"><head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Login — BrixHub Panel</title>{CSS}</head>
<body><div class="center"><div class="card">
<h1>🔐 BrixHub Panel</h1>
<p>Accès administrateur uniquement.</p>
{err_html}
<form method="POST">
<input type="password" name="password" placeholder="Mot de passe admin" autofocus>
<button type="submit">Connexion</button>
</form>
</div></div></body></html>"""


# ──────────────────────────────────────────────
# ROUTES
# ──────────────────────────────────────────────

def require_auth():
    if not session.get("auth"):
        return redirect(url_for("login"))
    return None


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        if request.form.get("password") == PANEL_SECRET:
            session["auth"] = True
            return redirect(url_for("index"))
        return Response(login_page("Mot de passe incorrect."), content_type="text/html")
    return Response(login_page(), content_type="text/html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/")
def index():
    redir = require_auth()
    if redir:
        return redir
    s = db.get_stats()
    body = f"""
<h1>📊 Dashboard</h1>
<div class="stat-grid">
  <div class="stat-card"><div class="num">{s['total_users']}</div><div class="lbl">Total utilisateurs</div></div>
  <div class="stat-card"><div class="num">{s['premium_users']}</div><div class="lbl">Premium</div></div>
  <div class="stat-card"><div class="num">{s['open_tickets']}</div><div class="lbl">Tickets ouverts</div></div>
</div>
<p style="color:#8b949e;font-size:13px;">Panel admin BrixHub — gère tes users et tickets depuis ici.</p>
"""
    return Response(page("Dashboard", body), content_type="text/html")


@app.route("/users")
def users():
    redir = require_auth()
    if redir:
        return redir
    rows = db.get_all_users()
    rows_html = ""
    for u in rows:
        prem = u["is_premium"]
        badge = '<span class="badge bp">💎 Premium</span>' if prem else '<span class="badge bf">🆓 Gratuit</span>'
        action = (
            f'<a href="/setpremium/{u["user_id"]}" class="btn bg">✅ Set Premium</a>'
            if not prem else
            '<span style="color:#3fb950;font-size:12px;">✔ Déjà premium</span>'
        )
        rows_html += f"""<tr>
<td><code>{u['user_id']}</code></td>
<td>{u['searches_today']}</td>
<td>{u['last_search_date'] or '—'}</td>
<td>{badge}</td>
<td>{action}</td>
</tr>"""
    if not rows_html:
        rows_html = '<tr><td colspan="5" style="color:#8b949e;text-align:center;padding:20px;">Aucun utilisateur.</td></tr>'
    body = f"""
<h1>👥 Utilisateurs</h1>
<table>
<thead><tr><th>User ID</th><th>Searches today</th><th>Dernier search</th><th>Statut</th><th>Action</th></tr></thead>
<tbody>{rows_html}</tbody>
</table>"""
    return Response(page("Users", body), content_type="text/html")


@app.route("/tickets")
def tickets():
    redir = require_auth()
    if redir:
        return redir
    rows = db.get_all_tickets()
    rows_html = ""
    for t in rows:
        open_ = t["status"] == "open"
        badge = '<span class="badge bo">🟢 Ouvert</span>' if open_ else '<span class="badge bc">🔴 Fermé</span>'
        action = (
            f'<a href="/setpremium/{t["user_id"]}" class="btn bg">✅ Premium</a>'
            f'<a href="/closeticket/{t["id"]}" class="btn br">🔒 Fermer</a>'
            if open_ else
            '<span style="color:#8b949e;font-size:12px;">Traité</span>'
        )
        created = str(t["created_at"])[:16]
        rows_html += f"""<tr>
<td><strong>#{t['id']}</strong></td>
<td><code>{t['user_id']}</code></td>
<td>{t['username']}</td>
<td>{badge}</td>
<td style="color:#8b949e;font-size:12px;">{created}</td>
<td>{action}</td>
</tr>"""
    if not rows_html:
        rows_html = '<tr><td colspan="6" style="color:#8b949e;text-align:center;padding:20px;">Aucun ticket.</td></tr>'
    body = f"""
<h1>🎫 Tickets</h1>
<table>
<thead><tr><th>#ID</th><th>User ID</th><th>Username</th><th>Statut</th><th>Créé le</th><th>Action</th></tr></thead>
<tbody>{rows_html}</tbody>
</table>"""
    return Response(page("Tickets", body), content_type="text/html")


@app.route("/setpremium/<user_id>")
def setpremium(user_id):
    redir = require_auth()
    if redir:
        return redir
    db.set_premium(user_id)
    return redirect(url_for("users"))


@app.route("/closeticket/<int:ticket_id>")
def closeticket(ticket_id):
    redir = require_auth()
    if redir:
        return redir
    db.close_ticket(ticket_id)
    return redirect(url_for("tickets"))


if __name__ == "__main__":
    db.init_db()
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
