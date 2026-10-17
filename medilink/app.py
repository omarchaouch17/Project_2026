import hmac
import os
import uuid
from datetime import timedelta

from flask import Flask, request, render_template, redirect, url_for, session, abort, Response

from fhir_db import (
    create_all_tables, add_patient, add_condition, delete_patient,
    save_risk, get_latest_risk, get_all_risks,
    count_visit, get_statistics, get_all_entries,
    get_patients_with_conditions, get_all_patients, get_conditions,
    save_screening, get_latest_screening, get_birth_year, set_birth_year, get_latest_risk_values
)
import screening as screening_logic
import screening_texts
import units
import medical_glossary
import eligibility
from translations import (
    texts, translate_diagnosis, category_name, CATEGORIES, DIAGNOSES, OTHER, NONE_DIAGNOSIS, excludes_framingham
)
from risk import framingham
from advice import risk_category, get_tips
import assistant
import sheet
import faq
from validation import (
    RISK_FIELDS, validate_risk, validate_patient, birth_year_error
)

DEFAULT_LANGUAGE = "en"
LANGUAGES = ["en", "de", "fr", "ar"]

app = Flask(__name__)
# On Render set SECRET_KEY and ADMIN_KEY as environment variables. Without ADMIN_KEY there is no admin access.
app.secret_key = os.environ.get("SECRET_KEY", "medilink-for-local-tests-only")
app.config.update(SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE="Lax",
                  PERMANENT_SESSION_LIFETIME=timedelta(days=365))
app.jinja_env.globals.update(category_name=category_name,
                             diagnosis_name=translate_diagnosis, OTHER=OTHER, NONE_DIAGNOSIS=NONE_DIAGNOSIS)

# Create the tables at start-up (important on Render: there is no ready-made database there).
# Data saved by the old German version is migrated automatically.
create_all_tables()


def current_language():
    """Language: ?lang=... / hidden form field (the person's choice, remembered in the session cookie),
    otherwise the remembered choice, otherwise the browser's language (Accept-Language), otherwise English."""
    chosen = request.values.get("lang")
    if chosen in texts:
        if session.get("lang") != chosen:
            session["lang"] = chosen
        return chosen
    remembered = session.get("lang")
    if remembered in texts:
        return remembered
    return request.accept_languages.best_match(LANGUAGES) or DEFAULT_LANGUAGE


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
        "units": units,
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



LANGUAGE_NAMES = {"de": "Deutsch", "en": "English", "fr": "Français", "ar": "العربية"}


@app.route("/glossary", methods=["GET", "POST"])
def glossary_page():
    """Look up one medical word typed by the person. POST only (the word never appears in a URL or log);
    unknown words get NO explanation - only close spellings of known words are offered."""
    language = current_language()
    query, results, suggestions, empty = "", [], [], False
    searched = request.method == "POST"
    if searched:
        query = medical_glossary.clean_query(request.form.get("q", ""))
        keys = medical_glossary.search(query)
        if len(medical_glossary.normalize(query)) < medical_glossary.MIN_QUERY:
            empty = True
        for key in keys:
            french_only = medical_glossary.is_french_only(key, language)
            results.append({
                "title": medical_glossary.title_of(key, language),
                "text": medical_glossary.text_of(key, language),
                "french_only": french_only,
                "others": [(code, LANGUAGE_NAMES[code], medical_glossary.title_of(key, code),
                            medical_glossary.text_of(key, code))
                           for code in ("fr", "ar", "de", "en")
                           if code != language and not medical_glossary.is_french_only(key, code)
                           and not (french_only and code == "fr")],
            })
        if not keys and not empty:
            suggestions = medical_glossary.suggest(query, language)
    return render_template("glossary.html", query=query, results=results, suggestions=suggestions,
                           searched=searched, empty=empty,
                           suggest_data=medical_glossary.suggest_data(language)), 200


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

    patient_id = add_patient(values["name"], "see conditions", values["birth_year"])
    if values["diagnosis"]:                      # "no known diagnosis" = no condition row
        add_condition(patient_id, values["diagnosis"], values["category"])

    remember_patient(patient_id)
    # The overview shows which tools fit the age; the questionnaire (step 1) is reachable from there
    return redirect(url_for("start_page", patient_id=patient_id, new=1, lang=current_language()))


@app.route("/patient/<int:patient_id>/start")
def start_page(patient_id):
    """Age timeline + cards: what is open for this person. The patient is always accepted."""
    if not can_see(patient_id):
        abort(404)
    name = dict(get_visible_patients()).get(patient_id)
    if name is None:
        abort(404)
    year = get_birth_year(patient_id)
    state = eligibility.tools(year, get_conditions(patient_id))
    return render_template("start.html", patient_id=patient_id, name=name, year=year, state=state,
                           just_saved=bool(request.args.get("new")),
                           language_path=f"/patient/{patient_id}/start")


