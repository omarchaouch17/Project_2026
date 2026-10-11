import hmac
import os
import uuid
from datetime import timedelta

from flask import Flask, request, render_template, redirect, url_for, session, abort

from fhir_db import (
    create_all_tables, add_patient, add_condition, delete_patient,
    save_risk, get_latest_risk, get_all_risks,
    count_visit, get_statistics, get_all_entries,
    get_patients_with_conditions, get_all_patients
)
from translations import (
    texts, translate_diagnosis, category_name, CATEGORIES, DIAGNOSES, OTHER
)
from risk import framingham
from advice import risk_category, get_tips
import assistant
import faq
from validation import (
    RISK_FIELDS, validate_risk, validate_patient
)

DEFAULT_LANGUAGE = "en"
LANGUAGES = ["en", "de", "fr", "ar"]

app = Flask(__name__)
# On Render set SECRET_KEY and ADMIN_KEY as environment variables. Without ADMIN_KEY there is no admin access.
app.secret_key = os.environ.get("SECRET_KEY", "medilink-for-local-tests-only")
app.config.update(SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE="Lax",
                  PERMANENT_SESSION_LIFETIME=timedelta(days=365))
app.jinja_env.globals.update(category_name=category_name,
                             diagnosis_name=translate_diagnosis, OTHER=OTHER)

# Create the tables at start-up (important on Render: there is no ready-made database there).
# Data saved by the old German version is migrated automatically.
create_all_tables()


def current_language():
    """Language from ?lang=... (GET) or the hidden form field (POST); unknown -> English."""
    language = request.values.get("lang", DEFAULT_LANGUAGE)
    return language if language in texts else DEFAULT_LANGUAGE


def is_admin():
    return bool(session.get("admin"))


def own_ids():
    return set(session.get("own_patients", []))


def can_see(patient_id):
    """Own patients (created in this browser) and the admin may see names and history."""
    return is_admin() or patient_id in own_ids()


def remember_patient(patient_id):
    own = session.get("own_patients", [])
    own.append(patient_id)
    session["own_patients"] = own[-200:]
    session.permanent = True


@app.before_request
def count_visitor():
    """Every browser is counted once - only through a random token, without an IP address."""
    if request.method == "GET" and request.endpoint not in (None, "static", "health") and "visitor" not in session:
        session["visitor"] = uuid.uuid4().hex
        session.permanent = True
        count_visit(session["visitor"])


@app.context_processor
def template_globals():
    """t, lang, direction and title are available automatically in EVERY template."""
    language = current_language()
    return {
        "t": texts[language],
        "lang": language,
        "direction": "rtl" if language == "ar" else "ltr",
        "title": texts[language]["title"],
        "languages": LANGUAGES,
        "language_path": request.path,
        "show_languages": True,
    }


@app.route("/")
def home():
    language = current_language()
    t = texts[language]

    grouped = {}
    others = False
    for name, diagnosis, category, patient_id in get_patients_with_conditions():
        if not can_see(patient_id):      # other visitors' patients are never shown, not even anonymously
            others = True
            continue
        if diagnosis is None:
            shown = t["no_diagnosis"]
        else:
            shown = translate_diagnosis(diagnosis, language)

        if patient_id not in grouped:
            grouped[patient_id] = {
                "name": name,
                "can_view": True,
                "diagnoses": [],
                "risk": get_latest_risk(patient_id)
            }
        grouped[patient_id]["diagnoses"].append(shown)

    return render_template("home.html", patients=grouped, others=others and not is_admin())


@app.route("/health")
def health():
    """Tiny answer for the waiting page (wake-up ping). Not counted as a visit."""
    response = app.response_class("ok", mimetype="text/plain")
    response.headers["Access-Control-Allow-Origin"] = "*"      # lets the static waiting page read the answer
    response.headers["Cache-Control"] = "no-store"
    return response


@app.route("/new")
def new_patient_form():
    return render_template("new.html", values={}, errors={}, categories=CATEGORIES,
                           diagnoses=DIAGNOSES)


@app.route("/add", methods=["POST"])
def create_patient():
    t = texts[current_language()]
    values, errors = validate_patient(request.form, t)
    if errors:
        return render_template("new.html", values=values, errors=errors,
                               categories=CATEGORIES, diagnoses=DIAGNOSES,
                               language_path="/new"), 400

    patient_id = add_patient(values["name"], "see conditions")
    add_condition(patient_id, values["diagnosis"], values["category"])

    remember_patient(patient_id)
    # Straight on to the score calculation, the new patient is already selected
    return redirect(url_for("risk_form", patient=patient_id, new=1, lang=current_language()))


@app.route("/delete/<int:patient_id>", methods=["POST"])
def remove_patient(patient_id):
    if not can_see(patient_id):
        abort(403)
    delete_patient(patient_id)
    return redirect(url_for("home", lang=current_language()))


def get_visible_patients():
    """Only patients this visitor may see (own ones, or all for the admin)."""
    return [(pid, name) for pid, name in get_all_patients() if can_see(pid)]


def patient_choices():
    """Entries for the select list; for identical names the ID is appended."""
    visible = get_visible_patients()
    frequency = {}
    for _, name in visible:
        frequency[name] = frequency.get(name, 0) + 1
    return [(pid, f"{name} (#{pid})" if frequency[name] > 1 else name) for pid, name in visible]


