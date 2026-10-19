# Omar Chaouch · Medical informatics projects

![tests](https://github.com/omarchaouch17/Project_2026/actions/workflows/tests.yml/badge.svg)

Medical informatics student (B.Sc., Hochschule Niederrhein, Krefeld). This repository collects the projects I built
to learn Python, SQL, testing, web development and the FHIR data standard, in the order I built them.

## Main project: Fahemni

**Fahemni** (Tunisian Arabic فهّمني, "make me understand") helps people understand the words of their health:
a heart-risk screening in two steps (questionnaire, then Framingham score), a medical word lookup with
332 terms, lab-unit conversion, and a **PDF sheet to bring to the doctor's appointment**, in German, English,
French and Arabic (right-to-left).

- **Live demo:** https://medilink-trbk.onrender.com (free server: the first request can take about 30 seconds)
- **Code and details:** [`medilink/`](medilink/)
- **Tech:** Python, Flask, Jinja2, SQLite / PostgreSQL, pytest (370+ tests), ReportLab, deployed on Render
- Learning project: please enter invented data only. It is not a medical device and gives no diagnosis.

## All projects

| Folder | What it is | Tech |
|---|---|---|
| [`medilink/`](medilink/) | **Fahemni**: web app with heart-risk screening, word lookup, unit conversion and a PDF sheet for the doctor, 4 languages | Python, Flask, PostgreSQL, pytest |
| [`fhir-conditions/`](fhir-conditions/) | Patients and diagnoses modelled on the FHIR `Patient` and `Condition` resources | Python, SQLite, FHIR |
| [`sql-patient-database/`](sql-patient-database/) | First patient database: CRUD functions and a JOIN with appointments | Python, SQLite |
| [`tunisia-data-analysis/`](tunisia-data-analysis/) | Suicide mortality rate in Tunisia 2000-2021, static chart and animation | Python, pandas, matplotlib |
| [`cli-note-manager/`](cli-note-manager/) | Command-line note tool with automated tests | Python, argparse, pytest |

## How I work

I build in small steps, write tests first for anything that affects a health result, and check formulas against the
primary source. I use AI assistance (Claude) as a tutor and pair programmer; I run, test and review what it produces.

## Contact

Omar Chaouch · amrouchchaouch@gmail.com · LinkedIn: www.linkedin.com/in/omar-chaouch-5200ba18a
