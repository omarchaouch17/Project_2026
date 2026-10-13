"""validation.py - input checks for the forms (server side, this is the one that counts).

The limits come from risk.py so that form, validation and calculation can never drift apart.
"""
import math

import units
from risk import RANGES
from translations import CATEGORIES, DIAGNOSES, OTHER

SMOKING_STATUS = ("never", "former", "current")
CIGARETTES_RANGE = (1, 100)   # cigarettes per day (average), only for current smokers
AGE_RANGE = (30, 79)          # same as in risk.framingham(): the score is only validated for ages 30-79

# field -> (label key in translations, limits, whole numbers only?, unit)
RISK_FIELDS = {
    "age": ("age", AGE_RANGE, True, ""),
    "cholesterol": ("cholesterol", RANGES["total_chol"], False, "mg/dL"),
    "hdl": ("hdl", RANGES["hdl"], False, "mg/dL"),
    "blood_pressure": ("blood_pressure", RANGES["sbp"], False, "mmHg"),
}


def _number(text):
    """Text -> float or None (empty, letters, nan, inf)."""
    try:
        value = float(text.strip().replace(",", "."))
    except (ValueError, AttributeError):
        return None
    return value if math.isfinite(value) else None


def validate_risk(form, t, patients):
    """Check the risk form. Returns (values, errors).

    patients - list of (id, name) of the existing patients; only these may be chosen.

    values - cleaned input (only usable if errors is empty)
    errors - {field name: message in the language of t}
    """
    errors, values = {}, {}

    names = dict(patients)
    try:
        patient_id = int(form.get("patient_id", ""))
    except ValueError:
        patient_id = None
    if patient_id in names:
        values["patient_id"], values["name"] = patient_id, names[patient_id]
    else:
        errors["patient_id"] = t["err_choose"].format(label=t["patient"])

    sex = form.get("sex", "")
    if sex not in ("m", "f"):
        errors["sex"] = t["err_sex"]
    values["sex"] = sex

    for field, (label_key, (low, high), whole_only, _unit) in RISK_FIELDS.items():
        label = t[label_key]
        code = None
        if units.has_units(field):
            code = units.unit_code(field, form)
            if code is None:
                errors[field] = t["err_choose"].format(label=t["unit"])
                continue
        raw = form.get(field, "")
        if not raw.strip():
            errors[field] = t["err_required"].format(label=label)
            continue
        value = _number(raw)
        if value is None or (whole_only and not value.is_integer()):
            errors[field] = t["err_number"].format(label=label)
            continue
        standard = units.to_standard(field, value, code) if code else value   # always checked in mg/dL / mmHg
        if not low <= standard <= high:
            if code:
                shown_low, shown_high = units.display_range(field, code, low, high)
                label = f"{label} ({units.label(field, code)})"
            else:
                shown_low, shown_high = low, high
            errors[field] = t["err_range"].format(label=label, low=shown_low, high=shown_high)
            continue
        values[field] = int(value) if whole_only else (round(standard, 2) if code else value)

    # Logic check: HDL is only a part of the total cholesterol, so it must be smaller
    if "hdl" in values and "cholesterol" in values and values["hdl"] >= values["cholesterol"]:
        errors["hdl"] = t["err_hdl"]

    # Smoking: status (required) + for current smokers the average amount per day
    status = form.get("smoking", "")
    if status not in SMOKING_STATUS:
        errors["smoking"] = t["err_choose"].format(label=t["smoking"])
    values["smoking"] = status
    values["smoker"] = status == "current"      # Framingham only knows "currently smokes yes/no"
    values["cigarettes"] = None
    if status == "current":
        low, high = CIGARETTES_RANGE
        raw = form.get("cigarettes", "")
        if not raw.strip():
            errors["cigarettes"] = t["err_required"].format(label=t["cigarettes"])
        else:
            value = _number(raw)
            if value is None or not value.is_integer():
                errors["cigarettes"] = t["err_number"].format(label=t["cigarettes"])
            elif not low <= value <= high:
                errors["cigarettes"] = t["err_range"].format(label=t["cigarettes"], low=low, high=high)
            else:
                values["cigarettes"] = int(value)

    values["treated"] = "treated" in form
    return values, errors


def validate_patient(form, t):
    """Check the "New patient" form. Returns (values, errors).

    values["diagnosis"] is the final text to store (choice or free text);
    values["diagnosis_choice"] / values["diagnosis_free"] are only used to show the form again.
    """
    labels = {"name": t["new_name"], "diagnosis": t["new_diagnosis"],
              "free": t["free_label"], "category": t["new_category"]}
    errors, values = {}, {}

    name = form.get("name", "").strip()
    if not name:
        errors["name"] = t["err_required"].format(label=labels["name"])
    elif len(name) > 60:
        errors["name"] = t["err_long"].format(label=labels["name"], max=60)
    elif "@" in name:       # people sometimes type their e-mail address: do not store it
        errors["name"] = t["err_no_email"].format(label=labels["name"])
    values["name"] = name

    # Diagnosis: fixed choice or "Other" + free text field
    choice = form.get("diagnosis", "")
    free = form.get("diagnosis_free", "").strip()
    values["diagnosis_choice"], values["diagnosis_free"], values["diagnosis"] = choice, free, ""
    if choice == OTHER:
        if not free:
            errors["diagnosis_free"] = t["err_required"].format(label=labels["free"])
        elif len(free) > 80:
            errors["diagnosis_free"] = t["err_long"].format(label=labels["free"], max=80)
        else:
            values["diagnosis"] = free
    elif choice in DIAGNOSES:
        values["diagnosis"] = choice
    else:
        errors["diagnosis"] = t["err_choose"].format(label=labels["diagnosis"])

    # Category: only values from the list are allowed
    category = form.get("category", "")
    if category not in CATEGORIES:
        errors["category"] = t["err_choose"].format(label=labels["category"])
    values["category"] = category
    return values, errors
