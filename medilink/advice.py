"""advice.py - general hints for the Framingham result (rule based, transparent).

No diagnosis, no medication, no dosages - general information only.
The texts live in translations.py (keys tip_*, cat_*, emergency).
"""

# ATP III categories (10-year risk, "hard CHD"): below 10 % low, 10-20 % medium, above 20 % high
THRESHOLD_MEDIUM = 10.0
THRESHOLD_HIGH = 20.0

# Single values that trigger an extra hint (ATP III / blood pressure limit 140 mmHg)
CHOLESTEROL_HIGH = 240   # mg/dL
HDL_LOW = {"m": 40, "f": 50}   # mg/dL
BLOOD_PRESSURE_HIGH = 140  # mmHg


def risk_category(percent):
    """'low' (<10 %), 'medium' (10-20 %) or 'high' (>20 %)."""
    if percent > THRESHOLD_HIGH:
        return "high"
    if percent >= THRESHOLD_MEDIUM:
        return "medium"
    return "low"


def get_tips(values, category):
    """List of text keys (show them in this order).

    values: cleaned input from validate_risk (sex, cholesterol, hdl, blood_pressure, smoker).
    """
    tips = ["tip_" + category]          # doctor recommendation matching the category
    if values["smoker"]:
        tips.append("tip_smoking")
    if values["blood_pressure"] >= BLOOD_PRESSURE_HIGH:
        tips.append("tip_blood_pressure")
    if values["cholesterol"] >= CHOLESTEROL_HIGH:
        tips.append("tip_cholesterol")
    if values["hdl"] < HDL_LOW[values["sex"]]:
        tips.append("tip_hdl")
    tips += ["tip_exercise", "tip_nutrition"]
    return tips
