# MediLink

Multilingual health web application (Flask + SQLite/PostgreSQL) with the Framingham 10-year heart-risk score.
Portfolio project from my Medical Informatics studies (HSNR Krefeld). English is the default language.

**Live demo:** https://medilink-trbk.onrender.com
(Render free tier: the first request can take ~30 s.)

## Flow
1. **New patient** – name, diagnosis (dropdown or "Other"), category (dropdown).
2. **Automatic redirect** to the risk calculation with the new patient preselected.
3. **Risk score** – sex, age, cholesterol, HDL, blood pressure, smoking status
   (never / former / current + cigarettes per day), blood-pressure treatment.
4. **Result** – 10-year risk in %, risk category (ATP III: <10 / 10–20 / >20 %),
   general advice, emergency note, disclaimer.
5. **History** per patient; deletion via POST with confirmation.

## Features
- 4 languages: English (default), German, French, Arabic (incl. RTL layout) – all texts, errors and advice
- Input validation on the server **and** in the browser (ranges, HDL < total cholesterol)
- Rule-based advice (no medication, no dosages, no medical advice)
- Free rule-based help assistant (`faq.py`) and an optional AI assistant (Claude API, `ANTHROPIC_API_KEY`) with message limits and emergency-word detection
- FHIR-inspired database (Patient, Condition, risk score) with automatic migration
- Intro animation (respects `prefers-reduced-motion`)
- 150+ automated tests (pytest)

## Privacy & statistics
- `/statistics`: anonymous totals (visitors, patients, calculations, average risk) plus the visitor's own entries.
- Every visitor sees only their own patients and entries (no other visitor's data, not even anonymously). Only the admin sees everything.
- Visitor counter without IP addresses (random token in a cookie).
- Admin view (all names/values): set `ADMIN_KEY` and `SECRET_KEY`, then open `/admin?key=...`.

## Waiting page (Render cold start)
`wake/index.html` is a static page (host it for free, e.g. GitHub Pages) that shows an animated half-circle with "Welcome" in four languages
while the sleeping Render server wakes up. It pings `/health` and redirects to the app as soon as the server answers.
`/health` is not counted as a visit.

## Persistent storage
- Without configuration the app uses a local SQLite file (`patients.db`).
- With the environment variable `DATABASE_URL` (PostgreSQL, e.g. free on Neon) all data survives restarts and deploys on Render. `db.py` translates the SQL automatically.
- Databases created by the earlier German version (`patienten`, `besuche`, …) are migrated automatically on start-up, in one transaction (see `migrate_german_schema` in `fhir_db.py`).
- Tests never touch the real database (`conftest.py`).

## About smoking
The Framingham score only uses "current smoker: yes/no". The number of cigarettes is stored and shown for documentation but does not change the percentage.

## Run locally
```
pip install -r requirements.txt
python app.py        # http://127.0.0.1:5000
python -m pytest -q  # tests
```

## Structure
`app.py` (routes) · `validation.py` · `risk.py` (Framingham) · `advice.py` · `faq.py` · `assistant.py` ·
`db.py` · `fhir_db.py` · `translations.py` · `templates/` · `test_app.py`, `test_risk.py`

Not a diagnostic tool – for learning and demonstration only. Please enter invented data only.
