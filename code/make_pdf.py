"""
Build the submission PDF from CE766_Final_Submission_Text.md (single source of truth) and the two figures.
Run from the repository root:   python code/make_pdf.py
Output: CE766_Final_Submission_PowaiLake.pdf
"""
import os, re, html
import matplotlib
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Image, ListFlowable, ListItem,
                                KeepTogether, HRFlowable)

HERE = os.path.dirname(os.path.abspath(__file__))
SUB = os.path.dirname(HERE)                                # repository root
MD = os.path.join(SUB, "CE766_Final_Submission_Text.md")
OUT = os.path.join(SUB, "CE766_Final_Submission_PowaiLake.pdf")
FIGS = {"Figure 1.": os.path.join(SUB, "figures", "Figure1_pareto_robustness.png"),
        "Figure 2.": os.path.join(SUB, "figures", "Figure2_trajectories_prim.png")}

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
title = ParagraphStyle("title", fontName="DejaVuSans-Bold", fontSize=16.5, leading=21, textColor=NAVY, spaceAfter=3)
subtitle = ParagraphStyle("subtitle", fontName="DejaVuSans", fontSize=10.5, leading=14, textColor=INK2, spaceAfter=7)
meta = ParagraphStyle("meta", fontName="DejaVuSans", fontSize=9.2, leading=13, textColor=INK, spaceAfter=2)

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
        w, h = A4
        self.setStrokeColor(RULE); self.setLineWidth(0.6)
        self.line(20 * mm, h - 13 * mm, w - 20 * mm, h - 13 * mm)
        self.line(20 * mm, 13 * mm, w - 20 * mm, 13 * mm)
        self.setFont("DejaVuSans", 7.8); self.setFillColor(INK2)
        self.drawString(20 * mm, h - 11 * mm, "CE 766: Watershed Management (Fall 2026)")
        self.drawRightString(w - 20 * mm, h - 11 * mm, "Final Project Submission")
        self.drawString(20 * mm, 9 * mm, "Prathmesh Walimbe (23B0747)")
        self.drawRightString(w - 20 * mm, 9 * mm, f"Page {self._pageNumber} of {n}")


# ---------------- parse the markdown ----------------
lines = open(MD, encoding="utf-8").read().splitlines()
lines = lines[lines.index("---") + 1:]                     # skip the md title / upload note above the rule
EQ = re.compile(r"^(Q\(t\)|L\(t\)|X\(t\+1\)) =")
frame_w = A4[0] - 40 * mm

story = [
    Paragraph("Reformulating the Lake Problem for Powai Lake, Mumbai", title),
    Paragraph("Final submission: robust phosphorus management after sewage diversion", subtitle),
    Paragraph("<b>Name:</b> Prathmesh Walimbe &nbsp;&nbsp;&nbsp; <b>Roll No.:</b> 23B0747", meta),
    Paragraph('<b>Repository:</b> <a href="https://github.com/Prathmesh-28/CE766_Powai_Lake_Data" color="#1a5fb4">'
              "github.com/Prathmesh-28/CE766_Powai_Lake_Data</a>", meta),
    Spacer(1, 3), HRFlowable(width="100%", thickness=0.8, color=RULE, spaceBefore=2, spaceAfter=4),
]

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
        from PIL import Image as PILImage
        iw, ih = PILImage.open(fig).size
        story.append(KeepTogether([Spacer(1, 2), Image(fig, width=frame_w, height=frame_w * ih / iw), Spacer(1, 6)]))
    story.append(Paragraph(fmt(s), body))
flush()

doc = SimpleDocTemplate(OUT, pagesize=A4, leftMargin=20 * mm, rightMargin=20 * mm, topMargin=19 * mm,
                        bottomMargin=19 * mm, title="Reformulating the Lake Problem for Powai Lake, Mumbai - Final submission",
                        author="Prathmesh Walimbe (23B0747)", subject="CE 766 Watershed Management, final project submission")
doc.build(story, canvasmaker=NumberedCanvas)
print("saved", OUT)
