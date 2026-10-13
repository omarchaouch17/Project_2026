"""units.py - lab values come in different units (Tunisia, Germany, France ...). Everything is converted
to the units Fahemni calculates with (mg/dL, mmHg) BEFORE any range check or calculation.

Factors: value in the chosen unit * factor = value in mg/dL (or mmHg).
"""

GROUPS = {
    # cholesterol (total, LDL, HDL): 1 mmol/L = 38.67 mg/dL, 1 g/L = 100 mg/dL
    "chol": {"mgdl": ("mg/dL", 1.0), "mmol": ("mmol/L", 38.67), "gl": ("g/L", 100.0)},
    # creatinine: 1 umol/L = 1/88.4 mg/dL, 1 mg/L = 0.1 mg/dL
    "creat": {"mgdl": ("mg/dL", 1.0), "umol": ("µmol/L", 1 / 88.4), "mgl": ("mg/L", 0.1)},
    # blood pressure: in North Africa often cmHg ("14/8" = 140/80 mmHg)
    "bp": {"mmhg": ("mmHg", 1.0), "cmhg": ("cmHg", 10.0)},
}
FIELD_GROUP = {"cholesterol": "chol", "hdl": "chol", "total_chol": "chol", "ldl": "chol",
               "creatinine": "creat", "blood_pressure": "bp", "sbp": "bp", "dbp": "bp"}


def default_code(field):
    return next(iter(GROUPS[FIELD_GROUP[field]]))


def has_units(field):
    return field in FIELD_GROUP


def options(field):
    """[(code, label, factor), ...] for the unit select of this field."""
    return [(code, label, factor) for code, (label, factor) in GROUPS[FIELD_GROUP[field]].items()]


def unit_code(field, form):
    """Chosen unit code, the standard unit if none was sent, or None if the code is invalid."""
    group = GROUPS[FIELD_GROUP[field]]
    code = form.get(field + "_unit", "") or default_code(field)
    return code if code in group else None


def _safe(field, code):
    """Unknown codes (tampered form) fall back to the standard unit instead of crashing a page."""
    return code if code in GROUPS[FIELD_GROUP[field]] else default_code(field)


def factor(field, code):
    return GROUPS[FIELD_GROUP[field]][_safe(field, code)][1]


def label(field, code):
    return GROUPS[FIELD_GROUP[field]][_safe(field, code)][0]


def to_standard(field, value, code):
    return value * factor(field, code)


def _fmt(number):
    return f"{number:.2f}".rstrip("0").rstrip(".")


def display_range(field, code, low, high):
    """Limits (given in the standard unit) shown in the chosen unit: (low_text, high_text)."""
    f = factor(field, code)
    if f == 1.0:
        return _fmt(low), _fmt(high)
    digits = 1 if f in (38.67, 10.0, 0.1) or f > 1 else 0
    return f"{low / f:.{max(digits, 1)}f}".rstrip("0").rstrip("."), f"{high / f:.{max(digits, 1)}f}".rstrip("0").rstrip(".")


def range_text(field, code, low, high):
    lo, hi = display_range(field, code, low, high)
    return f"{lo}–{hi} {label(field, code)}"
