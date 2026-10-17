"""sheet.py - PDF sheet for the doctor's visit (no Flask, no database: easy to test).

Two columns: the language of the practice (default German) and the language of the patient.
If both languages are the same, one wide column is used. Arabic is written right to left
(letters joined with arabic-reshaper, order fixed with python-bidi).

The sheet contains NO diagnosis and NO advice: only what the person entered, the result texts that are
already on the website, three neutral questions to the doctor, the disclaimer and the emergency numbers.
"""
import datetime
import io
import os
import re

from reportlab.lib.colors import HexColor, white
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

import screening as screening_logic
from advice import risk_category
from translations import texts

FONT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fonts")
REGULAR, BOLD = "FahemniSans", "FahemniSans-Bold"

ACCENT, TEXT, MUTED = HexColor("#005eb8"), HexColor("#212b32"), HexColor("#4c6272")
RED, RED_BG = HexColor("#9b1c1c"), HexColor("#fdecea")
AMBER, AMBER_BG = HexColor("#7a4b00"), HexColor("#fff4d6")
GREEN, GREEN_BG = HexColor("#1b5e20"), HexColor("#e6f4ea")
BLUE_BG = HexColor("#e8f1fa")
LINE = HexColor("#aeb7bd")

PAGE_W, PAGE_H = A4
MARGIN, GUTTER = 36, 22
HEADER_H = 26
BOTTOM = 38

_ARABIC = re.compile("[؀-ۿݐ-ݿﭐ-﷿ﹰ-﻿]")
_fonts_ready = False


def _register_fonts():
    global _fonts_ready
    if not _fonts_ready:
        pdfmetrics.registerFont(TTFont(REGULAR, os.path.join(FONT_DIR, "DejaVuSans.ttf")))
        pdfmetrics.registerFont(TTFont(BOLD, os.path.join(FONT_DIR, "DejaVuSans-Bold.ttf")))
        _fonts_ready = True


def shape(text, rtl):
    """Text in logical order -> text in visual order for the PDF (only needed when Arabic letters occur)."""
    if not _ARABIC.search(text):
        return text
    try:
        import arabic_reshaper
        from bidi.algorithm import get_display
    except ImportError:          # libraries missing: still produce a PDF (Arabic then unjoined)
        return text
    return get_display(arabic_reshaper.reshape(text), base_dir="R" if rtl else "L")


def wrap(text, font, size, width, rtl):
    """Break text into lines that fit into width (measured after shaping)."""
    lines = []
    for paragraph in str(text).split("\n"):
        current = ""
        for word in paragraph.split():
            candidate = f"{current} {word}" if current else word
            if not current or stringWidth(shape(candidate, rtl), font, size) <= width:
                current = candidate
            else:
                lines.append(current)
                current = word
        lines.append(current)
    return lines


