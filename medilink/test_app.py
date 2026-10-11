"""Tests for the MediLink Flask app. Run with: py -m pytest -v"""
import re

import pytest
import app as app_module
from app import app
from translations import texts, DIAGNOSIS_TRANSLATIONS, CATEGORY_TRANSLATIONS, CATEGORIES, DIAGNOSES, OTHER

VALID = {"patient_id": "1", "sex": "m", "age": "55", "cholesterol": "220",
         "hdl": "50", "blood_pressure": "140", "smoking": "never", "lang": "de"}


@pytest.fixture
def client():
    """A fake browser that sends requests to the app without starting a server."""
    app.config["TESTING"] = True
    c = app.test_client()
    with c.session_transaction() as session_data:   # Standard-Testbesucher ist Admin (sieht alles)
        session_data["admin"] = True
        session_data["visitor"] = "test"
    return c


@pytest.fixture
def visitor():
    """Normaler, fremder Besucher ohne Admin-Rechte."""
    app.config["TESTING"] = True
    c = app.test_client()
    with c.session_transaction() as session_data:
        session_data["visitor"] = "fremd"
    return c


@pytest.fixture
def fake_db(monkeypatch):
    """Replace the database functions so tests never touch the real patients.db."""
    saved = []
    monkeypatch.setattr(app_module, "add_patient",
                        lambda name, text: saved.append(name) or 99)
    monkeypatch.setattr(app_module, "add_condition",
                        lambda patient_id, diagnosis, category: None)
    monkeypatch.setattr(app_module, "save_risk", lambda *args, **kwargs: None)
    return saved


_real_list = app_module.get_visible_patients


@pytest.fixture(autouse=True)
def fake_visits(monkeypatch):
    """Besucher-Zaehler schreibt never in die echte Datenbank."""
    counted = []
    monkeypatch.setattr(app_module, "count_visit", counted.append)
    return counted


@pytest.fixture(autouse=True)
def fake_patients(monkeypatch):
    """Vorhandene Patienten fuer die Auswahlliste im Risiko-Formular (never die echte Datenbank)."""
    monkeypatch.setattr(app_module, "get_visible_patients", lambda: [(2, "Anna"), (1, "Demo")])


@pytest.fixture
def fake_risk(monkeypatch):
    """Merkt sich, zu welchen Patienten ein Score saved wird."""
    class SavedList(list):
        details = []
    saved = SavedList()
    saved.details = []

    def save(patient_id, *args, **kwargs):
        saved.append(patient_id)
        saved.details.append((args, kwargs))
    monkeypatch.setattr(app_module, "save_risk", save)
    return saved


@pytest.fixture
def fake_home(monkeypatch):
    """Fixed patient list for the start page (no real database access)."""
    monkeypatch.setattr(app_module, "get_patients_with_conditions",
                        lambda: [("Anna", "Hypertension", "Cardiology", 1), ("Ben", None, None, 2)])
    monkeypatch.setattr(app_module, "get_latest_risk",
                        lambda pid: (8.3, "2026-10-07") if pid == 1 else None)


@pytest.fixture
def fake_delete(monkeypatch):
    """Replace delete_patient so tests never delete real patients."""
    deleted = []
    monkeypatch.setattr(app_module, "delete_patient",
                        lambda patient_id: deleted.append(patient_id))
    return deleted


# ---------- bestehende Funktionen ----------

def test_form_page_loads(client):
    assert client.get("/new").status_code == 200


def test_add_patient_shows_confirmation(client, fake_db):
    response = client.post("/add", data={
        "name": "Test Patient", "diagnosis": "Hypertension", "category": "Cardiology", "lang": "de"})
    assert response.status_code == 302
    assert fake_db == ["Test Patient"]
    location = response.headers["Location"]
    assert "/risk?" in location and "patient=99" in location and "new=1" in location and "lang=de" in location


def test_add_patient_empty_fields_rejected(client, fake_db):
    response = client.post("/add", data={"name": "", "diagnosis": "x", "category": "y"})
    assert response.status_code == 400
    assert fake_db == []


def test_delete_via_get_is_not_allowed(client, fake_delete):
    assert client.get("/delete/1").status_code == 405
    assert fake_delete == []


def test_delete_via_post_redirects_and_keeps_language(client, fake_delete):
    response = client.post("/delete/1", data={"lang": "fr"})
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/?lang=fr")
    assert fake_delete == [1]


# ---------- Sprache: ALLES wechselt ----------

def test_all_languages_have_the_same_keys():
    """Fehlt ein Text in einer Sprache, schlaegt dieser Test fehl (statt KeyError im Browser)."""
    for language in ("de", "fr", "ar"):
        assert set(texts[language]) == set(texts["en"]), language
    for eintrag in DIAGNOSIS_TRANSLATIONS.values():
        assert set(eintrag) == {"de", "en", "fr", "ar"}


@pytest.mark.parametrize("lang,patients,none_text,risk_link_text", [
    ("de", "Patienten", "Keine Diagnose", "Herzrisiko berechnen"),
    ("en", "Patients", "No diagnosis", "Calculate heart risk"),
    ("fr", "Patients", "Aucun diagnostic", "Calculer le risque cardiaque"),
    ("ar", "المرضى", "لا يوجد تشخيص", "حساب خطر القلب"),
])
def test_home_is_fully_translated(client, fake_home, lang, patients, none_text, risk_link_text):
    html = client.get(f"/?lang={lang}").get_data(as_text=True)
    assert patients in html and none_text in html and risk_link_text in html
    assert f'lang="{lang}"' in html
    # Links behalten die Sprache
    assert f"/risk?lang={lang}" in html and f"/new?lang={lang}" in html
    assert f"/history/1?lang={lang}" in html


