"""
Build the submission PDF from CE766_Final_Submission_Text.md (single source of truth) and the two figures.
Page 1 is a cover page in the IIT Bombay report style (faded logo behind the text); every later page
carries the logo in the top-right corner and a "CE766 | ... Page x of y" footer.
Run from the repository root:   python code/make_pdf.py
Output: CE766_Final_Submission_PowaiLake.pdf
"""
import os, re, html
from typing import Any, Dict
import matplotlib
from PIL import Image as PILImage
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Image, ListFlowable, ListItem,
                                KeepTogether, PageBreak)

HERE = os.path.dirname(os.path.abspath(__file__))
SUB = os.path.dirname(HERE)                                # repository root
MD = os.path.join(SUB, "CE766_Final_Submission_Text.md")
OUT = os.path.join(SUB, "CE766_Final_Submission_PowaiLake.pdf")
FIGS = {"Figure 1.": os.path.join(SUB, "figures", "Figure1_pareto_robustness.png"),
        "Figure 2.": os.path.join(SUB, "figures", "Figure2_trajectories_prim.png")}
LOGO = os.path.join(SUB, "figures", "iitb_logo.png")              # IIT Bombay logo (page header)
WMARK = os.path.join(SUB, "figures", "iitb_logo_watermark.png")   # faded copy (cover page)

# ---------------- fonts (DejaVu ships with matplotlib and covers Greek, arrows, combining marks) ----------------
FONT_DIR = os.path.join(os.path.dirname(matplotlib.__file__), "mpl-data", "fonts", "ttf")
for fam, files in {"DejaVuSans": ("DejaVuSans", "DejaVuSans-Bold", "DejaVuSans-Oblique", "DejaVuSans-BoldOblique"),
                   "DejaVuSerif": ("DejaVuSerif", "DejaVuSerif-Bold", "DejaVuSerif-Italic", "DejaVuSerif-BoldItalic")}.items():
    for f in files:
        pdfmetrics.registerFont(TTFont(f, os.path.join(FONT_DIR, f + ".ttf")))
    pdfmetrics.registerFontFamily(fam, normal=files[0], bold=files[1], italic=files[2], boldItalic=files[3])
pdfmetrics.registerFont(TTFont("DejaVuSansMono", os.path.join(FONT_DIR, "DejaVuSansMono.ttf")))

NAVY, INK, INK2, RULE, LINK = HexColor("#1F4E79"), HexColor("#111111"), HexColor("#55534e"), HexColor("#c9d6e6"), HexColor("#1a5fb4")
body = ParagraphStyle("body", fontName="DejaVuSans", fontSize=9.2, leading=13.1, textColor=INK, alignment=TA_LEFT,
                      spaceAfter=4.5)
bullet = ParagraphStyle("bullet", parent=body, spaceAfter=1.2)
h2 = ParagraphStyle("h2", fontName="DejaVuSans-Bold", fontSize=12.2, leading=15, textColor=NAVY, spaceBefore=8,
                    spaceAfter=4)
eq = ParagraphStyle("eq", fontName="DejaVuSerif", fontSize=10.2, leading=15, alignment=TA_CENTER, textColor=INK,
                    spaceBefore=1, spaceAfter=6)

# ---------------- cover page (same layout, fonts and colours as the CE769 report cover) ----------------
COVER_NAVY, COVER_BLUE, FOOT_RULE = HexColor("#1F3864"), HexColor("#0070C0"), HexColor("#4F81BD")


def cover_style(name, **k):
    base: Dict[str, Any] = dict(fontName="Times-Bold", fontSize=14, leading=20, alignment=TA_CENTER, textColor=INK)
    base.update(k)
    return ParagraphStyle(name, **base)


c_report, c_title = cover_style("c_report", textColor=COVER_NAVY), cover_style("c_title", fontSize=15.5, leading=22)
c_sub, c_line = cover_style("c_sub", fontSize=13.5), cover_style("c_line")
c_by, c_name = cover_style("c_by", fontName="Times-BoldItalic"), cover_style("c_name", textColor=COVER_BLUE)
c_date = cover_style("c_date", textColor=COVER_NAVY)
cover = [
    Spacer(1, 15 * mm), Paragraph("A Report on", c_report), Spacer(1, 4 * mm),
    Paragraph("REFORMULATING THE LAKE PROBLEM<br/>FOR POWAI LAKE, MUMBAI", c_title), Spacer(1, 2 * mm),
    Paragraph("(Robust Phosphorus Management after Sewage Diversion)", c_sub), Spacer(1, 22 * mm),
    Paragraph("CE766 Course Project Report:", c_line), Paragraph("Watershed Management", c_line), Spacer(1, 12 * mm),
    Paragraph("Submitted by", c_by), Spacer(1, 2 * mm), Paragraph("Prathmesh Walimbe (23B0747)", c_name),
    Spacer(1, 30 * mm), Paragraph("<u>Submission Date: 24 November 2026</u>", c_date), Spacer(1, 10 * mm),
    Paragraph("Department of Civil Engineering", c_line), Paragraph("Indian Institute of Technology Bombay", c_line),
    Paragraph("Powai, Mumbai - 400076", c_line), PageBreak(),
]


def cover_page(c, doc):                                     # faded logo behind the cover text
    w, h = A4
    iw, ih = PILImage.open(WMARK).size
    lw = 165 * mm
    lh = lw * ih / iw
    c.drawImage(WMARK, (w - lw) / 2, h - 58 * mm - lh, width=lw, height=lh, mask="auto")

