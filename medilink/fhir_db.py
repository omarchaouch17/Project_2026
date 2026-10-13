"""fhir_db.py - FHIR-inspired tables: patients, conditions, risk_scores (+ visits for the counter).

* patients     ~ FHIR Patient
* conditions   ~ FHIR Condition (code_text, category_text, clinical_status)
* risk_scores  ~ FHIR RiskAssessment (one row per calculated Framingham score)
"""
import datetime

import db
from translations import to_canonical_category, to_canonical_diagnosis


def _patients_ddl():
    return f"""
        CREATE TABLE IF NOT EXISTS patients (
            id {db.id_column()},
            name TEXT,
            diagnosis TEXT,
            birth_year INTEGER
        )
    """


def create_patients_table():
    db.execute(_patients_ddl())


def add_patient(name, diagnosis, birth_year=None):
    return db.insert("INSERT INTO patients (name, diagnosis, birth_year) VALUES (?, ?, ?)",
                     (name, diagnosis, birth_year))


def ensure_birth_year_column():
    """Older databases have no birth_year column yet: add it (existing patients keep NULL = unknown)."""
    if db.table_exists("patients") and "birth_year" not in db.columns("patients"):
        db.execute("ALTER TABLE patients ADD COLUMN birth_year INTEGER")


def get_birth_year(patient_id):
    rows = db.query("SELECT birth_year FROM patients WHERE id = ?", (patient_id,))
    return rows[0][0] if rows and rows[0][0] else None


def set_birth_year(patient_id, birth_year):
    db.execute("UPDATE patients SET birth_year = ? WHERE id = ?", (birth_year, patient_id))


def _conditions_ddl():
    return f"""
        CREATE TABLE IF NOT EXISTS conditions (
            id {db.id_column()},
            patient_id INTEGER,
            code_text TEXT,
            category_text TEXT,
            clinical_status TEXT,
            FOREIGN KEY (patient_id) REFERENCES patients (id)
        )
    """


def create_conditions_table():
    db.execute(_conditions_ddl())


def add_condition(patient_id, code_text, category_text, clinical_status="active"):
    db.execute(
        "INSERT INTO conditions (patient_id, code_text, category_text, clinical_status) VALUES (?, ?, ?, ?)",
        (patient_id, code_text, category_text, clinical_status)
    )


def get_conditions(patient_id):
    """All stored diagnoses (code_text) of one patient as a list of strings."""
    rows = db.query("SELECT code_text FROM conditions WHERE patient_id = ?", (patient_id,))
    return [r[0] for r in rows if r[0]]


def print_patients_with_conditions():
    for row in db.query("""
        SELECT patients.name, conditions.code_text, conditions.category_text, conditions.clinical_status
        FROM patients
        JOIN conditions ON patients.id = conditions.patient_id
    """):
        print(row)


def delete_patient(patient_id):
    db.execute_many([
        ("DELETE FROM screenings WHERE patient_id = ?", (patient_id,)),
        ("DELETE FROM risk_scores WHERE patient_id = ?", (patient_id,)),
        ("DELETE FROM conditions WHERE patient_id = ?", (patient_id,)),
        ("DELETE FROM patients WHERE id = ?", (patient_id,)),
    ])


def _risk_scores_ddl():
    return f"""
        CREATE TABLE IF NOT EXISTS risk_scores (
            id {db.id_column()},
            patient_id INTEGER,
            recorded_on TEXT,
            age INTEGER,
            total_cholesterol DOUBLE PRECISION,
            hdl DOUBLE PRECISION,
            systolic_bp DOUBLE PRECISION,
            smoker INTEGER,
            treated_hypertension INTEGER,
            risk_percent DOUBLE PRECISION,
            cigarettes_per_day INTEGER,
            FOREIGN KEY (patient_id) REFERENCES patients (id)
        )
    """


def create_risk_scores_table():
    db.execute(_risk_scores_ddl())


def get_latest_risk(patient_id):
    rows = db.query("""
        SELECT risk_percent, recorded_on
        FROM risk_scores
        WHERE patient_id = ?
        ORDER BY recorded_on DESC, id DESC
        LIMIT 1
    """, (patient_id,))
    return rows[0] if rows else None