def test_home_translates_diagnosis_and_has_no_german_leftovers_in_english(client, fake_home):
    html = client.get("/?lang=en").get_data(as_text=True)
    assert "Hypertension" in html
    for german_text in ("Hypertonie", "löschen", "Verlauf", "Keine Diagnose", "Herzrisiko"):
        assert german_text not in html


def test_arabic_is_right_to_left(client, fake_home):
    assert 'dir="rtl"' in client.get("/?lang=ar").get_data(as_text=True)
    assert 'dir="ltr"' in client.get("/?lang=en").get_data(as_text=True)


def test_unknown_language_falls_back_to_english(client, fake_home):
    response = client.get("/?lang=xx")
    assert response.status_code == 200
    assert "Patients" in response.get_data(as_text=True)


@pytest.mark.parametrize("lang,expected", [
    ("fr", ["Cholestérol total", "Sexe", "Pression artérielle systolique", "Fumeur", "Plage"]),
    ("en", ["Total cholesterol", "Systolic blood pressure", "Smoker", "Range"]),
    ("ar", ["الكوليسترول الكلي", "ضغط الدم الانقباضي", "مدخّن", "المدى"]),
])
def test_risk_form_labels_follow_language(client, lang, expected):
    html = client.get(f"/risk?lang={lang}").get_data(as_text=True)
    for text in expected:
        assert text in html
    for german_text in ("Gesamtcholesterin", "Raucher", "Zurück", "Blutdruckbehandlung"):
        assert german_text not in html
    assert f'name="lang" value="{lang}"' in html


def test_risk_form_shows_valid_range_from_the_start(client):
    html = client.get("/risk").get_data(as_text=True)
    assert "20–100" in html and 'min="20"' in html and 'max="100"' in html   # HDL
    assert "30–79" in html                                                    # Alter
    assert "100–400" in html and "80–220" in html


def test_new_patient_page_translated(client):
    assert "Nouveau patient" in client.get("/new?lang=fr").get_data(as_text=True)



def test_language_switch_on_risk_page_points_to_get_route(client):
    html = client.get("/risk?lang=en").get_data(as_text=True)
    assert 'href="/risk?lang=fr"' in html


# ---------- Eingaben: logisch ab Anfang, rote Meldung sonst ----------

def post_risk(client, **overrides):
    data = dict(VALID, **overrides)
    return client.post("/calculate_risk", data=data)


def test_valid_input_saves_once_and_shows_result(client, fake_risk):
    response = post_risk(client)
    assert response.status_code == 200
    assert re.search(r"Risiko berechnet: \d+\.\d%", response.get_data(as_text=True))
    assert fake_risk == [1]   # Score gehoert zum gewaehlten Patienten 1


def test_result_is_in_selected_language(client, fake_risk):
    html = post_risk(client, lang="fr").get_data(as_text=True)
    assert "Risque calculé" in html and "Risiko berechnet" not in html


@pytest.mark.parametrize("field,value", [
    ("hdl", "5"), ("hdl", "150"), ("cholesterol", "50"), ("cholesterol", "900"),
    ("blood_pressure", "300"), ("blood_pressure", "20"), ("age", "20"), ("age", "95"),
])
def test_out_of_range_is_rejected_and_nothing_is_saved(client, fake_risk, field, value):
    response = post_risk(client, **{field: value})
    assert response.status_code == 400
    assert fake_risk == []                      # kein Patient ohne Score
    html = response.get_data(as_text=True)
    assert 'class="error"' in html and "muss zwischen" in html
    assert f'value="{value}"' in html          # Eingabe bleibt erhalten


def test_error_message_is_in_selected_language(client, fake_risk):
    html = post_risk(client, hdl="5", lang="fr").get_data(as_text=True)
    assert "doit être compris entre 20 et 100" in html
    html = post_risk(client, hdl="5", lang="ar").get_data(as_text=True)
    assert "بين 20 و100" in html


def test_empty_and_non_numeric_fields_rejected(client, fake_risk):
    assert post_risk(client, hdl="").status_code == 400
    assert post_risk(client, hdl="abc").status_code == 400
    assert post_risk(client, hdl="nan").status_code == 400
    assert post_risk(client, age="55.5").status_code == 400
    assert post_risk(client, patient_id="").status_code == 400
    assert post_risk(client, patient_id="999").status_code == 400   # gibt es nicht
    assert post_risk(client, patient_id="abc").status_code == 400
    assert post_risk(client, sex="x").status_code == 400
    assert fake_risk == []


def test_hdl_must_be_lower_than_total_cholesterol(client, fake_risk):
    response = post_risk(client, cholesterol="100", hdl="100")   # beide im Bereich, aber unlogisch
    assert response.status_code == 400
    assert "HDL muss kleiner" in response.get_data(as_text=True)
    assert fake_risk == []


def test_decimal_comma_is_accepted(client, fake_risk):
    assert post_risk(client, cholesterol="220,5").status_code == 200


def test_error_page_language_switch_uses_get_route(client, fake_risk):
    html = post_risk(client, hdl="5").get_data(as_text=True)
    assert 'href="/risk?lang=en"' in html


# ---------- Kategorie: Auswahl statt Tippen ----------

def test_category_is_a_dropdown_with_all_options(client):
    html = client.get("/new").get_data(as_text=True)
    assert '<select id="category" name="category"' in html
    assert 'type="text" id="category"' not in html
    for k in CATEGORIES:
        assert f'value="{k}"' in html