# ---------------------------------------------------------------------------------------------
# One column of one section: list of items -> height (and drawing)
# ---------------------------------------------------------------------------------------------
def render(c, items, x0, y_top, width, rtl):
    """Draw the items (if c is not None) and return their height. Items:
    ("tag", text) ("title", text) ("sub", text) ("h", text) ("p", text) ("bullet", text) ("note", text)
    ("badge", text, fg, bg) ("lines", n) ("box", [(text, bold)...])"""
    y = y_top
    right = x0 + width

    def put(line, x_left, x_right, font, size, color, base):
        if c is None:
            return
        c.setFont(font, size)
        c.setFillColor(color)
        visual = shape(line, rtl)
        if rtl:
            c.drawRightString(x_right, base, visual)
        else:
            c.drawString(x_left, base, visual)

    def paragraph(text, font, size, color, leading, indent=0, mark=None):
        nonlocal y
        for number, line in enumerate(wrap(text, font, size, width - indent, rtl)):
            put(line, x0 + indent, right - indent, font, size, color, y - size)
            if number == 0 and mark:
                put(mark, x0, right, font, size, color, y - size)
            y -= leading

    for item in items:
        kind = item[0]
        if kind == "tag":
            label = item[1]
            w = stringWidth(shape(label, rtl), BOLD, 8) + 14
            if c is not None:
                c.setFillColor(ACCENT)
                bx = right - w if rtl else x0
                c.roundRect(bx, y - 14, w, 14, 7, stroke=0, fill=1)
                c.setFillColor(white)
                c.setFont(BOLD, 8)
                c.drawCentredString(bx + w / 2, y - 10.5, shape(label, rtl))
            y -= 22
        elif kind == "title":
            paragraph(item[1], BOLD, 15, ACCENT, 19)
            y -= 2
        elif kind == "sub":
            paragraph(item[1], REGULAR, 8.5, MUTED, 11)
            y -= 4
        elif kind == "h":
            y -= 9
            paragraph(item[1], BOLD, 10.5, ACCENT, 13)
            if c is not None:
                c.setStrokeColor(LINE)
                c.setLineWidth(0.6)
                c.line(x0, y + 1, right, y + 1)
            y -= 4
        elif kind == "p":
            paragraph(item[1], REGULAR, 9.5, TEXT, 12.5)
            y -= 2
        elif kind == "note":
            paragraph(item[1], REGULAR, 8, MUTED, 10.5)
            y -= 2
        elif kind == "bullet":
            paragraph(item[1], REGULAR, 9.5, TEXT, 12.5, indent=12, mark="•")
            y -= 1.5
        elif kind == "badge":
            _, label, fg, bg = item
            lines = wrap(label, BOLD, 10.5, width - 16, rtl)
            height = len(lines) * 14 + 10
            if c is not None:
                c.setFillColor(bg)
                c.setStrokeColor(fg)
                c.setLineWidth(1)
                c.roundRect(x0, y - height, width, height, 6, stroke=1, fill=1)
            saved = y
            y -= 5
            for line in lines:
                put(line, x0 + 8, right - 8, BOLD, 10.5, fg, y - 10.5)
                y -= 14
            y = saved - height - 5
        elif kind == "lines":
            for _ in range(item[1]):
                y -= 19
                if c is not None:
                    c.setStrokeColor(LINE)
                    c.setLineWidth(0.5)
                    c.line(x0, y, right, y)
            y -= 2
        elif kind == "box":
            rows = []
            for text, bold in item[1]:
                font, size = (BOLD, 9.5) if bold else (REGULAR, 9)
                rows += [(line, font, size) for line in wrap(text, font, size, width - 22, rtl)]
            height = sum(size + 4 for _, _, size in rows) + 12
            if c is not None:
                c.setFillColor(HexColor("#fff7f6"))
                c.setStrokeColor(LINE)
                c.setLineWidth(0.6)
                c.roundRect(x0, y - height, width, height, 6, stroke=1, fill=1)
                c.setFillColor(HexColor("#c62828"))
                c.rect(right - 5 if rtl else x0, y - height, 5, height, stroke=0, fill=1)
            saved = y
            y -= 7
            for line, font, size in rows:
                put(line, x0 + 12, right - 12, font, size, TEXT, y - size)
                y -= size + 4
            y = saved - height - 4
    return y_top - y


# ---------------------------------------------------------------------------------------------
# Content: identical structure in every language, only the texts differ
# ---------------------------------------------------------------------------------------------
def _number(value, lang):
    shown = f"{value:g}"
    return shown.replace(".", ",") if lang in ("de", "fr") else shown


def build_blocks(lang, data, two_columns):
    t = texts[lang]
    level = data["level"]
    blocks = []

    head = []
    if two_columns:
        head.append(("tag", t["sheet_tag_doctor"] if lang == data["doctor_lang"] and not data.get("_second")
                     else t["sheet_tag_patient"]))
    head += [("title", t["sheet_title"]),
             ("sub", t["sheet_sub"].format(date=data["date"].strftime("%d.%m.%Y")))]
    blocks.append(head)

    person = [("h", t["sheet_h_person"]), ("p", f"{t['sheet_name']}: {data['name']}")]
    if data.get("age"):
        person.append(("p", f"{t['sheet_age']}: {t['sheet_years'].format(n=data['age'])}"))
    blocks.append(person)

    risk = data.get("risk")
    category, upgraded = None, False
    if level == screening_logic.PROCEED and risk:
        category = risk_category(risk["percent"])
        if category == "low" and data["modifiers"]:
            category, upgraded = "medium", True

    result = [("h", t["sheet_h_result"])]
    if level in (screening_logic.HIGH, screening_logic.VERY_HIGH):
        result.append(("badge", t[f"sc_res_{level}_title"], RED, RED_BG))
        result.append(("p", t[f"sc_res_{level}_text"]))
        if data["reasons"]:
            result.append(("p", t["sheet_h_reasons"] + ":"))
            result += [("bullet", t["r_" + key]) for key in data["reasons"]]
    else:
        result.append(("badge", t["sheet_level_proceed"], ACCENT, BLUE_BG))
        if risk:
            colors = {"low": (GREEN, GREEN_BG), "medium": (AMBER, AMBER_BG), "high": (RED, RED_BG)}[category]
            result.append(("badge", t["cat_" + category], *colors))
            result.append(("p", t["result"].format(p=_number(risk["percent"], lang))))
            if upgraded:
                result.append(("note", t["mod_note"]))
        else:
            result.append(("p", t["sheet_score_none"]))
    blocks.append(result)

    if data["modifiers"]:
        blocks.append([("h", t["sheet_h_extra"])] + [("bullet", t["m_" + key]) for key in data["modifiers"]])

    if level == screening_logic.PROCEED and risk and risk.get("values"):
        v = risk["values"]
        yes_no = lambda flag: t["sheet_yes"] if flag else t["sheet_no"]   # noqa: E731
        rows = [("h", t["sheet_h_values"]),
                ("p", f"{t['sheet_v_chol']}: {_number(v['cholesterol'], lang)} mg/dL"),
                ("p", f"{t['sheet_v_hdl']}: {_number(v['hdl'], lang)} mg/dL"),
                ("p", f"{t['sheet_v_sbp']}: {_number(v['systolic'], lang)} mmHg"),
                ("p", f"{t['sheet_v_smoking']}: {yes_no(v['smoker'])}"
                      + (f" ({t['sheet_v_cig']}: {v['cigarettes']})" if v.get("cigarettes") else "")),
                ("p", f"{t['sheet_v_treated']}: {yes_no(v['treated'])}")]
        blocks.append(rows)

    blocks.append([("h", t["sheet_h_questions"]), ("bullet", t["sheet_q1"]),
                   ("bullet", t["sheet_q2"]), ("bullet", t["sheet_q3"])])
    blocks.append([("h", t["sheet_h_notes"]), ("lines", 3)])
    blocks.append([("note", t["sheet_selfdata"]),
                   ("box", [(t["sos_title"], True), (t["sos_112"], False), (t["sos_116"], False)])])
    return blocks


