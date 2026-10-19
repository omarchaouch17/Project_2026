# SQL Patient Database

My first database project: a small SQLite database of patients with their appointments.
Variable names and texts are in German.

## What it shows

- `CREATE TABLE`, `INSERT`, `SELECT`, `UPDATE`, `DELETE` (the five CRUD operations) as Python functions
- Parameterised queries (`?` placeholders), which protect against SQL injection
- A second table (`termine`, appointments) linked to the patient by a foreign key
- A `JOIN` that shows every patient with their appointments

## Files

- `patienten_db.py`: the database functions
- `db_test.py`: a small manual test script

## What came next

The same ideas were rebuilt with the FHIR structure in [`fhir-conditions/`](../fhir-conditions/)
and then used in the web app [`medilink/`](../medilink/) (Fahemni).

## Technical details

- Language: Python
- Storage: SQLite (`sqlite3` module); the `.db` file is not published