@app.route("/patient/<int:patient_id>/birth-year", methods=["POST"])
def save_birth_year(patient_id):
    """For patients saved before the birth year existed."""
    if not can_see(patient_id):
        abort(404)
    year = eligibility.parse_birth_year(request.form.get("birth_year", ""))
    if year is None:
        t = texts[current_language()]
        name = dict(get_visible_patients()).get(patient_id, "")
        return render_template("start.html", patient_id=patient_id, name=name, year=None,
                               state=eligibility.tools(None), just_saved=False,
                               year_error=birth_year_error(t),
                               language_path=f"/patient/{patient_id}/start"), 400
    set_birth_year(patient_id, year)
    return redirect(url_for("start_page", patient_id=patient_id, lang=current_language()))


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


# form field -> glossary term explained next to it (only meanings, taken from medical_terms.py)
FIELD_TERMS = {"cholesterol": "gesamtcholesterin", "hdl": "hdl", "blood_pressure": "blutdruck",
               "smoking": "nikotinabusus"}


def risk_term_data(lang):
    """{field: {"t": title, "x": explanation}} in the page language, for the 'what does this mean?' buttons."""
    return {field: {"t": medical_glossary.title_of(key, lang), "x": medical_glossary.text_of(key, lang)}
            for field, key in FIELD_TERMS.items()}


SCREENING_TERMS = {"mi_acs": "myokardinfarkt", "angina": "angina", "afib": "vorhofflimmern", "stroke_tia": "schlaganfall",
                   "pad": "x_aomi_arteriopathie_des_membres_inferieurs", "heart_failure": "herzinsuffizienz",
                   "stenosis50": "stenose", "uric_acid": "x_acide_urique", "sleep_apnea": "x_apnee_du_sommeil",
                   "overweight": "adipositas", "creatinine": "kreatinin", "egfr": "egfr", "ldl": "ldl",
                   "total_chol": "gesamtcholesterin"}


DIABETES_ORGAN_TERMS = ("x_retinopathie_diabetique", "x_nephropathie_diabetique", "x_neuropathie_diabetique")


def screening_term_data(lang):
    """{input name: {"t": title, "x": explanation}} for the screening questionnaire (words with a validated glossary entry only)."""
    data = {name: {"t": medical_glossary.title_of(key, lang), "x": medical_glossary.text_of(key, lang)}
            for name, key in SCREENING_TERMS.items()}
    # "organ damage from diabetes" = eyes, kidneys, nerves: one explanation line per organ, taken from the glossary
    lines = [medical_glossary.title_of(key, lang) + ": " + medical_glossary.text_of(key, lang) for key in DIABETES_ORGAN_TERMS]
    base = screening_texts.SCREENING_TEXTS[lang]["c_dm_organ_damage"].split(" (")[0].split(" （")[0]
    data["dm_organ_damage"] = {"t": base, "x": "\n".join(lines)}
    return data


def _risk_page(values, errors, status=200, just_saved=False):
    """Render the risk form (empty, or with the input and red messages)."""
    return render_template("risk.html", values=values, errors=errors, fields=RISK_FIELDS,
                           term_data=risk_term_data(current_language()),
                           patients=patient_choices(), just_saved=just_saved,
                           chat_enabled=assistant.chat_enabled(), language_path="/risk"), status


@app.route("/risk")
def risk_form():
    # /risk?patient=3 pre-selects the patient (but the questionnaire must have been answered first)
    patient = request.args.get("patient", "")
    if patient.isdigit() and int(patient) in dict(get_visible_patients()) \
            and get_latest_screening(int(patient)) is None:
        return redirect(url_for("screening_form", patient=patient, lang=current_language()))
    values = {"patient_id": request.args.get("patient", "")}
    if patient.isdigit() and int(patient) in dict(get_visible_patients()):
        age = eligibility.age_from(get_birth_year(int(patient)))
        if age:
            values["age"] = age
    return _risk_page(values, {}, just_saved=bool(request.args.get("new")))


@app.route("/calculate_risk", methods=["POST"])
def calculate_risk():
    t = texts[current_language()]
    values, errors = validate_risk(request.form, t, get_visible_patients())
    if errors:
        return _risk_page(request.form, errors, 400)

    language = current_language()
    # Step 1 must be done and must not have found a high-risk condition
    screening = get_latest_screening(values["patient_id"])
    if screening is None:
        return redirect(url_for("screening_form", patient=values["patient_id"], lang=language))
    level, reasons, modifiers = screening
    if level != screening_logic.PROCEED:
        return _screening_result_page(values["patient_id"], values["name"], level, reasons, modifiers)

    # Safety net: stored diagnoses that also mean "no Framingham" (known heart disease, diabetes)
    for diagnosis in get_conditions(values["patient_id"]):
        if excludes_framingham(diagnosis):
            shown = translate_diagnosis(diagnosis, language)
            return _risk_page(request.form, {"general": t["err_framingham_excluded"].format(diagnosis=shown)}, 400)

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
    # Step 3: below 10 % but additional risk factors -> medium instead of low
    upgraded = category == "low" and bool(modifiers)
    if upgraded:
        category = "medium"
    # Remember it for the assistant (without the name)
    session["result"] = {"sex": values["sex"], "age": values["age"], "cholesterol": values["cholesterol"],
                         "hdl": values["hdl"], "blood_pressure": values["blood_pressure"],
                         "smoking": values["smoking"], "cigarettes": values["cigarettes"],
                         "risk_percent": risk_percent, "category": category}
    return render_template("result.html", chat_enabled=assistant.chat_enabled(),
                           suggestions=faq.suggestions(current_language()),
                           message=f"{values['name']}: " + t["result"].format(p=risk_percent),
                           smoking_line=smoking_line(values, t),
                           category=category, tips=get_tips(values, category), patient_id=values["patient_id"],
                           modifier_keys=modifiers if upgraded else [],
                           show_languages=False)


