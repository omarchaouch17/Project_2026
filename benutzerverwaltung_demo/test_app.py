import pytest

from app import create_app
from users import UserStore, seed


@pytest.fixture()
def client():
    store = UserStore()
    seed(store)
    app = create_app(store)
    app.config["TESTING"] = True
    return app.test_client(), store


def login(c, name, password):
    return c.post("/login", data={"name": name, "password": password})


def test_ohne_login_wird_umgeleitet(client):
    c, _ = client
    r = c.get("/akte")
    assert r.status_code == 302 and "/login" in r.headers["Location"]


def test_pflege_darf_akte_lesen(client):
    c, _ = client
    login(c, "schwester_anna", "demo-pflege-1")
    assert c.get("/akte").status_code == 200


def test_pflege_darf_nicht_schreiben(client):
    c, _ = client
    login(c, "schwester_anna", "demo-pflege-1")
    assert c.post("/akte/neu").status_code == 403


def test_arzt_darf_schreiben(client):
    c, _ = client
    login(c, "dr_berger", "demo-arzt-1")
    assert c.post("/akte/neu").status_code == 200


def test_verwaltung_sieht_abrechnung_aber_keine_akte(client):
    c, _ = client
    login(c, "verwaltung_kai", "demo-verwaltung-1")
    assert c.get("/abrechnung").status_code == 200
    assert c.get("/akte").status_code == 403


def test_falsches_passwort(client):
    c, _ = client
    assert login(c, "dr_berger", "falsch").status_code == 401


def test_passwort_nur_als_hash_gespeichert(client):
    _, store = client
    assert "demo-arzt-1" not in store.raw_hash("dr_berger")


def test_deaktiviertes_konto_kann_sich_nicht_anmelden(client):
    c, store = client
    store.deactivate("dr_berger")
    assert login(c, "dr_berger", "demo-arzt-1").status_code == 401


def test_deaktivierung_beendet_laufende_sitzung(client):
    c, store = client
    login(c, "schwester_anna", "demo-pflege-1")
    assert c.get("/akte").status_code == 200
    store.deactivate("schwester_anna")
    assert c.get("/akte").status_code == 302


def test_nur_admin_sieht_benutzerliste(client):
    c, _ = client
    login(c, "schwester_anna", "demo-pflege-1")
    assert c.get("/admin/benutzer").status_code == 403
    c.get("/logout")
    login(c, "admin_it", "demo-admin-1")
    assert c.get("/admin/benutzer").status_code == 200


def test_startseite_nach_login_passt_zur_gruppe(client):
    c, _ = client
    r = login(c, "admin_it", "demo-admin-1")
    assert r.status_code == 302 and r.headers["Location"].endswith("/")
    assert c.get("/").headers["Location"].endswith("/admin/benutzer")
    c.get("/logout")
    login(c, "verwaltung_kai", "demo-verwaltung-1")
    assert c.get("/").headers["Location"].endswith("/abrechnung")
