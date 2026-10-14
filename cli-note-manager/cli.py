import argparse
from notes import NoteManager


def main():
    parser = argparse.ArgumentParser(description="CLI Notiztool")
    subparsers = parser.add_subparsers(dest="befehl")

    add_parser = subparsers.add_parser("add")
    add_parser.add_argument("titel")
    add_parser.add_argument("inhalt")

    list_parser = subparsers.add_parser("list")

    search_parser = subparsers.add_parser("search")
    search_parser.add_argument("begriff")

    delete_parser = subparsers.add_parser("delete")
    delete_parser.add_argument("note_id")

    args = parser.parse_args()
    manager = NoteManager()

    if args.befehl == "add":
        manager.add_note(args.titel, args.inhalt)
        print("Notiz gespeichert.")
    elif args.befehl == "list":
        for notiz in manager.list_notes():
            print(f"{notiz.id}: {notiz.titel} - {notiz.inhalt}")
    elif args.befehl == "search":
        treffer = manager.search_notes(args.begriff)
        for notiz in treffer:
            print(f"{notiz.id}: {notiz.titel} - {notiz.inhalt}")
    elif args.befehl == "delete":
        manager.delete_note(int(args.note_id))
        print("Notiz gelöscht.")


if __name__ == "__main__":
    main()