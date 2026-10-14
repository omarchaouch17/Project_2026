from dataclasses import dataclass, asdict
from datetime import datetime
import json
from pathlib import Path


@dataclass
class Note:
    id: int
    titel: str
    inhalt: str
    erstellt_am: str = None

    def __post_init__(self):
        if self.erstellt_am is None:
            self.erstellt_am = datetime.now().isoformat()


class NoteManager:
    def __init__(self, filepath="notes_data.json"):
        self.filepath = Path(filepath)
        self.notes = []
        self.load()

    def add_note(self, titel, inhalt):
        neue_id = len(self.notes) + 1
        neue_notiz = Note(neue_id, titel, inhalt)
        self.notes.append(neue_notiz)
        self.save()

    def save(self):
        notes_als_dicts = []
        for notiz in self.notes:
            notes_als_dicts.append(asdict(notiz))

        with open(self.filepath, "w") as f:
            json.dump(notes_als_dicts, f)

    def load(self):
        if self.filepath.exists():
            with open(self.filepath, "r") as f:
                geladene_dicts = json.load(f)

            for d in geladene_dicts:
                self.notes.append(Note(**d))
        else:
            self.notes = []

    def list_notes(self):
        return self.notes

    def search_notes(self, begriff):
        ergebnis = []
        for notiz in self.notes:
            if begriff in notiz.titel or begriff in notiz.inhalt:
                ergebnis.append(notiz)
        return ergebnis

    def delete_note(self, note_id):
        for notiz in self.notes:
            if notiz.id == note_id:
                self.notes.remove(notiz)
                self.save()