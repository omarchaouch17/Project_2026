# Omar Chaouch · Medical informatics projects

![tests](https://github.com/omarchaouch17/Project_2026/actions/workflows/tests.yml/badge.svg)

Medical informatics student (B.Sc., Hochschule Niederrhein, Krefeld) with a computer science background.
This repository collects the projects I built to learn Python, SQL, testing, web development and the
FHIR data standard.

**Languages I work in:** Arabic (native), German (C1), French (C1), English (B2).
**Looking for:** a working-student position in healthcare IT or data management.

## Main project: Fahemni

**Fahemni** (Tunisian Arabic فهّمني, "make me understand") helps people understand the words of their health.

- A heart-risk screening in two steps: a questionnaire, then the Framingham 10-year score
- A medical word lookup with 332 terms, with short explanations next to the questionnaire items
- Lab-unit conversion (mg/dL, mmol/L, g/L, cmHg ...)
- A **PDF sheet to bring to the doctor's appointment**
- Four languages: German, English, French and Arabic (right-to-left layout)

<!-- Add a phone screenshot: put the file in docs/ and uncomment the next line -->
<!-- ![Fahemni on a phone](docs/screenshot-fahemni.png) -->

| | |
|---|---|
| **Live demo** | https://medilink-trbk.onrender.com (free server: the first request can take about 30 seconds) |
| **Code and details** | [`medilink/`](medilink/) (the folder still carries the old project name) |
| **Tech** | Python, Flask, Jinja2, SQLite / PostgreSQL, pytest (400+ tests), ReportLab, GitHub Actions, Render |
| **Data** | invented test data only |

> Learning project. It is **not a medical device**, gives **no diagnosis** and does not replace a doctor.
> Please enter invented data only.

### What this project shows

- **Backend:** Flask routes, server-side validation, parameterised SQL (one database layer for SQLite and PostgreSQL)
- **Health data:** a FHIR-inspired data model (Patient, Condition, risk results), unit conversion, formulas checked against their sources
- **Quality:** 400+ automated tests (reference values, boundary cases, routes), run on every push
- **Accessibility and languages:** four languages with right-to-left support, keyboard use, reduced-motion support
- **Privacy:** each visitor sees only their own entries; no personal data beyond invented test entries

## All projects

| Folder | What it is | Tech |
|---|---|---|
| [`medilink/`](medilink/) | **Fahemni**: heart-risk screening, word lookup, unit conversion and a PDF sheet for the doctor, in 4 languages | Python, Flask, PostgreSQL, pytest |
| [`fhir-conditions/`](fhir-conditions/) | Patients and diagnoses modelled on the FHIR `Patient` and `Condition` resources | Python, SQLite, FHIR |
| [`sql-patient-database/`](sql-patient-database/) | First patient database: CRUD functions and a JOIN with appointments | Python, SQLite |
| [`tunisia-data-analysis/`](tunisia-data-analysis/) | Mortality indicator for Tunisia 2000-2021 from public data, static chart and animation | Python, pandas, matplotlib |
| [`cli-note-manager/`](cli-note-manager/) | Command-line note tool with automated tests | Python, argparse, pytest |

## How I work

I build in small steps, write tests first for anything that affects a health result, and check formulas against the
primary source. I use AI assistance (Claude) as a tutor and pair programmer; I run, test and review what it produces.
Medical wording is reviewed by a medical student before it is published.

## Run Fahemni locally

```powershell
cd medilink
pip install -r requirements.txt
python app.py          # http://127.0.0.1:5000
python -m pytest -q    # tests
```

## Contact

Omar Chaouch · amrouchchaouch@gmail.com · LinkedIn: https://www.linkedin.com/in/chaouch-omar-5200ba18a