@pytest.mark.parametrize("lang,expected", [
    ("en", ["Cardiology", "Internal medicine", "Please select"]),
    ("fr", ["Médecine interne", "Gastro-entérologie", "Veuillez choisir"]),
    ("ar", ["أمراض القلب", "الطب النفسي", "يرجى الاختيار"]),
])
def test_category_options_follow_language(client, lang, expected):
    html = client.get(f"/new?lang={lang}").get_data(as_text=True)
    for text in expected:
        assert text in html
    assert "Kardiologie</option>" not in html


def test_every_category_has_all_four_languages():
    for key, names in CATEGORY_TRANSLATIONS.items():
        assert set(names) == {"de", "en", "fr", "ar"}, key


def test_valid_category_is_saved(client, monkeypatch, fake_db):
    saved = []
    monkeypatch.setattr(app_module, "add_condition",
                        lambda pid, diagnosis, category: saved.append(category))
    client.post("/add", data={"name": "A", "diagnosis": "Asthma", "category": "Pulmonology"})
    assert saved == ["Pulmonology"]


@pytest.mark.parametrize("value", ["", "Magic", "<script>"])
def test_category_outside_list_is_rejected(client, fake_db, value):
    response = client.post("/add", data={"name": "A", "diagnosis": "Asthma", "category": value})
    assert response.status_code == 400
    assert fake_db == []
    assert "please make a selection" in response.get_data(as_text=True)


def test_selected_category_stays_after_error(client, fake_db):
    html = client.post("/add", data={"name": "", "diagnosis": "x",
                                             "category": "Oncology"}).get_data(as_text=True)
    assert 'value="Oncology" selected' in html


# ---------- Diagnose: Auswahl + "Andere" ----------

def test_diagnosis_is_a_dropdown_with_other_option(client):
    html = client.get("/new").get_data(as_text=True)
    assert '<select id="diagnosis" name="diagnosis"' in html
    for d in DIAGNOSES:
        assert f'value="{d}"' in html
    assert f'value="{OTHER}"' in html and 'name="diagnosis_free"' in html


@pytest.mark.parametrize("lang,expected", [
    ("en", ["Heart failure", "Stroke", "Other (enter yourself)"]),
    ("fr", ["Insuffisance cardiaque", "Accident vasculaire cérébral (AVC)", "Autre (saisir soi-même)"]),
    ("ar", ["قصور القلب", "السكتة الدماغية", "أخرى (أدخلها بنفسك)"]),
])
def test_diagnosis_options_follow_language(client, lang, expected):
    html = client.get(f"/new?lang={lang}").get_data(as_text=True)
    for text in expected:
        assert text in html


def test_all_dropdown_diagnoses_have_translations():
    for d in DIAGNOSES:
        assert set(DIAGNOSIS_TRANSLATIONS[d]) == {"de", "en", "fr", "ar"}, d


def post_patient(client, **overrides):
    data = {"name": "A", "diagnosis": "Asthma", "category": "Pulmonology"}
    data.update(overrides)
    return client.post("/add", data=data)


def test_listed_diagnosis_is_saved_in_german(client, monkeypatch, fake_db):
    saved = []
    monkeypatch.setattr(app_module, "add_condition",
                        lambda pid, diagnosis, category: saved.append(diagnosis))
    assert post_patient(client, diagnosis="Stroke").status_code == 302
    assert saved == ["Stroke"]


def test_other_diagnosis_uses_free_text(client, monkeypatch, fake_db):
    saved = []
    monkeypatch.setattr(app_module, "add_condition",
                        lambda pid, diagnosis, category: saved.append(diagnosis))
    response = post_patient(client, diagnosis=OTHER, diagnosis_free="  Gout ")
    assert response.status_code == 302 and saved == ["Gout"]


def test_other_without_free_text_is_rejected(client, fake_db):
    response = post_patient(client, diagnosis=OTHER, diagnosis_free="  ")
    assert response.status_code == 400 and fake_db == []
    assert "required field" in response.get_data(as_text=True)


def test_free_text_is_ignored_when_a_listed_diagnosis_is_chosen(client, monkeypatch, fake_db):
    saved = []
    monkeypatch.setattr(app_module, "add_condition",
                        lambda pid, diagnosis, category: saved.append(diagnosis))
    post_patient(client, diagnosis="Asthma", diagnosis_free="irgendwas")
    assert saved == ["Asthma"]


@pytest.mark.parametrize("value", ["", "Magic", "<script>"])
def test_diagnosis_outside_list_is_rejected(client, fake_db, value):
    response = post_patient(client, diagnosis=value)
    assert response.status_code == 400 and fake_db == []


def test_diagnosis_choice_stays_after_error(client, fake_db):
    html = post_patient(client, name="", diagnosis="COPD").get_data(as_text=True)
    assert 'value="COPD" selected' in html


def test_free_diagnosis_is_translated_when_it_matches_the_dictionary(client, fake_home):
    # Eigene Eingabe "hypertonie" (klein geschrieben) wird beim Anzeigen trotzdem uebersetzt
    from translations import translate_diagnosis
    assert translate_diagnosis("hypertonie", "fr") == "Hypertension artérielle"


# ---------- Risiko-Formular: Patient aus der SavedList choose ----------