def _draw(c, langs, data, total_pages):
    """Draw all pages. Returns the number of pages."""
    two = len(langs) == 2
    col_w = (PAGE_W - 2 * MARGIN - GUTTER * (len(langs) - 1)) / len(langs)
    xs = [MARGIN + i * (col_w + GUTTER) for i in range(len(langs))]
    per_lang = []
    for index, lang in enumerate(langs):
        per_lang.append(build_blocks(lang, dict(data, _second=bool(index)), two))

    page = 1
    top = PAGE_H - MARGIN - HEADER_H

    def page_frame():
        c.setFillColor(ACCENT)
        c.setFont(BOLD, 12)
        c.drawString(MARGIN, PAGE_H - MARGIN - 4, "Fahemni")
        c.setStrokeColor(ACCENT)
        c.setLineWidth(1.2)
        c.line(MARGIN, PAGE_H - MARGIN - 10, PAGE_W - MARGIN, PAGE_H - MARGIN - 10)
        if two:
            mid = MARGIN + col_w + GUTTER / 2
            c.setStrokeColor(LINE)
            c.setLineWidth(0.6)
            c.line(mid, BOTTOM - 6, mid, top + 4)
        if total_pages and total_pages > 1:
            c.setFont(REGULAR, 8)
            c.setFillColor(MUTED)
            c.drawRightString(PAGE_W - MARGIN, PAGE_H - MARGIN - 4,
                              texts["en"]["sheet_page"].format(n=page, total=total_pages)
                              if not two else f"{page} / {total_pages}")

    page_frame()
    y = top
    for index in range(len(per_lang[0])):
        rtls = [lang == "ar" for lang in langs]
        height = max(render(None, blocks[index], 0, 0, col_w, rtl)
                     for blocks, rtl in zip(per_lang, rtls))
        if y - height < BOTTOM and y != top:
            c.showPage()
            page += 1
            page_frame()
            y = top
        for blocks, x0, rtl in zip(per_lang, xs, rtls):
            render(c, blocks[index], x0, y, col_w, rtl)
        y -= height
    c.showPage()
    return page


def build_pdf(data):
    """data: name, age, level, reasons, modifiers, risk ({"percent", "values"} or None),
    doctor_lang, patient_lang, date. Returns the PDF as bytes."""
    _register_fonts()
    langs = [data["doctor_lang"]] if data["doctor_lang"] == data["patient_lang"] \
        else [data["doctor_lang"], data["patient_lang"]]
    data = dict(data, date=data.get("date") or datetime.date.today())
    pages = _draw(canvas.Canvas(io.BytesIO(), pagesize=A4), langs, data, None)
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    c.setTitle(texts[data["patient_lang"]]["sheet_title"])
    c.setAuthor("Fahemni")
    _draw(c, langs, data, pages)
    c.save()
    return buffer.getvalue()