def save_risk(patient_id, age, total_cholesterol, hdl, systolic_bp, smoker, treated_hypertension,
              risk_percent, cigarettes_per_day=None):
    db.execute(
        "INSERT INTO risk_scores (patient_id, recorded_on, age, total_cholesterol, hdl, systolic_bp, smoker, "
        "treated_hypertension, risk_percent, cigarettes_per_day) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (patient_id, datetime.date.today().isoformat(), age, total_cholesterol, hdl, systolic_bp,
         int(bool(smoker)), int(bool(treated_hypertension)), risk_percent, cigarettes_per_day)
    )


def get_all_risks(patient_id):
    return db.query("""
        SELECT risk_percent, recorded_on
        FROM risk_scores
        WHERE patient_id = ?
        ORDER BY recorded_on DESC, id DESC
    """, (patient_id,))


def get_patients_with_conditions():
    """(name, diagnosis, category, patient_id) - patients without a condition have None."""
    return db.query("""
        SELECT patients.name, conditions.code_text, conditions.category_text, patients.id
        FROM patients
        LEFT JOIN conditions ON patients.id = conditions.patient_id
        ORDER BY patients.id, conditions.id
    """)


def get_all_patients():
    """All patients as [(id, name), ...], alphabetical."""
    return db.query("SELECT id, name FROM patients ORDER BY LOWER(name), id")


_VISITS_DDL = """
    CREATE TABLE IF NOT EXISTS visits (
        token TEXT PRIMARY KEY,
        first_visit TEXT
    )
"""


def create_screenings_table():
    """Result of the step-1 questionnaire (only the outcome, not the single answers)."""
    db.execute(f"""
        CREATE TABLE IF NOT EXISTS screenings (
            id {db.id_column()},
            patient_id INTEGER NOT NULL,
            recorded_on TEXT NOT NULL,
            level TEXT NOT NULL,
            reasons TEXT,
            modifiers TEXT
        )
    """)


def save_screening(patient_id, level, reasons, modifiers):
    db.execute(
        "INSERT INTO screenings (patient_id, recorded_on, level, reasons, modifiers) VALUES (?, ?, ?, ?, ?)",
        (patient_id, datetime.date.today().isoformat(), level, ",".join(reasons), ",".join(modifiers))
    )


def get_latest_screening(patient_id):
    """(level, [reason keys], [modifier keys]) of the newest questionnaire, or None if there is none."""
    rows = db.query("""
        SELECT level, reasons, modifiers FROM screenings
        WHERE patient_id = ? ORDER BY id DESC LIMIT 1
    """, (patient_id,))
    if not rows:
        return None
    level, reasons, modifiers = rows[0]
    return level, [r for r in (reasons or "").split(",") if r], [m for m in (modifiers or "").split(",") if m]


def create_visits_table():
    """Counts visitors without personal data: only a random token (no IP address)."""
    db.execute(_VISITS_DDL)


def count_visit(token):
    db.execute(
        "INSERT INTO visits (token, first_visit) VALUES (?, ?) ON CONFLICT (token) DO NOTHING",
        (token, datetime.datetime.now().isoformat(timespec="seconds")))


def get_statistics():
    """Totals: visitors, patients, calculations, average risk."""
    visitors = db.query("SELECT COUNT(*) FROM visits")[0][0]
    patients = db.query("SELECT COUNT(*) FROM patients")[0][0]
    calculations, average = db.query("SELECT COUNT(*), AVG(risk_percent) FROM risk_scores")[0]
    return {"visitors": visitors, "patients": patients, "calculations": calculations,
            "average": round(float(average), 1) if average is not None else None}


