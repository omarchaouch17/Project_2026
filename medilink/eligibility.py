"""eligibility.py - which tools fit a patient's age (and diagnoses). Pure functions, no database.

The patient is always accepted. Only the tools are limited:
  * screening questionnaire (INEAS pathway): 18-100 years
  * Framingham score:                        30-79 years, and not with a known heart disease / diabetes
We only know the YEAR of birth, so the real age is "year difference" or one less. A tool counts as open if
either of the two possible ages fits; the forms still check the exact age that is typed in.
"""
import datetime

import screening
from translations import excludes_framingham

FRAMINGHAM_AGES = (30, 79)
SCREENING_AGES = screening.AGE_RANGE_SCREENING
OLDEST_BIRTH_YEAR = 1900


def this_year():
    return datetime.date.today().year


def birth_year_range():
    """Allowed birth years for the form: (first, last)."""
    return OLDEST_BIRTH_YEAR, this_year()


def parse_birth_year(text):
    """Text -> int year inside the allowed range, otherwise None."""
    text = (text or "").strip()
    if not text.isdigit() or len(text) != 4:
        return None
    year = int(text)
    low, high = birth_year_range()
    return year if low <= year <= high else None


def age_from(birth_year):
    """Estimated age (this year minus birth year). None if the year is unknown."""
    return None if not birth_year else this_year() - birth_year


def _fits(age, limits):
    low, high = limits
    return any(low <= candidate <= high for candidate in (age, age - 1))


def tools(birth_year, diagnoses=()):
    """State of the two tools: 'open', 'age' (age outside the range), 'diagnosis' or 'unknown' (no birth year)."""
    age = age_from(birth_year)
    if age is None:
        return {"age": None, "screening": "unknown", "framingham": "unknown", "any": False}
    screening_state = "open" if _fits(age, SCREENING_AGES) else "age"
    if not _fits(age, FRAMINGHAM_AGES):
        framingham_state = "age"
    elif any(excludes_framingham(d) for d in diagnoses):
        framingham_state = "diagnosis"
    else:
        framingham_state = "open"
    return {"age": age, "screening": screening_state, "framingham": framingham_state,
            "any": screening_state == "open" or framingham_state == "open"}
