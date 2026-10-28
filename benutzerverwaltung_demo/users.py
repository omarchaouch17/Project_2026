"""Benutzer, Gruppen (Rollen) und Rechte: kleines Modell wie in Active Directory.

Alle Daten sind erfunden (Demo). Keine echten Patientendaten.
"""
from werkzeug.security import generate_password_hash, check_password_hash

# Gruppe -> Rechte (Prinzip der geringsten Rechte)
GROUP_PERMISSIONS = {
    "pflege": {"akte_lesen"},
    "arzt": {"akte_lesen", "akte_schreiben"},
    "verwaltung": {"abrechnung_lesen"},
    "admin": {"benutzer_verwalten"},
}


class UserStore:
    """Verwaltet Konten im Speicher. Passwoerter nur als Hash."""

    def __init__(self):
        self._users = {}

    def add_user(self, name, password, group):
        if group not in GROUP_PERMISSIONS:
            raise ValueError("unbekannte Gruppe: " + group)
        self._users[name] = {
            "password_hash": generate_password_hash(password),
            "group": group,
            "active": True,
        }

    def check_login(self, name, password):
        user = self._users.get(name)
        if user is None or not user["active"]:
            return False
        return check_password_hash(user["password_hash"], password)

    def group_of(self, name):
        return self._users[name]["group"]

    def has_permission(self, name, permission):
        user = self._users.get(name)
        if user is None or not user["active"]:
            return False
        return permission in GROUP_PERMISSIONS[user["group"]]

    def deactivate(self, name):
        self._users[name]["active"] = False

    def is_active(self, name):
        user = self._users.get(name)
        return bool(user and user["active"])

    def list_users(self):
        return [(n, u["group"], u["active"]) for n, u in sorted(self._users.items())]

    def raw_hash(self, name):
        return self._users[name]["password_hash"]


def seed(store):
    """Demo-Konten (nur zum Testen der eigenen App)."""
    store.add_user("schwester_anna", "demo-pflege-1", "pflege")
    store.add_user("dr_berger", "demo-arzt-1", "arzt")
    store.add_user("verwaltung_kai", "demo-verwaltung-1", "verwaltung")
    store.add_user("admin_it", "demo-admin-1", "admin")
