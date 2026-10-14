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


def alle_patienten_anzeigen():
    verbindung = sqlite3.connect("patienten.db")
    cursor = verbindung.cursor()
    cursor.execute("SELECT * FROM patienten")
    ergebnisse = cursor.fetchall()
    for zeile in ergebnisse:
        print(zeile)
    verbindung.close()

def patient_loeschen(patient_id):
    verbindung = sqlite3.connect("patienten.db")
    cursor = verbindung.cursor()
    # deine Aufgabe: DELETE-Befehl mit ?-Platzhalter
    cursor.execute("DELETE FROM patienten WHERE id = ?", (patient_id,))  
    verbindung.commit()
    verbindung.close()


def diagnose_aktualisieren(patient_id, neue_diagnose):
    verbindung = sqlite3.connect("patienten.db")
    cursor = verbindung.cursor()
    # dein Teil: UPDATE-Befehl mit zwei ?-Platzhaltern
    cursor.execute("UPDATE patienten SET diagnose = ? WHERE id = ?", (neue_diagnose, patient_id))
    verbindung.commit()
    verbindung.close()

def erstelle_termine_tabelle():
    verbindung = sqlite3.connect("patienten.db")
    cursor = verbindung.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS termine (
            id INTEGER PRIMARY KEY,
            patient_id INTEGER,
            datum TEXT,
            grund TEXT,
            FOREIGN KEY (patient_id) REFERENCES patienten (id)
        )
    """)
    verbindung.commit()
    verbindung.close()


def termin_hinzufuegen(patient_id, datum, grund):
    verbindung = sqlite3.connect("patienten.db")
    cursor = verbindung.cursor()
    # dein Teil: INSERT-Befehl für die termine-Tabelle
    cursor.execute("INSERT INTO termine (patient_id, datum, grund) VALUES (?, ?, ?)", (patient_id, datum, grund))
    verbindung.commit()
    verbindung.close()


def patient_mit_terminen_anzeigen():
    verbindung = sqlite3.connect("patienten.db")
    cursor = verbindung.cursor()
    cursor.execute("""
        SELECT patienten.name, termine.datum, termine.grund
        FROM patienten
        JOIN termine ON patienten.id = termine.patient_id
    """)
    ergebnisse = cursor.fetchall()
    for zeile in ergebnisse:
        print(zeile)
    verbindung.close()