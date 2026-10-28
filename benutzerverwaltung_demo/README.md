# Benutzerverwaltung (Demo)

Kleine Flask-App: Konten, Gruppen und Rechte, wie in Active Directory.
Alle Daten sind erfunden. Keine echten Patientendaten.

## Idee (Active Directory einfach erklärt)

| Begriff | In dieser Demo |
|---|---|
| Konto (Benutzer) | `UserStore.add_user` |
| Gruppe | `pflege`, `arzt`, `verwaltung`, `admin` |
| Recht | z. B. `akte_lesen`, `akte_schreiben` |
| Prinzip der geringsten Rechte | jede Gruppe hat nur ihre nötigen Rechte |
| Konto deaktivieren | `UserStore.deactivate` (laufende Sitzung endet) |

Passwörter werden nur als Hash gespeichert. Das Geheimnis für Sitzungen kommt aus der Umgebungsvariable `SECRET_KEY`, nicht aus dem Code.

## Starten

    py -m pip install -r requirements.txt
    py app.py
    py -m pytest -q

Demo-Konten stehen in `users.py` (Funktion `seed`).

## Grenzen (ehrlich)

Das ist eine Lern-Demo: Konten liegen im Speicher, es gibt kein echtes Active Directory und keine Zwei-Faktor-Anmeldung. Für den Echtbetrieb wären zentrale Verzeichnisdienste (z. B. AD/LDAP), Protokollierung und Datenschutzkonzept nötig.
