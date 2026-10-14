# FHIR-Inspired Patient Condition Database

A small SQLite database that models patients and their medical diagnoses (conditions) following the structure of the HL7 FHIR standard's `Patient` and `Condition` resources — built as a learning project to connect Medical Informatics coursework (KM1 - Klinische Medizin 1) with practical database design.

## Why FHIR

FHIR (Fast Healthcare Interoperability Resources) is the international standard for exchanging healthcare data between systems. Instead of inventing an arbitrary schema, this project follows FHIR's core idea: every diagnosis is a structured "Condition" resource, linked to a patient, with a clinical status (active/resolved).

## What it does

- Stores patients in a `patienten` table
- Stores diagnoses in a `conditions` table, linked via a foreign key
- Joins both tables to show each patient with their full diagnosis history
- Uses real disease categories from the KM1 (Klinische Medizin 1) curriculum — cardiovascular disease, visceral surgery (benign and malignant) — as realistic test data instead of placeholder text

## Example usage

```python
from fhir_db import erstelle_tabelle, erstelle_condition_tabelle, patient_hinzufuegen, condition_hinzufuegen, patient_mit_diagnosen_anzeigen

erstelle_tabelle()
erstelle_condition_tabelle()
patient_hinzufuegen("Anna Muster", "gesund")
condition_hinzufuegen(1, "Herzinsuffizienz", "Herz-Kreislauf-Erkrankung")
condition_hinzufuegen(1, "Appendizitis", "Viszeralchirurgie (nicht-maligne)")
patient_mit_diagnosen_anzeigen()
```

## Files

- `fhir_db.py` — main database logic (table creation, insert, join query)
- `fhir_condition.py` — earlier exploration of the FHIR JSON structure (dictionaries, nested resources) before moving to the database version

## Technical details

- Language: Python
- Storage: SQLite (`sqlite3` module)
- Data model inspired by: [HL7 FHIR Patient](https://www.hl7.org/fhir/patient.html) and [HL7 FHIR Condition](https://www.hl7.org/fhir/condition.html) resources

## Note

This is a simplified, educational version of FHIR — it captures the core idea (structured, linked clinical data) without implementing the full FHIR specification, REST API, or validation rules a production system would need.