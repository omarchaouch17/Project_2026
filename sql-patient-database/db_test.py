import sqlite3

verbindung = sqlite3.connect("test.db")
cursor = verbindung.cursor()

cursor.execute("""
    CREATE TABLE IF NOT EXISTS patienten (
        id INTEGER PRIMARY KEY,
        name TEXT,
        diagnose TEXT
    )
""")
verbindung.commit()

cursor.execute("INSERT INTO patienten (name, diagnose) VALUES (?, ?)", ("Anna Muster", "Grippe"))
verbindung.commit()
cursor.execute("INSERT INTO patienten (name, diagnose) VALUES (?, ?)", ("Mohamed Ali", "Erkaeltumg"))
verbindung.commit()

cursor.execute("SELECT * FROM patienten")
ergebnisse = cursor.fetchall()

for zeile in ergebnisse:
    print(zeile)