# ---------------- inline markdown -> reportlab markup ----------------
SUBSCRIPT = re.compile(r"\b(A|Q|TP|P|e|v|p)_(C|L|STP|raw|eff|yr|u|s|h)\b")


def fmt(s):
    keep = []

    def stash(markup):
        keep.append(markup)
        return f"\x00{len(keep) - 1}\x00"

    s = html.escape(s, quote=False)
    s = re.sub(r"`([^`]+)`", lambda m: stash(f'<font name="DejaVuSansMono" size="8.6">{m.group(1)}</font>'), s)

    def link(m):
        url = m.group(0).rstrip(".,;)")
        tail = m.group(0)[len(url):]
        return stash(f'<a href="{url}" color="#1a5fb4">{url}</a>') + tail
    s = re.sub(r"https?://\S+", link, s)
    s = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", s)
    s = re.sub(r"(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?![\w*])", r"<i>\1</i>", s)
    s = SUBSCRIPT.sub(r"\1<sub>\2</sub>", s)
    s = re.sub(r"\bf0\b", "f<sub>0</sub>", s)
    s = re.sub(r"\^(\w)", r"<super>\1</super>", s)
    s = s.replace("yr⁻¹", "yr<super>−1</super>")
    return re.sub(r"\x00(\d+)\x00", lambda m: keep[int(m.group(1))], s)


# ---------------- page decoration with "Page x of y" ----------------
class NumberedCanvas(canvas.Canvas):
    def __init__(self, *a, **k):
        super().__init__(*a, **k)
        self._pages = []

    def showPage(self):
        self._pages.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        n = len(self._pages)
        for st in self._pages:
            self.__dict__.update(st)
            self.decorate(n)
            super().showPage()
        super().save()

    def decorate(self, n):
        if self._pageNumber == 1:                           # cover page: no header or footer
            return
        w, h = A4
        iw, ih = PILImage.open(LOGO).size
        lh = 12.5 * mm
        lw = lh * iw / ih
        self.drawImage(LOGO, w - 20 * mm - lw, h - 5.5 * mm - lh, width=lw, height=lh, mask="auto")
        self.setStrokeColor(FOOT_RULE); self.setLineWidth(1.4)
        self.line(20 * mm, 14 * mm, w - 20 * mm, 14 * mm)
        self.setFillColor(INK); self.setFont("Times-Bold", 9.5)
        self.drawString(20 * mm, 9.5 * mm, "CE766 | Powai Lake Phosphorus Management")
        parts = [("Page ", "Times-Roman"), (str(self._pageNumber), "Times-Bold"), (" of ", "Times-Roman"),
                 (str(n), "Times-Bold")]
        x = w - 20 * mm - sum(pdfmetrics.stringWidth(t, f, 9.5) for t, f in parts)
        for t, f in parts:
            self.setFont(f, 9.5); self.drawString(x, 9.5 * mm, t)
            x += pdfmetrics.stringWidth(t, f, 9.5)


# ---------------- parse the markdown ----------------
lines = open(MD, encoding="utf-8").read().splitlines()
lines = lines[lines.index("---") + 1:]                     # skip the md title / upload note above the rule
EQ = re.compile(r"^(Q\(t\)|L\(t\)|X\(t\+1\)) =")
frame_w = A4[0] - 40 * mm

story = list(cover)

items, kind = [], None


def flush():
    global items, kind
    if items:
        if kind == "num":
            lf = ListFlowable([ListItem(Paragraph(fmt(t), bullet), leftIndent=14) for t in items], bulletType="1",
                              bulletFontName="DejaVuSans", bulletFontSize=9.2, leftIndent=14, bulletFormat="%s.")
        else:
            lf = ListFlowable([ListItem(Paragraph(fmt(t), bullet), leftIndent=12, value="•") for t in items],
                              bulletType="bullet", bulletFontName="DejaVuSans", bulletFontSize=9.2, leftIndent=12)
        story.extend([lf, Spacer(1, 4)])
    items, kind = [], None


for ln in lines:
    s = ln.strip()
    if not s:
        flush(); continue
    if s.startswith("## "):
        flush(); story.append(Paragraph(fmt(s[3:]), h2)); continue
    m_b, m_n = s.startswith("- "), re.match(r"^\d+\. (.*)", s)
    if m_b or m_n:
        k = "bul" if m_b else "num"
        if kind and kind != k:
            flush()
        kind = k
        items.append(s[2:] if m_b else m_n.group(1)); continue
    flush()
    if EQ.match(s):
        p = Paragraph(fmt(s), eq)
        if isinstance(story[-1], Paragraph) and story[-1].text.rstrip().endswith(":"):
            p = KeepTogether([story.pop(), p])               # keep "...:" lead-in on the same page as its equation
        story.append(p); continue
    fig = next((p for key, p in FIGS.items() if s.startswith(f"**{key}**")), None)
    if fig:
        iw, ih = PILImage.open(fig).size
        story.append(KeepTogether([Spacer(1, 2), Image(fig, width=frame_w, height=frame_w * ih / iw), Spacer(1, 6)]))
    story.append(Paragraph(fmt(s), body))
flush()

doc = SimpleDocTemplate(OUT, pagesize=A4, leftMargin=20 * mm, rightMargin=20 * mm, topMargin=19 * mm,
                        bottomMargin=19 * mm, title="Reformulating the Lake Problem for Powai Lake, Mumbai - Final submission",
                        author="Prathmesh Walimbe (23B0747)", subject="CE 766 Watershed Management, final project submission")
doc.build(story, onFirstPage=cover_page, canvasmaker=NumberedCanvas)
print("saved", OUT)