def _screening_result_page(patient_id, name, level, reasons, modifiers, missing=(), egfr=None, status=200):
    return render_template("screening_result.html", patient_id=patient_id, name=name, level=level,
                           reasons=reasons, missing=list(missing), egfr=egfr, show_languages=False,
                           language_path="/screening"), status


def _screening_page(patient_id, name, values, errors, status=200, just_saved=False):
    return render_template("screening.html", patient_id=patient_id, name=name, values=values, errors=errors,
                           checks=screening_logic, just_saved=just_saved,
                           term_data=screening_term_data(current_language()),
                           language_path=f"/screening?patient={patient_id}",
                           patient_arg=patient_id), status


@app.route("/screening")
def screening_form():
    patient = request.args.get("patient", "")
    names = dict(get_visible_patients())
    if not patient.isdigit() or int(patient) not in names:
        return redirect(url_for("home", lang=current_language()))
    age = eligibility.age_from(get_birth_year(int(patient)))
    return _screening_page(int(patient), names[int(patient)], {"age": age} if age else {}, {},
                           just_saved=bool(request.args.get("new")))


@app.route("/screening", methods=["POST"])
def screening_submit():
    t = texts[current_language()]
    names = dict(get_visible_patients())
    patient = request.form.get("patient_id", "")
    if not patient.isdigit() or int(patient) not in names:
        abort(404)
    patient_id = int(patient)

    answers, raw_errors = screening_logic.clean(request.form)
    labels = {"diabetes": t["sc_diabetes"], "creatinine": t["sc_creatinine"], "egfr": t["sc_egfr"],
              "total_chol": t["sc_total_chol"], "ldl": t["sc_ldl"], "sbp": t["sc_sbp"], "dbp": t["sc_dbp"],
              "age": t["age"]}
    errors = {}
    for field, (kind, info) in raw_errors.items():
        label = labels.get(field, "")
        if field == "sex":
            errors[field] = t["err_sex"]
        elif kind == "choose":
            errors[field] = t["err_choose"].format(label=label)
        elif kind == "required":
            errors[field] = t["err_required"].format(label=label)
        elif kind == "unit":
            errors[field] = t["err_choose"].format(label=t["unit"])
        elif kind == "number":
            errors[field] = t["err_number"].format(label=label)
        else:
            shown = f"{label} ({info[2]})" if info[2] else label
            errors[field] = t["err_range"].format(label=shown, low=info[0], high=info[1])
    if errors:
        return _screening_page(patient_id, names[patient_id], request.form, errors, 400)

    result = screening_logic.assess(answers)
    save_screening(patient_id, result["level"], result["reasons"], result["modifiers"])
    if result["level"] == screening_logic.PROCEED and not result["missing"]:
        return redirect(url_for("risk_form", patient=patient_id, lang=current_language()))
    return _screening_result_page(patient_id, names[patient_id], result["level"], result["reasons"],
                                  result["modifiers"], result["missing"], result["egfr"])


@app.route("/sheet/<int:patient_id>.pdf")
def doctor_sheet(patient_id):
    """PDF sheet for the doctor's visit: language of the practice (default German) next to the patient's language."""
    names = dict(get_visible_patients())
    if patient_id not in names:
        abort(404)
    screening = get_latest_screening(patient_id)
    if screening is None:
        return redirect(url_for("screening_form", patient=patient_id, lang=current_language()))
    level, reasons, modifiers = screening
    doctor_lang = request.args.get("doctor", "de")
    patient_lang = request.args.get("patient", current_language())
    if doctor_lang not in LANGUAGES or patient_lang not in LANGUAGES:
        abort(400)
    risk = get_latest_risk_values(patient_id) if level == screening_logic.PROCEED else None
    pdf = sheet.build_pdf({"name": names[patient_id], "age": eligibility.age_from(get_birth_year(patient_id)),
                           "level": level, "reasons": reasons, "modifiers": modifiers, "risk": risk,
                           "doctor_lang": doctor_lang, "patient_lang": patient_lang})
    return Response(pdf, mimetype="application/pdf",
                    headers={"Content-Disposition": f'attachment; filename="Fahemni_Sheet_{patient_id}.pdf"',
                             "Cache-Control": "no-store"})


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
