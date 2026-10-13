"""screening.py - step 1 BEFORE the score: questionnaire that finds high / very high risk directly.

Follows the pathway "Evaluation du risque cardiovasculaire" (INEAS 2022, figure 5):
  step 1  look for conditions that already mean high or very high risk  -> no score needed, treat first
  step 2  otherwise calculate the score (Med4All uses Framingham / ATP III, the course uses Globorisk)
  step 3  if the score is below 10 %: look for risk modifiers (they move "low" to "moderate")

Pure logic, no Flask and no database: easy to test.
For illustration only - not a diagnostic tool.
"""
import math

import units

# --- answer keys (check boxes) -------------------------------------------------------------
CVD_CLINICAL = ("mi_acs", "angina", "revascularisation", "afib", "stroke_tia",
                "aortic_aneurysm", "pad", "heart_failure")
CVD_IMAGING = ("stenosis50",)
DIABETES_DETAILS = ("dm_organ_damage", "dm_other_major_rf", "dm_type1_over20")
HTN_ORGAN_DAMAGE = ("htn_organ_damage",)
MODIFIERS = ("low_social", "uric_acid", "early_menopause_pregnancy", "heart_rate_80", "overweight",
             "sedentary", "psychosocial_stress", "family_early", "inflammatory", "psychiatric",
             "hiv", "sleep_apnea")
CHECK_KEYS = CVD_CLINICAL + CVD_IMAGING + DIABETES_DETAILS + HTN_ORGAN_DAMAGE + MODIFIERS

# --- numeric fields: key -> (low, high, unit) ----------------------------------------------
NUMBER_FIELDS = {
    "creatinine": (0.2, 15.0, "mg/dL"),
    "egfr": (3.0, 200.0, "mL/min/1.73 m²"),
    "total_chol": (100.0, 400.0, "mg/dL"),
    "ldl": (30.0, 300.0, "mg/dL"),
    "sbp": (80.0, 220.0, "mmHg"),
    "dbp": (40.0, 140.0, "mmHg"),
}
AGE_RANGE_SCREENING = (18, 100)

# --- limits from the pathway ---------------------------------------------------------------
EGFR_VERY_HIGH = 30      # severe CKD: eGFR < 30
EGFR_HIGH = 60           # moderate CKD: eGFR 30-59
CHOL_SEVERE = 310        # mg/dL (= 8 mmol/L)
LDL_SEVERE = 190         # mg/dL (= 4.9 mmol/L)
SBP_SEVERE, DBP_SEVERE = 180, 110

VERY_HIGH, HIGH, PROCEED = "very_high", "high", "proceed"


def egfr_ckd_epi_2021(creatinine_mg_dl, sex, age):
    """Kidney filtration rate in mL/min/1.73 m² (CKD-EPI 2021, without race factor)."""
    kappa, alpha = (0.7, -0.241) if sex == "f" else (0.9, -0.302)
    ratio = creatinine_mg_dl / kappa
    value = 142 * (min(ratio, 1) ** alpha) * (max(ratio, 1) ** -1.200) * (0.9938 ** age)
    return round(value * (1.012 if sex == "f" else 1), 1)


def _number(text):
    try:
        value = float(str(text).strip().replace(",", "."))
    except ValueError:
        return None
    return value if math.isfinite(value) else None


def clean(form):
    """Raw form -> (answers, errors). errors = {field: ("required"|"number"|"range"|"choose", info)}.

    answers: {"checks": set, "diabetes": bool, "sex", "age", "creatinine", "egfr", "total_chol",
              "ldl", "sbp", "dbp"}  (numbers are None when left empty)
    """
    errors, answers = {}, {"checks": set()}
    answers["diabetes"] = form.get("diabetes", "") == "yes"
    if form.get("diabetes", "") not in ("yes", "no"):
        errors["diabetes"] = ("choose", None)

    for key in CHECK_KEYS:
        if form.get(key):
            if key in DIABETES_DETAILS and not answers["diabetes"]:
                continue                       # sub-questions only count if diabetes = yes
            answers["checks"].add(key)

    for key, (low, high, std_unit) in NUMBER_FIELDS.items():
        raw = form.get(key, "").strip()
        answers[key] = None
        code = None
        if units.has_units(key):
            code = units.unit_code(key, form)
            if code is None:
                errors[key] = ("unit", None)
                continue
        if not raw:
            continue
        value = _number(raw)
        if value is None:
            errors[key] = ("number", None)
            continue
        standard = units.to_standard(key, value, code) if code else value
        if not low <= standard <= high:
            if code:
                errors[key] = ("range", (*units.display_range(key, code, low, high), units.label(key, code)))
            else:
                errors[key] = ("range", (low, high, std_unit))
        else:
            answers[key] = round(standard, 2) if code else standard

    sex = form.get("sex", "")
    answers["sex"] = sex if sex in ("m", "f") else ""
    answers["age"] = None
    raw_age = form.get("age", "").strip()
    if raw_age:
        value = _number(raw_age)
        low, high = AGE_RANGE_SCREENING
        if value is None or not value.is_integer():
            errors["age"] = ("number", None)
        elif not low <= value <= high:
            errors["age"] = ("range", (low, high, ""))
        else:
            answers["age"] = int(value)

    # Creatinine can only be turned into an eGFR with sex and age (and only if no eGFR was typed in)
    if answers["creatinine"] is not None and answers["egfr"] is None:
        if not answers["sex"]:
            errors["sex"] = ("required", None)
        if answers["age"] is None and "age" not in errors:
            errors["age"] = ("required", None)
    # diastolic without systolic (or the reverse) is allowed - each value is judged on its own
    return answers, errors


def assess(answers):
    """Judge the cleaned answers.

    Returns {"level": "very_high" | "high" | "proceed", "reasons": [keys], "modifiers": [keys],
             "missing": [lab keys], "egfr": float | None}
    """
    very_high, high = [], []
    checks = answers["checks"]

    if checks & set(CVD_CLINICAL) or checks & set(CVD_IMAGING):
        very_high.append("cvd_documented")

    if answers["diabetes"]:
        if checks & set(DIABETES_DETAILS):
            very_high.append("diabetes_complicated")
        else:
            high.append("diabetes")

    egfr = answers.get("egfr")
    if egfr is None and answers.get("creatinine") is not None and answers.get("sex") and answers.get("age"):
        egfr = egfr_ckd_epi_2021(answers["creatinine"], answers["sex"], answers["age"])
    if egfr is not None:
        if egfr < EGFR_VERY_HIGH:
            very_high.append("ckd_severe")
        elif egfr < EGFR_HIGH:
            high.append("ckd_moderate")

    if answers["total_chol"] is not None and answers["total_chol"] > CHOL_SEVERE:
        high.append("chol_severe")
    if answers["ldl"] is not None and answers["ldl"] > LDL_SEVERE:
        high.append("ldl_severe")
    if (answers["sbp"] is not None and answers["sbp"] >= SBP_SEVERE) or \
       (answers["dbp"] is not None and answers["dbp"] >= DBP_SEVERE):
        high.append("bp_severe")
    if checks & set(HTN_ORGAN_DAMAGE):
        high.append("htn_organ_damage")

    missing = []
    if egfr is None:
        missing.append("lab_kidney")
    if answers["total_chol"] is None or answers["ldl"] is None:
        missing.append("lab_lipids")
    if answers["sbp"] is None:
        missing.append("lab_bp")

    level = VERY_HIGH if very_high else HIGH if high else PROCEED
    return {"level": level, "reasons": very_high + high,
            "modifiers": [m for m in MODIFIERS if m in checks], "missing": missing, "egfr": egfr}
