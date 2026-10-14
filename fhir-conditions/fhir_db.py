import sqlite3

def erstelle_tabelle():
    verbindung = sqlite3.connect("patienten.db")
    cursor = verbindung.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS patienten (
            id INTEGER PRIMARY KEY,
            name TEXT,
            diagnose TEXT
        )
    """)
    verbindung.commit()
    verbindung.close()

def patient_hinzufuegen(name, diagnose):
    verbindung = sqlite3.connect("patienten.db")
    cursor = verbindung.cursor()
    cursor.execute("INSERT INTO patienten (name, diagnose) VALUES (?, ?)", (name, diagnose))
    verbindung.commit()
    verbindung.close()

def erstelle_condition_tabelle():
    verbindung = sqlite3.connect("patienten.db")
    cursor = verbindung.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS conditions (
            id INTEGER PRIMARY KEY,
            patient_id INTEGER,
            code_text TEXT,
            category_text TEXT,
            clinical_status TEXT,
            FOREIGN KEY (patient_id) REFERENCES patienten (id)
        )
    """)
    verbindung.commit()
    verbindung.close()

def condition_hinzufuegen(patient_id, code_text, category_text, clinical_status="active"):
    verbindung = sqlite3.connect("patienten.db")
    cursor = verbindung.cursor()
    cursor.execute(
        "INSERT INTO conditions (patient_id, code_text, category_text, clinical_status) VALUES (?, ?, ?, ?)",
        (patient_id, code_text, category_text, clinical_status)
    )
    verbindung.commit()
    verbindung.close()

def patient_mit_diagnosen_anzeigen():
    verbindung = sqlite3.connect("patienten.db")
    cursor = verbindung.cursor()
    cursor.execute("""
        SELECT patienten.name, conditions.code_text, conditions.category_text, conditions.clinical_status
        FROM patienten
        JOIN conditions ON patienten.id = conditions.patient_id
    """)
    ergebnisse = cursor.fetchall()
    for zeile in ergebnisse:
        print(zeile)
    verbindung.close()
