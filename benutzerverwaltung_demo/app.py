"""Mini-Benutzerverwaltung mit Gruppen und Rechten (Flask).

Ziel: zeigen, wie Konten, Gruppen und Rechte zusammenspielen,
wie in Active Directory. Nur erfundene Demo-Daten.
"""
import os
import secrets
from functools import wraps

from flask import Flask, abort, redirect, render_template_string, request, session, url_for

from users import UserStore, seed

PAGE = """
<!doctype html><meta charset="utf-8"><title>Benutzerverwaltung Demo</title>
<h1>{{ title }}</h1>
{% if user %}<p>Angemeldet als <b>{{ user }}</b> (Gruppe: {{ group }}) | <a href="/logout">Abmelden</a></p>{% endif %}
{{ body|safe }}
"""


def create_app(store=None):
    app = Flask(__name__)
    # Geheimnis aus der Umgebung, nie im Code
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY") or secrets.token_hex(16)
    if store is None:
        store = UserStore()
        seed(store)
    app.config["STORE"] = store

    def current_user():
        name = session.get("user")
        if name and store.is_active(name):
            return name
        session.pop("user", None)
        return None

    def permission_required(permission):
        def decorator(view):
            @wraps(view)
            def wrapped(*args, **kwargs):
                name = current_user()
                if name is None:
                    return redirect(url_for("login"))
                if not store.has_permission(name, permission):
                    abort(403)
                return view(*args, **kwargs)
            return wrapped
        return decorator

    def page(title, body):
        name = current_user()
        group = store.group_of(name) if name else ""
        return render_template_string(PAGE, title=title, body=body, user=name, group=group)

    @app.route("/")
    def index():
        name = current_user()
        if name is None:
            return redirect(url_for("login"))
        # Startseite nach Login: erste Seite, die zur Gruppe passt
        for permission, endpoint in (
            ("akte_lesen", "akte"),
            ("abrechnung_lesen", "abrechnung"),
            ("benutzer_verwalten", "benutzer"),
        ):
            if store.has_permission(name, permission):
                return redirect(url_for(endpoint))
        abort(403)

    @app.route("/login", methods=["GET", "POST"])
    def login():
        if request.method == "POST":
            name = request.form.get("name", "")
            if store.check_login(name, request.form.get("password", "")):
                session["user"] = name
                return redirect(url_for("index"))
            return page("Anmelden", "<p>Anmeldung fehlgeschlagen.</p>"), 401
        form = ('<form method="post">Name <input name="name"> '
                'Passwort <input name="password" type="password"> '
                '<button>Anmelden</button></form>')
        return page("Anmelden", form)

    @app.route("/logout")
    def logout():
        session.clear()
        return redirect(url_for("login"))

    @app.route("/akte")
    @permission_required("akte_lesen")
    def akte():
        return page("Patientenakte (Demo)", "<p>Erfundener Patient: Max Muster, Herz-Kreislauf-Check.</p>")

    @app.route("/akte/neu", methods=["POST"])
    @permission_required("akte_schreiben")
    def akte_neu():
        return page("Eintrag gespeichert (Demo)", "<p>Neuer Eintrag angelegt.</p>")

    @app.route("/abrechnung")
    @permission_required("abrechnung_lesen")
    def abrechnung():
        return page("Abrechnung (Demo)", "<p>Erfundene Rechnung Nr. 1001.</p>")

    @app.route("/admin/benutzer")
    @permission_required("benutzer_verwalten")
    def benutzer():
        rows = "".join(f"<li>{n}: {g} ({'aktiv' if a else 'deaktiviert'})</li>" for n, g, a in store.list_users())
        return page("Benutzer", f"<ul>{rows}</ul>")

    @app.route("/admin/benutzer/<name>/deaktivieren", methods=["POST"])
    @permission_required("benutzer_verwalten")
    def deaktivieren(name):
        store.deactivate(name)
        return redirect(url_for("benutzer"))

    return app


if __name__ == "__main__":
    create_app().run(debug=False)