def test_patient_is_a_dropdown_with_existing_names(client):
    html = client.get("/risk").get_data(as_text=True)
    assert '<select id="patient_id" name="patient_id"' in html
    assert 'name="name"' not in html and 'id="name"' not in html     # kein Tippfeld mehr
    assert ">Anna</option>" in html and ">Demo</option>" in html
    assert html.index(">Anna<") < html.index(">Demo<")


def test_patient_can_be_preselected_by_link(client):
    html = client.get("/risk?patient=1").get_data(as_text=True)
    assert 'value="1" selected' in html


def test_duplicate_names_get_an_id_suffix(client, monkeypatch):
    monkeypatch.setattr(app_module, "get_visible_patients", lambda: [(1, "Omar"), (3, "Omar"), (2, "Anna")])
    html = client.get("/risk").get_data(as_text=True)
    assert "Omar (#1)" in html and "Omar (#3)" in html and ">Anna</option>" in html


def test_without_patients_the_form_asks_to_add_one_first(client, monkeypatch):
    monkeypatch.setattr(app_module, "get_visible_patients", lambda: [])
    html = client.get("/risk?lang=fr").get_data(as_text=True)
    assert "Aucun patient pour l'instant" in html or "Aucun patient pour l&#39;instant" in html
    assert 'id="risk-form"' not in html and "/new?lang=fr" in html


def test_score_is_saved_for_chosen_patient_and_no_new_patient_is_created(client, fake_risk, monkeypatch):
    created = []
    monkeypatch.setattr(app_module, "add_patient", lambda n, d: created.append(n) or 99)
    response = post_risk(client, patient_id="2")
    assert response.status_code == 200 and fake_risk == [2] and created == []
    assert "Anna: Risiko berechnet" in response.get_data(as_text=True)


def test_patient_label_follows_language(client):
    assert "المريض" in client.get("/risk?lang=ar").get_data(as_text=True)
    assert "Veuillez choisir" in client.get("/risk?lang=fr").get_data(as_text=True)


# ---------- Mehrere Scores am selben Tag: der zuletzt gespeicherte gilt als neuester ----------

def test_newest_risk_wins_when_two_scores_are_saved_on_the_same_day(tmp_path, monkeypatch):
    import fhir_db
    monkeypatch.chdir(tmp_path)                       # own_patients Test-Datenbank, nicht die echte
    fhir_db.create_patients_table(); fhir_db.create_risk_scores_table()
    pid = fhir_db.add_patient("Test", "x")
    fhir_db.save_risk(pid, 55, 220, 50, 140, 0, 0, 8.3)
    fhir_db.save_risk(pid, 56, 230, 50, 140, 0, 0, 9.4)
    assert fhir_db.get_latest_risk(pid)[0] == 9.4
    assert [r[0] for r in fhir_db.get_all_risks(pid)] == [9.4, 8.3]


# ---------- Hinweise zum Ergebnis (regelbasiert) ----------

from advice import risk_category, get_tips


@pytest.mark.parametrize("percent,expected", [
    (0.0, "low"), (9.9, "low"), (10.0, "medium"), (20.0, "medium"), (20.1, "high"), (45.0, "high"),
])
def test_risk_categories_follow_atp3_thresholds(percent, expected):
    assert risk_category(percent) == expected


def values(**o):
    base = {"sex": "m", "cholesterol": 200.0, "hdl": 55.0, "blood_pressure": 120.0, "smoker": False}
    base.update(o)
    return base


def test_healthy_values_only_give_basic_tips():
    assert get_tips(values(), "low") == ["tip_low", "tip_exercise", "tip_nutrition"]


def test_each_risk_factor_adds_its_own_tip():
    tips = get_tips(values(smoker=True, blood_pressure=150.0, cholesterol=250.0, hdl=35.0), "high")
    assert tips[0] == "tip_high"
    for k in ("tip_smoking", "tip_blood_pressure", "tip_cholesterol", "tip_hdl"):
        assert k in tips


def test_hdl_threshold_differs_by_sex():
    assert "tip_hdl" not in get_tips(values(sex="m", hdl=45.0), "low")   # Mann: ab 40 ok
    assert "tip_hdl" in get_tips(values(sex="f", hdl=45.0), "low")       # Frau: unter 50 low


def test_result_page_shows_category_tips_and_emergency_note(client, fake_risk):
    html = post_risk(client, cholesterol="260", blood_pressure="150", smoking="current", cigarettes="15").get_data(as_text=True)
    assert 'class="badge badge-' in html and "Allgemeine Hinweise" in html
    assert "Rauchen" in html and "Blutdruck" in html and "cholesterin" in html
    assert "Notruf 112" in html and "keine ärztliche Beratung" in html


def test_result_page_tips_follow_language(client, fake_risk):
    html = post_risk(client, lang="fr", smoking="current", cigarettes="15").get_data(as_text=True)
    assert "Conseils généraux" in html and "appelez immédiatement le 112" in html
    assert "Allgemeine Hinweise" not in html
    html = post_risk(client, lang="ar", smoking="current", cigarettes="15").get_data(as_text=True)
    assert "نصائح عامة" in html and "112" in html


def test_new_patient_lands_on_risk_page_with_banner_and_preselection(client, monkeypatch, fake_db):
    response = post_patient(client, lang="fr")
    assert "lang=fr" in response.headers["Location"]
    monkeypatch.setattr(app_module, "get_visible_patients", lambda: [(99, "Neu"), (1, "Demo")])
    html = client.get(response.headers["Location"]).get_data(as_text=True)
    assert "Calculez maintenant le risque cardiaque" in html
    assert re.search(r'<option value="99"\s+selected', html)


