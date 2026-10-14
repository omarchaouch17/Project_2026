from notes import Note, NoteManager

def test_note_erstellen():
    notiz = Note(1, "Daten von Patient 1", "krank")
    assert notiz.titel == "Daten von Patient 1"
    assert notiz.inhalt == "krank"

def test_add_note():
    # Erstelle einen NoteManager, füge eine Notiz hinzu,
    manager = NoteManager()
    manager.add_note("Daten von Patient 1", "krank")
    notizen = manager.list_notes()
    # prüfe mit assert, ob sie in list_notes() auftaucht
    assert notizen[-1].titel == "Daten von Patient 1"
    pass

def test_delete_note():
    manager = NoteManager()
    manager.add_note("Daten von Patient 1", "krank")
    notizen = manager.list_notes()
    letzte_id = notizen[-1].id

    manager.delete_note(letzte_id)
    alle_ids = [notiz.id for notiz in manager.list_notes()]
    assert letzte_id not in alle_ids

    # deine Aufgabe: prüfen, dass letzte_id nicht mehr vorkommt
if __name__ == "__main__":
    test_note_erstellen()
    test_add_note()
    test_delete_note()
    print("Alle Tests bestanden!")