def smoking_line(values, t):
    """e.g. 'Smoking status: Current smoker, 15 cigarettes per day' for the result page."""
    line = f"{t['smoking']}: {t['smoking_' + values['smoking']]}"
    if values["cigarettes"]:
        line += f", {values['cigarettes']} {t['cigarettes_short']}"
    return line


def _risk_page(values, errors, status=200, just_saved=False):
    """Render the risk form (empty, or with the input and red messages)."""
    return render_template("risk.html", values=values, errors=errors, fields=RISK_FIELDS,
                           patients=patient_choices(), just_saved=just_saved,
                           chat_enabled=assistant.chat_enabled(), language_path="/risk"), status


@app.route("/risk")
def risk_form():
    # /risk?patient=3 pre-selects the patient
    return _risk_page({"patient_id": request.args.get("patient", "")}, {},
                      just_saved=bool(request.args.get("new")))


@app.route("/calculate_risk", methods=["POST"])
def calculate_risk():
    t = texts[current_language()]
    values, errors = validate_risk(request.form, t, get_visible_patients())
    if errors:
        return _risk_page(request.form, errors, 400)

    try:
        risk_percent = framingham(
            values["sex"], values["age"], values["cholesterol"], values["hdl"],
            values["blood_pressure"], values["treated"], values["smoker"]
        )
    except ValueError as e:  # safety net in case risk.py becomes stricter than validation.py
        return _risk_page(request.form, {"general": str(e)}, 400)

    # The score belongs to the chosen, already existing patient (no new patient is created here)
    save_risk(values["patient_id"], values["age"], values["cholesterol"], values["hdl"],
              values["blood_pressure"], values["smoker"], values["treated"], risk_percent,
              cigarettes_per_day=values["cigarettes"])

    category = risk_category(risk_percent)
    # Remember it for the assistant (without the name)
    session["result"] = {"sex": values["sex"], "age": values["age"], "cholesterol": values["cholesterol"],
                         "hdl": values["hdl"], "blood_pressure": values["blood_pressure"],
                         "smoking": values["smoking"], "cigarettes": values["cigarettes"],
                         "risk_percent": risk_percent, "category": category}
    return render_template("result.html", chat_enabled=assistant.chat_enabled(),
                           suggestions=faq.suggestions(current_language()),
                           message=f"{values['name']}: " + t["result"].format(p=risk_percent),
                           smoking_line=smoking_line(values, t),
                           category=category, tips=get_tips(values, category),
                           show_languages=False)


@app.route("/history/<int:patient_id>")
def history(patient_id):
    if not can_see(patient_id):
        abort(404)
    return render_template("history.html", risks=get_all_risks(patient_id),
                           patient_id=patient_id)


@app.route("/chat", methods=["POST"])
def chat():
    """Assistant: JSON {message, history}; response JSON {answer} or {error}."""
    t = texts[current_language()]
    data = request.get_json(silent=True) or {}
    message = data.get("message")
    if not isinstance(message, str) or not message.strip():
        return {"error": t["err_required"].format(label="")}, 400
    message = message.strip()
    if len(message) > assistant.MAX_MESSAGE:
        return {"error": t["chat_too_long"]}, 400
    if assistant.is_emergency(message):   # emergency: fixed answer, no AI
        return {"answer": t["emergency"]}
    if not assistant.chat_enabled():      # free default: rule-based help assistant
        return {"answer": faq.answer(message, current_language(), session.get("result"))}
    if session.get("chat_count", 0) >= assistant.LIMIT_PER_VISITOR or assistant.daily_limit_reached():
        return {"error": t["chat_limit"]}, 429
    session["chat_count"] = session.get("chat_count", 0) + 1
    try:
        answer = assistant.ask_assistant(message, data.get("history"), current_language(),
                                         session.get("result"))
    except assistant.AssistantError:
        return {"error": t["chat_error"]}, 503
    return {"answer": answer}


@app.route("/admin")
def admin():
    """/admin?key=... unlocks the admin view for this browser (key = ADMIN_KEY)."""
    expected = os.environ.get("ADMIN_KEY", "")
    if not expected or not hmac.compare_digest(request.args.get("key", ""), expected):
        abort(404)
    session["admin"] = True
    session.permanent = True
    return redirect(url_for("statistics", lang=current_language()))


@app.route("/statistics")
def statistics():
    admin_mode = is_admin()
    own = own_ids()
    entries = []
    for (entry_id, pid, recorded_on, age, chol, hdl, bp, smoker, cigarettes, percent, name) in get_all_entries():
        if not admin_mode and pid not in own:      # visitors only see their own entries
            continue
        entry = {"number": entry_id, "date": recorded_on, "age": age, "percent": percent,
                 "category": risk_category(percent), "own": pid in own}
        if admin_mode:   # only the admin sees names and details of everybody
            entry.update(name=name, chol=chol, hdl=hdl, bp=bp, smoker=smoker, cigarettes=cigarettes)
        entries.append(entry)
    return render_template("statistics.html", stat=get_statistics(), entries=entries,
                           admin=admin_mode)


if __name__ == "__main__":
    app.run(debug=True)