def test_risk_page_without_new_flag_has_no_banner(client):
    assert "success-box" not in client.get("/risk").get_data(as_text=True).split("</style>")[-1]


def test_smoking_select_and_cigarette_box_present(client):
    html = client.get("/risk").get_data(as_text=True)
    for value in ("never", "former", "current"):
        assert f'value="{value}"' in html
    assert "Cigarettes per day (average)" in html and 'id="cigarettes-box"' in html


def test_current_smoker_needs_cigarettes(client, fake_risk):
    r = post_risk(client, smoking="current", cigarettes="")
    assert r.status_code == 400 and fake_risk == []
    for bad in ("0", "101", "abc"):
        assert post_risk(client, smoking="current", cigarettes=bad).status_code == 400


def test_smoking_status_required(client, fake_risk):
    data = dict(VALID); del data["smoking"]
    assert client.post("/calculate_risk", data=data).status_code == 400


def test_non_smokers_store_no_cigarettes(client, fake_risk):
    for status in ("never", "former"):
        post_risk(client, smoking=status, cigarettes="30")
    assert [d[1]["cigarettes_per_day"] for d in fake_risk.details] == [None, None]


def test_cigarettes_saved_and_shown_on_result(client, fake_risk):
    html = post_risk(client, smoking="current", cigarettes="15").get_data(as_text=True)
    assert fake_risk.details[0][1]["cigarettes_per_day"] == 15
    assert "Rauchstatus: Raucher, 15 Zigaretten pro Tag" in html


def test_smoking_line_follows_language(client, fake_risk):
    html = post_risk(client, lang="en", smoking="current", cigarettes="5").get_data(as_text=True)
    assert "5 cigarettes per day" in html


def _old_german_database(path):
    """Build a database exactly like the German version of MediLink created it."""
    import sqlite3
    con = sqlite3.connect(path)
    con.executescript("""
        CREATE TABLE patienten (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, diagnose TEXT);
        CREATE TABLE conditions (id INTEGER PRIMARY KEY AUTOINCREMENT, patient_id INTEGER, code_text TEXT,
            category_text TEXT, clinical_status TEXT);
        CREATE TABLE risk_scores (id INTEGER PRIMARY KEY AUTOINCREMENT, patient_id INTEGER, datum TEXT,
            alter_wert INTEGER, cholesterin REAL, hdl REAL, blutdruck REAL, raucher INTEGER, behandelt INTEGER,
            risiko_prozent REAL, zigaretten_pro_tag INTEGER);
        CREATE TABLE besuche (token TEXT PRIMARY KEY, erster_besuch TEXT);
        INSERT INTO patienten VALUES (5, 'Anna', 'siehe conditions');
        INSERT INTO conditions VALUES (3, 5, 'Hypertonie', 'Kardiologie', 'active');
        INSERT INTO risk_scores VALUES (9, 5, '2026-10-07', 55, 220.0, 50.0, 140.0, 1, 0, 8.3, 15);
        INSERT INTO besuche VALUES ('abc', '2026-10-07T10:00:00');
    """)
    con.commit()
    con.close()


