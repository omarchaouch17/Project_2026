\# CLI Notiztool



Ein Kommandozeilen-Tool, mit dem Notizen erstellt, durchsucht und gelöscht werden können. Die Daten werden dauerhaft in einer JSON-Datei gespeichert.



\## Funktionen

\- \*\*Add\*\*: Notizen hinzufügen

\- \*\*List\*\*: Alle vorhandenen Notizen anzeigen

\- \*\*Search\*\*: Notizen nach einem Begriff durchsuchen

\- \*\*Delete\*\*: Notizen löschen



\## Installation

```powershell

py -m venv venv

venv\\Scripts\\activate

```



\## Verwendung

```powershell

py cli.py add "Titel" "Inhalt"

py cli.py list

py cli.py search <Begriff>

py cli.py delete <ID>

```



\## Technische Details

\- Sprache: Python

\- Speicherung: JSON-Datei (notes\_data.json)

\- Kommandozeilen-Interface via argparse