def get_all_entries(limit=200):
    """All calculations (newest first) incl. the name - anonymisation happens later, in the app."""
    return db.query("""
        SELECT risk_scores.id, risk_scores.patient_id, risk_scores.recorded_on, risk_scores.age,
               risk_scores.total_cholesterol, risk_scores.hdl, risk_scores.systolic_bp, risk_scores.smoker,
               risk_scores.cigarettes_per_day, risk_scores.risk_percent, patients.name
        FROM risk_scores LEFT JOIN patients ON patients.id = risk_scores.patient_id
        ORDER BY risk_scores.recorded_on DESC, risk_scores.id DESC
        LIMIT ?
    """, (limit,))


# ---------------------------------------------------------------------------------------------
# Migration: databases created by the German version (tables patienten, besuche, columns datum,
# alter_wert, ...) are copied once into the English tables. Everything runs in ONE transaction.
# ---------------------------------------------------------------------------------------------

def _reset_sequence(table):
    """PostgreSQL only: after copying rows with explicit ids the next automatic id must be higher."""
    return (f"SELECT setval(pg_get_serial_sequence('{table}', 'id'), "
            f"COALESCE((SELECT MAX(id) FROM {table}), 1), (SELECT MAX(id) FROM {table}) IS NOT NULL)", ())


def migrate_german_schema():
    """Copy data from the old German schema into the English one; returns True if something was migrated."""
    if not db.table_exists("patienten"):
        return False

    old_patients = db.query("SELECT id, name, diagnose FROM patienten")
    old_conditions = []
    if db.table_exists("conditions"):
        old_conditions = db.query("SELECT id, patient_id, code_text, category_text, clinical_status FROM conditions")
    old_scores = []
    if db.table_exists("risk_scores") and "alter_wert" in db.columns("risk_scores"):
        zig = "zigaretten_pro_tag" if "zigaretten_pro_tag" in db.columns("risk_scores") else "NULL"
        old_scores = db.query(
            f"SELECT id, patient_id, datum, alter_wert, cholesterin, hdl, blutdruck, raucher, behandelt, "
            f"risiko_prozent, {zig} FROM risk_scores")
    old_visits = db.query("SELECT token, erster_besuch FROM besuche") if db.table_exists("besuche") else []

    # Everything below runs in ONE transaction: drop the old tables, create the new ones, copy the rows.
    statements = []
    for table in ("conditions", "risk_scores"):
        if db.table_exists(table):
            statements.append((f"DROP TABLE {table}", ()))
    statements.append(("DROP TABLE patienten", ()))
    if db.table_exists("besuche"):
        statements.append(("DROP TABLE besuche", ()))
    statements += [(_patients_ddl(), ()), (_conditions_ddl(), ()), (_risk_scores_ddl(), ()), (_VISITS_DDL, ())]

    copy = statements
    for pid, name, diagnose in old_patients:
        copy.append(("INSERT INTO patients (id, name, diagnosis) VALUES (?, ?, ?)",
                     (pid, name, "see conditions" if diagnose == "siehe conditions" else diagnose)))
    for cid, pid, code, category, status in old_conditions:
        copy.append(("INSERT INTO conditions (id, patient_id, code_text, category_text, clinical_status) "
                     "VALUES (?, ?, ?, ?, ?)",
                     (cid, pid, to_canonical_diagnosis(code), to_canonical_category(category), status)))
    for row in old_scores:
        copy.append(("INSERT INTO risk_scores (id, patient_id, recorded_on, age, total_cholesterol, hdl, systolic_bp, "
                     "smoker, treated_hypertension, risk_percent, cigarettes_per_day) "
                     "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", tuple(row)))
    for token, first in old_visits:
        copy.append(("INSERT INTO visits (token, first_visit) VALUES (?, ?)", (token, first)))
    if db.postgres_enabled():
        copy += [_reset_sequence(t) for t in ("patients", "conditions", "risk_scores")]
    db.execute_many(copy)
    return True


def create_all_tables():
    """Called once at start-up: create missing tables, then migrate old German data if there is any."""
    if db.table_exists("patienten"):
        migrate_german_schema()
        create_screenings_table()
        ensure_birth_year_column()
        return
    create_patients_table()
    create_conditions_table()
    create_risk_scores_table()
    create_visits_table()
    create_screenings_table()
    ensure_birth_year_column()
