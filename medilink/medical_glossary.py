"""medical_glossary.py - look up a medical word typed by a person (no automatic reading of letters).

Rules: only words that are in the glossary are explained; an unknown word is never explained or guessed.
The search text is neither stored nor logged by this module.
"""
import difflib
import re
import unicodedata

from medical_terms import TERMS
from medical_terms_extra import EXTRA_TERMS

LANG_KEYS = ("de", "en", "fr", "ar")
MAX_RESULTS = 6
MIN_QUERY = 2
MAX_QUERY = 80
SHORT_NAME = 3          # names up to this length (HTA, LDL, TSH ...) only match exactly


def normalize(text):
    """Lower case, no accents or Arabic vowel marks, œ->oe, ß->ss, punctuation -> space."""
    text = (text or "").lower().replace("œ", "oe").replace("ß", "ss").replace("æ", "ae")
    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if not unicodedata.combining(c))
    text = re.sub(r"[أإآٱ]", "ا", text).replace("ى", "ي").replace("ـ", "")
    text = re.sub(r"[^\w]+", " ", text, flags=re.UNICODE).replace("_", " ")
    return re.sub(r"\s+", " ", text).strip()


def is_french_only(key, lang):
    """True when the term only exists in French so far (the page then shows the French text with a note)."""
    return key in EXTRA_TERMS and lang != "fr"


def title_of(key, lang):
    if key in EXTRA_TERMS:                       # French only so far: same title in every language
        return EXTRA_TERMS[key]["title"]
    return TERMS[key][lang].split(":", 1)[0].strip()


def text_of(key, lang):
    if key in EXTRA_TERMS:
        text = EXTRA_TERMS[key]["text"]
        return text[:1].upper() + text[1:]
    parts = TERMS[key][lang].split(":", 1)
    text = parts[1].strip() if len(parts) > 1 else parts[0].strip()
    return text[:1].upper() + text[1:]          # the stored texts start in lower case after the colon


def names_of(key):
    """Every name a person might type for this term (normalised, without duplicates)."""
    if key in EXTRA_TERMS:
        raw = list(EXTRA_TERMS[key]["aliases"]) + [EXTRA_TERMS[key]["title"]]
    else:
        raw = _raw_names(key)
    seen, names = set(), []
    for item in raw:
        name = normalize(item)
        if name and name not in seen:
            seen.add(name)
            names.append(name)
    return names


def _raw_names(key):
    entry = TERMS[key]
    return list(entry["de_aliases"]) + list(entry["fr_aliases"]) + [title_of(key, l) for l in LANG_KEYS]


ALL_KEYS = list(TERMS) + list(EXTRA_TERMS)
_NAMES = {key: names_of(key) for key in ALL_KEYS}


def _score(query, names):
    best = 0
    words_q = f" {query} "
    for name in names:
        if name == query:
            return 3
        if len(name) < 3:
            continue
        if f" {name} " in words_q:                          # a known name inside what was typed ("diabete et hta")
            best = max(best, 2)
        elif len(name) <= SHORT_NAME or len(query) < 3:     # short names / very short input: exact match only
            continue
        elif name.startswith(query) or any(w.startswith(query) for w in name.split()):
            best = max(best, 2)
        elif query in name:
            best = max(best, 1)
    return best


def clean_query(text):
    return (text or "").strip()[:MAX_QUERY]


def search(text):
    """Keys of matching terms, best match first. Empty list = unknown word (nothing is invented)."""
    query = normalize(clean_query(text))
    if len(query) < MIN_QUERY:
        return []
    scored = [(_score(query, names), index, key) for index, (key, names) in enumerate(_NAMES.items())]
    scored = [s for s in scored if s[0] > 0]
    scored.sort(key=lambda s: (-s[0], s[1]))
    return [key for _, _, key in scored[:MAX_RESULTS]]


def suggest(text, lang):
    """'Did you mean ...': close spellings of KNOWN words only (shown as titles in the page language)."""
    query = normalize(clean_query(text))
    if len(query) < 3:
        return []
    lookup = {}
    for key, names in _NAMES.items():
        for name in names:
            if len(name) > SHORT_NAME:
                lookup.setdefault(name, key)
    close = difflib.get_close_matches(query, list(lookup), n=6, cutoff=0.75)
    keys = []
    for name in close:
        if lookup[name] not in keys:
            keys.append(lookup[name])
    return [(key, title_of(key, lang)) for key in keys[:3]]


def suggest_data(lang):
    """List for the type-ahead in the browser: [{"t": title in the page language, "n": normalised names}].
    The matching runs in the browser, so nothing typed is sent to the server before the person presses the button."""
    return [{"t": title_of(key, lang), "n": names} for key, names in _NAMES.items()]