def test_german_database_is_migrated_to_english_schema(tmp_path, monkeypatch):
    import sqlite3, fhir_db
    monkeypatch.chdir(tmp_path)
    _old_german_database("patients.db")
    fhir_db.create_all_tables()
    con = sqlite3.connect("patients.db")
    tables = {r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    assert "patienten" not in tables and "besuche" not in tables
    assert con.execute("SELECT id, name, diagnosis FROM patients").fetchall() == [(5, "Anna", "see conditions")]
    assert con.execute("SELECT code_text, category_text FROM conditions").fetchall() == [("Hypertension", "Cardiology")]
    assert con.execute("SELECT id, age, systolic_bp, cigarettes_per_day FROM risk_scores").fetchall() == [(9, 55, 140.0, 15)]
    assert con.execute("SELECT token FROM visits").fetchall() == [("abc",)]
    con.close()
    # New rows continue after the copied ids, and a second start-up changes nothing.
    fhir_db.create_all_tables()
    assert fhir_db.add_patient("Ben", "x") == 6
    assert fhir_db.get_patients_with_conditions()[0][:3] == ("Anna", "Hypertension", "Cardiology")


def test_migration_handles_old_risk_table_without_cigarette_column(tmp_path, monkeypatch):
    import sqlite3, fhir_db
    monkeypatch.chdir(tmp_path)
    con = sqlite3.connect("patients.db")
    con.executescript("""
        CREATE TABLE patienten (id INTEGER PRIMARY KEY, name TEXT, diagnose TEXT);
        CREATE TABLE risk_scores (id INTEGER PRIMARY KEY, patient_id INTEGER, datum TEXT, alter_wert INTEGER,
            cholesterin REAL, hdl REAL, blutdruck REAL, raucher INTEGER, behandelt INTEGER, risiko_prozent REAL);
        INSERT INTO patienten VALUES (1, 'Zoe', 'Asthma');
        INSERT INTO risk_scores VALUES (1, 1, '2026-01-01', 50, 200.0, 50.0, 120.0, 0, 0, 5.0);
    """)
    con.commit(); con.close()
    fhir_db.create_all_tables()
    assert fhir_db.get_latest_risk(1)[0] == 5.0


def test_fresh_database_needs_no_migration(tmp_path, monkeypatch):
    import fhir_db
    monkeypatch.chdir(tmp_path)
    assert fhir_db.migrate_german_schema() is False
    fhir_db.create_all_tables()
    assert fhir_db.add_patient("A", "b") == 1


# ---------- Animation beim Betreten ----------

def test_home_has_intro_animation_with_title_in_selected_language(client, fake_home):
    html = client.get("/?lang=fr").get_data(as_text=True)
    assert 'id="intro"' in html and "MédiLien" in html
    assert "prefers-reduced-motion" in html         # respektiert die Systemeinstellung


def test_other_pages_have_no_intro(client, fake_home):
    assert 'id="intro"' not in client.get("/risk").get_data(as_text=True)
    assert 'id="intro"' not in client.get("/new").get_data(as_text=True)


# ---------- Anonymitaet, Statistik, Besucherzaehler ----------

@pytest.fixture
def all_data(monkeypatch):
    """Zwei fremde Patienten + ein Eintrag; Namen sollen fuer Fremde unsichtbar bleiben."""
    monkeypatch.setattr(app_module, "get_patients_with_conditions",
                        lambda: [("Geheim Gerda", "Asthma", "Pulmonology", 7), ("Eigen Egon", "Hypertension", "Cardiology", 8)])
    monkeypatch.setattr(app_module, "get_latest_risk", lambda pid: (8.3, "2026-10-07"))
    monkeypatch.setattr(app_module, "get_all_patients", lambda: [(8, "Eigen Egon"), (7, "Geheim Gerda")])
    monkeypatch.setattr(app_module, "get_visible_patients", _real_list)
    monkeypatch.setattr(app_module, "get_statistics",
                        lambda: {"visitors": 12, "patients": 2, "calculations": 1, "average": 8.3})
    monkeypatch.setattr(app_module, "get_all_entries",
                        lambda: [(5, 7, "2026-10-07", 55, 220.0, 50.0, 140.0, 1, 15, 8.3, "Geheim Gerda")])


def test_stranger_sees_no_other_patients_at_all(visitor, all_data):
    html = visitor.get("/").get_data(as_text=True)
    assert "Geheim Gerda" not in html and "Eigen Egon" not in html
    assert "Anonymous" not in html and "Hypertension" not in html and "Asthma" not in html
    assert "/history/7" not in html and "/delete/7" not in html
    assert "private and not shown here" in html


def test_admin_sees_all_patients_on_home(client, all_data):
    html = client.get("/").get_data(as_text=True)
    assert "Geheim Gerda" in html and "Eigen Egon" in html
    assert "private and not shown here" not in html


def test_visitor_sees_own_patient_by_name(visitor, all_data):
    with visitor.session_transaction() as s:
        s["own_patients"] = [8]
    html = visitor.get("/").get_data(as_text=True)
    assert "Eigen Egon" in html and "/history/8" in html and "Geheim Gerda" not in html


def test_stranger_cannot_delete_or_open_history_of_others(visitor, all_data, fake_delete):
    assert visitor.post("/delete/7").status_code == 403 and fake_delete == []
    assert visitor.get("/history/7").status_code == 404


def test_risk_form_lists_only_own_patients_for_strangers(visitor, all_data):
    html = visitor.get("/risk").get_data(as_text=True)
    assert "Geheim Gerda" not in html
    with visitor.session_transaction() as s:
        s["own_patients"] = [8]
    assert "Eigen Egon" in visitor.get("/risk").get_data(as_text=True)


def test_stranger_cannot_calculate_for_foreign_patient(visitor, all_data, fake_risk):
    r = visitor.post("/calculate_risk", data=dict(VALID, patient_id="7"))
    assert r.status_code == 400 and fake_risk == []


def test_new_patient_becomes_own(visitor, fake_db):
    visitor.post("/add", data={"name": "A", "diagnosis": "Asthma", "category": "Pulmonology"})
    with visitor.session_transaction() as s:
        assert s["own_patients"] == [99]


def test_statistics_page_is_anonymous_for_strangers(visitor, all_data):
    html = visitor.get("/statistics").get_data(as_text=True)
    assert "Geheim Gerda" not in html and "220" not in html and "140" not in html
    assert ">12<" in html and "8.3" in html and "Statistics (anonymous)" in html


def test_statistics_lists_only_own_entries_for_visitor(visitor, all_data):
    with visitor.session_transaction() as sess:
        sess["own_patients"] = [7]
    html = visitor.get("/statistics").get_data(as_text=True)
    assert "8.3%" in html and "your entry" in html          # own entry is listed
    assert "Geheim Gerda" not in html and "220" not in html  # but still no names and no raw values


def test_statistics_hides_foreign_entries(visitor, all_data):
    html = visitor.get("/statistics").get_data(as_text=True)
    assert "8.3%" not in html                                 # entry of patient 7 belongs to somebody else
    assert "No calculations yet." in html


def test_statistics_page_shows_names_and_values_to_admin(client, all_data):
    html = client.get("/statistics").get_data(as_text=True)
    assert "Geheim Gerda" in html and "220" in html and "Admin view" in html


def test_statistics_follows_language(visitor, all_data):
    assert "Statistiques (anonymes)" in visitor.get("/statistics?lang=fr").get_data(as_text=True)
    assert "الإحصائيات" in visitor.get("/statistics?lang=ar").get_data(as_text=True)


def test_visit_is_counted_once_per_browser(fake_visits, fake_home):
    c = app.test_client()
    c.get("/"); c.get("/new"); c.get("/")
    assert len(fake_visits) == 1


def test_admin_login_needs_correct_key(monkeypatch, all_data):
    monkeypatch.setenv("ADMIN_KEY", "geheim123")
    c = app.test_client()
    assert c.get("/admin").status_code == 404
    assert c.get("/admin?key=falsch").status_code == 404
    assert c.get("/admin?key=geheim123").status_code == 302
    assert "Geheim Gerda" in c.get("/statistics").get_data(as_text=True)


def test_admin_disabled_without_env_key(monkeypatch):
    monkeypatch.delenv("ADMIN_KEY", raising=False)
    assert app.test_client().get("/admin?key=").status_code == 404


def test_statistics_db_functions(tmp_path, monkeypatch):
    import fhir_db
    monkeypatch.chdir(tmp_path)
    for f in (fhir_db.create_patients_table, fhir_db.create_conditions_table,
              fhir_db.create_risk_scores_table, fhir_db.create_visits_table):
        f()
    fhir_db.count_visit("a"); fhir_db.count_visit("a"); fhir_db.count_visit("b")
    pid = fhir_db.add_patient("X", "y")
    fhir_db.save_risk(pid, 50, 200, 50, 120, 0, 0, 10.0)
    fhir_db.save_risk(pid, 51, 200, 50, 120, 0, 0, 20.0)
    st = fhir_db.get_statistics()
    assert st == {"visitors": 2, "patients": 1, "calculations": 2, "average": 15.0}
    assert len(fhir_db.get_all_entries()) == 2
    fhir_db.delete_patient(pid)
    assert fhir_db.get_statistics()["calculations"] == 0


# ---------- Werte-Erklaerung (Skalen) ----------

def test_risk_page_has_value_guide_with_three_scales(client):
    html = client.get("/risk").get_data(as_text=True)
    assert html.count('class="scale"') == 3
    for field in ("cholesterol", "hdl", "blood_pressure"):
        assert f'data-field="{field}"' in html
    assert "Understand the values" in html and "Example" in html


@pytest.mark.parametrize("lang,expected", [
    ("en", "Understand the values"), ("fr", "Comprendre les valeurs"), ("ar", "فهم القيم")])
def test_value_guide_follows_language(client, lang, expected):
    html = client.get(f"/risk?lang={lang}").get_data(as_text=True)
    assert expected in html and "Werte verstehen" not in html


def test_value_guide_zone_widths_add_up_to_100(client):
    html = client.get("/risk").get_data(as_text=True)
    widths = [float(w) for w in re.findall(r'class="zone zone-\w+" style="width: ([\d.]+)%', html)]
    assert len(widths) == 9
    for i in range(0, 9, 3):
        assert abs(sum(widths[i:i + 3]) - 100) < 0.1


# ---------- KI-Assistent (Claude API wird immer nur nachgeahmt, never echt aufgerufen) ----------

import assistant


class _FakeAnswer:
    def __init__(self, text):
        self.content = [type("B", (), {"type": "text", "text": text})()]


@pytest.fixture
def ai(monkeypatch):
    """Aktiviert den Assistenten mit einer gefaelschten API und merkt sich die Aufrufe."""
    calls = []
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    monkeypatch.setattr(assistant, "_daily_counter", {})

    class Messages:
        def create(self, **kwargs):
            calls.append(kwargs)
            return _FakeAnswer("HDL ist das gute Cholesterin.")
    monkeypatch.setattr(assistant, "_client", lambda: type("C", (), {"messages": Messages()})())
    return calls


def chat(client, text="Was ist HDL?", lang="de", **extra):
    return client.post(f"/chat?lang={lang}", json=dict({"message": text}, **extra))


def test_without_api_key_the_free_helper_answers(client, monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    r = chat(client, "Was bedeutet HDL?")
    assert r.status_code == 200 and "gute" in r.get_json()["answer"]


def test_result_page_always_shows_assistant_box(client, monkeypatch, fake_risk):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    html = client.post("/calculate_risk", data=VALID).get_data(as_text=True)
    assert 'id="chat-form"' in html and "Hilfe-Assistent" in html and "keine KI" in html
    assert html.count('class="chip"') == 7 and "Was bedeutet HDL?" in html


def test_chat_box_shown_on_result_page_when_enabled(client, ai, fake_risk):
    html = client.post("/calculate_risk", data=VALID).get_data(as_text=True)
    assert 'id="chat-form"' in html and "KI-Assistent" in html and "Anthropic" in html


def test_chat_answers_and_calls_api_with_safety_settings(client, ai):
    r = chat(client)
    assert r.status_code == 200 and r.get_json()["answer"] == "HDL ist das gute Cholesterin."
    call = ai[0]
    assert call["max_tokens"] <= 400 and "No diagnoses" in call["system"]
    assert call["messages"][-1] == {"role": "user", "content": "Was ist HDL?"}


def test_chat_sends_result_values_but_no_name(client, ai, fake_risk):
    client.post("/calculate_risk", data=dict(VALID, cholesterol="233"))
    chat(client)
    system = ai[0]["system"]
    assert "cholesterol=233.0" in system and "Demo" not in system and "Anna" not in system


def test_chat_language_in_system_prompt(client, ai):
    chat(client, lang="fr")
    assert "Français" in ai[0]["system"]


def test_chat_emergency_keywords_skip_ai(client, ai):
    r = chat(client, "Ich habe starke Brustschmerzen")
    assert "112" in r.get_json()["answer"] and ai == []
    assert "112" in chat(client, "douleur thoracique", lang="fr").get_json()["answer"]


def test_chat_rejects_empty_and_too_long(client, ai):
    assert chat(client, "   ").status_code == 400
    assert chat(client, "x" * 501).status_code == 400 and ai == []


def test_chat_limit_per_visitor(client, ai):
    for _ in range(assistant.LIMIT_PER_VISITOR):
        assert chat(client).status_code == 200
    assert chat(client).status_code == 429


def test_chat_daily_limit(client, ai, monkeypatch):
    monkeypatch.setattr(assistant, "DAILY_LIMIT", 2)
    assert chat(client).status_code == 200 and chat(client).status_code == 200
    assert chat(client).status_code == 429


def test_chat_api_failure_gives_friendly_error(client, ai, monkeypatch):
    class Broken:
        def create(self, **kw):
            raise RuntimeError("boom")
    monkeypatch.setattr(assistant, "_client", lambda: type("C", (), {"messages": Broken()})())
    r = chat(client)
    assert r.status_code == 503 and "nicht erreichbar" in r.get_json()["error"]


def test_history_is_sanitised():
    clean = assistant.sanitize_history([
        {"role": "assistant", "content": "alt"}, {"role": "system", "content": "böse"},
        {"role": "user", "content": "hi"}, {"role": "assistant", "content": 5}, "müll"])
    assert clean == [{"role": "user", "content": "hi"}]


def test_chat_translations_exist_in_all_languages():
    for lang in ("de", "en", "fr", "ar"):
        for k in ("chat_title", "chat_hint", "chat_send", "chat_error", "chat_limit"):
            assert texts[lang][k]


def test_risk_page_teases_assistant_only_when_enabled(client, ai):
    assert "After the calculation" in client.get("/risk").get_data(as_text=True)


def test_risk_page_teaser_also_without_key(client, monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    assert "After the calculation" in client.get("/risk").get_data(as_text=True)


# ---------- kostenloser Hilfe-Assistent (faq.py) ----------

import faq


@pytest.mark.parametrize("lang", ["de", "en", "fr", "ar"])
def test_every_suggestion_chip_gets_its_own_topic(lang):
    result = {"category": "medium", "risk_percent": 12.3}
    expected = {t["label"][lang]: t["answer"][lang] for t in faq.TOPICS}
    for question in faq.suggestions(lang)[1:]:
        assert faq.answer(question, lang, result) == expected[question]
    answer = faq.answer(faq.suggestions(lang)[0], lang, result)
    assert "12.3" in answer


def test_faq_result_question_without_result():
    assert "Zuerst" in faq.answer("Was bedeutet mein Ergebnis?", "de")


def test_faq_unknown_question_lists_topics():
    answer = faq.answer("Wie wird das Wetter?", "de")
    assert "keine Antwort" in answer and "Gesamtcholesterin" in answer


def test_faq_topics_complete_in_all_languages():
    for topic in faq.ALL_TOPICS:
        for lang in ("de", "en", "fr", "ar"):
            assert topic["label"][lang] and topic["answer"][lang]


def test_faq_uses_result_from_session(client, monkeypatch, fake_risk):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    client.post("/calculate_risk", data=VALID)
    answer = chat(client, "Was bedeutet mein Ergebnis?").get_json()["answer"]
    assert "10-Jahres-Risiko" in answer and "%" in answer


def test_faq_emergency_still_wins(client, monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    assert "112" in chat(client, "Brustschmerzen und was ist HDL").get_json()["answer"]


# ---------- Datenbank-Schicht (SQLite lokal, PostgreSQL mit DATABASE_URL) ----------

import db


def test_tests_never_use_a_real_database_url():
    import os
    assert "DATABASE_URL" not in os.environ and not db.postgres_enabled()


def test_db_switches_to_postgres_with_database_url(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgres://u:p@host/dbname")
    assert db.postgres_enabled()
    assert db._pg_url() == "postgresql://u:p@host/dbname"      # alte Schreibweise wird angepasst
    assert db._sql("SELECT * FROM t WHERE a = ? AND b = ?") == "SELECT * FROM t WHERE a = %s AND b = %s"
    assert db.id_column() == "SERIAL PRIMARY KEY"


def test_db_uses_sqlite_by_default():
    assert db._sql("SELECT ?") == "SELECT ?" and db.id_column() == "INTEGER PRIMARY KEY"


def test_db_functions_roundtrip_with_sqlite(tmp_path, monkeypatch):
    import fhir_db
    monkeypatch.chdir(tmp_path)
    fhir_db.create_patients_table(); fhir_db.create_conditions_table(); fhir_db.create_risk_scores_table()
    pid = fhir_db.add_patient("Zoe", "x"); fhir_db.add_patient("anna", "x")
    fhir_db.add_condition(pid, "Asthma", "Pulmonology")
    fhir_db.save_risk(pid, 55, 220.0, 50.0, 140.0, True, False, 8.3, 15)
    assert [n for _, n in fhir_db.get_all_patients()] == ["anna", "Zoe"]      # alphabetisch, ohne Gross/Klein
    assert fhir_db.get_patients_with_conditions()[0][:3] == ("Zoe", "Asthma", "Pulmonology")
    assert fhir_db.get_latest_risk(pid)[0] == 8.3
    fhir_db.delete_patient(pid)
    assert [n for _, n in fhir_db.get_all_patients()] == ["anna"]


# ---------- health check for the waiting page ----------

def test_health_route_answers_ok_and_is_not_counted(fake_visits):
    c = app.test_client()
    response = c.get("/health")
    assert response.status_code == 200 and response.get_data(as_text=True) == "ok"
    assert response.headers["Access-Control-Allow-Origin"] == "*"
    assert fake_visits == []                       # pings from the waiting page are no visitors
    with c.session_transaction() as sess:
        assert "visitor" not in sess
