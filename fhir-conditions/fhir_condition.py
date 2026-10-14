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


diagnose = {
    "patient_name": "Anna Muster",
    "krankheit": "Herzinsuffizienz",  # heart failure
    "kategorie": "Herz-Kreislauf-Erkrankung",  # cardiovascular disease
    "typ": "nicht-operativ"  # non-surgical
}

print(diagnose)

diagnose2 = {
    "patient_name": "Anna Muster",
    "krankheit": "Gallensteine",  # gallstones
    "kategorie": "Viszeralchirurgie",  # visceral surgery
    "typ": "operativ"  # surgical
}

print(diagnose2)

alle_diagnosen = [diagnose, diagnose2]

for d in alle_diagnosen:
    print(d["krankheit"], "-", d["kategorie"])

condition_fhir = {
    "resourceType": "Condition",  # this tells the system: this is a diagnosis
    "subject": "Anna Muster",  # patient (Patient)
    "code": {
        "text": "Herzinsuffizienz"  # diagnosis name (Diagnosename)
    },
    "category": [
        {"text": "Herz-Kreislauf-Erkrankung"}  # cardiovascular disease
    ],
    "clinicalStatus": "active"  # currently ongoing (aktuell bestehend)
}

print(condition_fhir)

print(condition_fhir["code"]["text"])
print(condition_fhir["category"][0]["text"])

def erstelle_condition(patient_name, krankheit, kategorie, status="active"):
    return {
        "resourceType": "Condition",
        "subject": patient_name,
        "code": {
            "text": krankheit
        },
        "category": [
            {"text": kategorie}
        ],
        "clinicalStatus": status
    }


c1 = erstelle_condition("Anna Muster", "Herzinsuffizienz", "Herz-Kreislauf-Erkrankung")
c2 = erstelle_condition("Anna Muster", "Gallensteine", "Viszeralchirurgie")
c3 = erstelle_condition("Mohamed Ali", "Asthma", "Atemwegserkrankung")

for c in [c1, c2, c3]:
    print(c["subject"], "-", c["code"]["text"])

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