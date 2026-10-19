# CLI Note Manager

A command-line tool to add, list, search and delete notes. Notes are stored permanently in a JSON file.
My first Python project: classes, file handling, `argparse` and automated tests.

## Commands

```powershell
py cli.py add "Title" "Content"
py cli.py list
py cli.py search <term>
py cli.py delete <id>
```

## Tests

```powershell
py -m pytest -q
```

## Files

- `notes.py`: the `Note` class and the `NoteManager` (add, list, search, delete, save, load)
- `cli.py`: the command-line interface
- `test_notes.py`: automated tests

## Technical details

- Language: Python
- Storage: JSON file (`notes_data.json`, not published)
- Interface: `argparse`
