# Study Notes – Fahemni (formerly MediLink)

Study notes for the medical and technical topics behind my Fahemni project (first called MediLink).
Each file covers one topic I worked through while building the project.

| # | Topic | File |
|---|-------|------|
| 01 | Framingham Hard CHD Risk Score | [01_Framingham_Risk_Score_Notes.pdf](01_Framingham_Risk_Score_Notes.pdf) |
| 02 | Testing with pytest | [02_Testing_with_pytest_Notes.pdf](02_Testing_with_pytest_Notes.pdf) |

## 01 – Framingham Hard CHD Risk Score

**In short:** Fahemni estimates a patient's 10-year risk of a heart attack or coronary death,
using age, cholesterol, blood pressure and smoking status. The formula comes from the
Framingham Heart Study, which followed thousands of people over decades.

**What I did**
- Implemented the score for men and women in `risk.py`
- Verified every coefficient against the primary source
  ([Framingham Heart Study](https://www.framinghamheartstudy.org/fhs-risk-functions/hard-coronary-heart-disease-10-year-risk/))
- Wrote automated tests for reference values, clinical rules and invalid input (`test_risk.py`)
- Added input validation, because in healthcare a wrong result is worse than no result
- Tested myself on the medical background (self-test in the PDF)

**What I learned**

-What surprised me most was that age is by far the biggest factor: with the same cholesterol and blood pressure, the risk rose from 0.2 % at age 30 to 16.8 % at age 79.

-The biggest lesson was that a passing test doesn't prove the code is correct: when I broke a test on purpose, it still passed for age 30 and only failed for age 79.

## How these notes were made

The explanations and diagrams in the PDFs were created with AI assistance (Claude), which I used
as a tutor. The implementation, the validation against the original source and the self-tests are my own work.

> ⚠️ Fahemni is a learning project. The risk calculator is a demo, not a diagnostic tool.
