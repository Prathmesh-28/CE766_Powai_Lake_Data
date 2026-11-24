/*
 * Build the Word version of the final report from CE766_Final_Submission_Text.md (the same source as the PDF).
 * Page 1 is the IIT Bombay-style cover page (faded logo behind the text); later pages carry the logo in the
 * header and a "CE766 | ... Page x of y" footer.
 * Run from the repository root:   npm install docx    then    node code/make_docx.js
 * Output: CE766_Final_Submission_PowaiLake.docx
 */
const fs = require("fs");
const path = require("path");
const {
  Document, Packer, Paragraph, TextRun, ImageRun, Header, Footer, AlignmentType, HeadingLevel, PageNumber,
  ExternalHyperlink, LevelFormat, BorderStyle, Tab, TabStopType, HorizontalPositionRelativeFrom,
  VerticalPositionRelativeFrom, HorizontalPositionAlign, TextWrappingType,
} = require("docx");

const ROOT = path.resolve(__dirname, "..");
const MD = path.join(ROOT, "CE766_Final_Submission_Text.md");
const OUT = path.join(ROOT, "CE766_Final_Submission_PowaiLake.docx");
const FIGS = {
  "Figure 1.": path.join(ROOT, "figures", "Figure1_pareto_robustness.png"),
  "Figure 2.": path.join(ROOT, "figures", "Figure2_trajectories_prim.png"),
};
const LOGO = path.join(ROOT, "figures", "iitb_logo.png");
const WMARK = path.join(ROOT, "figures", "iitb_logo_watermark.png");

const FONT = "Times New Roman";
const NAVY = "1F3864", BLUE = "0070C0", HEAD = "1F4E79", RULE = "4F81BD", LINK = "1A5FB4";
const PX_PER_MM = 96 / 25.4;   // docx-js image sizes are pixels at 96 dpi
const TWIP_PER_MM = 56.693;    // page measures are twentieths of a point
const TEXT_W_MM = 210 - 2 * 25;

function pngSize(file) {       // width and height from the PNG header
  const b = fs.readFileSync(file);
  return { w: b.readUInt32BE(16), h: b.readUInt32BE(20) };
}
function image(file, widthMm, extra = {}) {
  const { w, h } = pngSize(file);
  const width = widthMm * PX_PER_MM;
  return new ImageRun({ type: "png", data: fs.readFileSync(file), transformation: { width, height: (width * h) / w }, ...extra });
}

// ---------------- inline markdown -> runs (same rules as code/make_pdf.py) ----------------
const SCRIPT = /\b(A|Q|TP|P|e|v|p)_(C|L|STP|raw|eff|yr|u|s|h)\b|\bf0\b|\^(\w)|yr⁻¹/g;

function scriptRuns(text, fmt) {   // ordinary text with subscripts and superscripts
  const out = [];
  const run = (t, o = {}) => out.push(new TextRun({ text: t, ...fmt, ...o }));
  let last = 0, m;
  SCRIPT.lastIndex = 0;
  while ((m = SCRIPT.exec(text)) !== null) {
    if (m.index > last) run(text.slice(last, m.index));
    if (m[1]) { run(m[1]); run(m[2], { subScript: true }); }
    else if (m[0] === "f0") { run("f"); run("0", { subScript: true }); }
    else if (m[3]) run(m[3], { superScript: true });
    else { run("yr"); run("−1", { superScript: true }); }
    last = m.index + m[0].length;
  }
  if (last < text.length) run(text.slice(last));
  return out;
}

function inline(s, fmt = {}) {
  s = s.replace(/\((\S+) − (\S+?)\)/g, "($1 − $2)")   // keep short formulas such as (1 − u) on one line
       .replace(/(\d) ± (\d)/g, "$1 ± $2");
  const TOK = /\*\*(.+?)\*\*|(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?![\w*])|`([^`]+)`|(https?:\/\/\S+)/g;
  const out = [];
  let last = 0, m;
  while ((m = TOK.exec(s)) !== null) {
    if (m.index > last) out.push(...scriptRuns(s.slice(last, m.index), fmt));
    if (m[1] !== undefined) out.push(...inline(m[1], { ...fmt, bold: true }));
    else if (m[2] !== undefined) out.push(...inline(m[2], { ...fmt, italics: true }));
    else if (m[3] !== undefined) out.push(new TextRun({ text: m[3], ...fmt, font: "Courier New", size: 21 }));
    else {
      const url = m[4].replace(/[.,;)]+$/, "");
      const tail = m[4].slice(url.length);
      out.push(new ExternalHyperlink({ link: url, children: [new TextRun({ text: url, ...fmt, color: LINK, underline: {} })] }));
      if (tail) out.push(new TextRun({ text: tail, ...fmt }));
    }
    last = TOK.lastIndex;
  }
  if (last < s.length) out.push(...scriptRuns(s.slice(last), fmt));
  return out;
}

// ---------------- cover page (layout, fonts and colours of the CE769 report cover) ----------------
function coverLine(text, o = {}) {
  return new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { before: Math.round((o.beforeMm || 0) * TWIP_PER_MM), after: 0, line: 360 },
    children: [
      ...(o.anchor ? [o.anchor] : []),
      new TextRun({ text, font: FONT, size: o.size || 28, bold: true, italics: !!o.italics, color: o.color || "000000",
                    underline: o.underline ? {} : undefined }),
    ],
  });
}
const watermark = image(WMARK, 165, {
  floating: {
    horizontalPosition: { relative: HorizontalPositionRelativeFrom.PAGE, align: HorizontalPositionAlign.CENTER },
    verticalPosition: { relative: VerticalPositionRelativeFrom.PAGE, offset: Math.round(58 * 36000) },
    behindDocument: true, allowOverlap: true, lockAnchor: true, wrap: { type: TextWrappingType.NONE }, zIndex: 0,
  },
});
const cover = [
  coverLine("A Report on", { color: NAVY, beforeMm: 10, anchor: watermark }),
  coverLine("REFORMULATING THE LAKE PROBLEM", { size: 31, beforeMm: 4 }),
  coverLine("FOR POWAI LAKE, MUMBAI", { size: 31 }),
  coverLine("(Robust Phosphorus Management after Sewage Diversion)", { size: 27, beforeMm: 2 }),
  coverLine("CE766 Course Project Report:", { beforeMm: 22 }),
  coverLine("Watershed Management"),
  coverLine("Submitted by", { italics: true, beforeMm: 12 }),
  coverLine("Prathmesh Walimbe (23B0747)", { color: BLUE, beforeMm: 2 }),
  coverLine("Submission Date: 24 November 2026", { color: NAVY, underline: true, beforeMm: 30 }),
  coverLine("Department of Civil Engineering", { beforeMm: 10 }),
  coverLine("Indian Institute of Technology Bombay"),
  coverLine("Powai, Mumbai - 400076"),
];

// ---------------- header (logo) and footer ("CE766 | ...   Page x of y") ----------------
const header = new Header({ children: [new Paragraph({ alignment: AlignmentType.RIGHT, children: [image(LOGO, 13.2)] })] });
const f = (o) => new TextRun({ font: FONT, size: 20, ...o });
const footer = new Footer({
  children: [new Paragraph({
    border: { top: { style: BorderStyle.SINGLE, size: 12, color: RULE, space: 4 } },
    tabStops: [{ type: TabStopType.RIGHT, position: Math.round(TEXT_W_MM * TWIP_PER_MM) }],
    children: [
      f({ text: "CE766 | Powai Lake Phosphorus Management", bold: true }),
      f({ children: [new Tab(), "Page "] }),
      f({ children: [PageNumber.CURRENT], bold: true }), f({ text: " of " }), f({ children: [PageNumber.TOTAL_PAGES], bold: true }),
    ],
  })],
});
const blank = { header: new Header({ children: [new Paragraph({})] }), footer: new Footer({ children: [new Paragraph({})] }) };

// ---------------- parse the markdown (everything after the "---" rule) ----------------
const all = fs.readFileSync(MD, "utf8").split(/\r?\n/);
const lines = all.slice(all.indexOf("---") + 1);
const EQ = /^(Q\(t\)|L\(t\)|X\(t\+1\)) =/;
const blocks = [];
for (const ln of lines) {
  const s = ln.trim();
  if (!s) continue;
  if (s.startsWith("## ")) blocks.push({ kind: "h", text: s.slice(3) });
  else if (s.startsWith("- ")) blocks.push({ kind: "bul", text: s.slice(2) });
  else if (/^\d+\. /.test(s)) blocks.push({ kind: "num", text: s.replace(/^\d+\. /, "") });
  else if (EQ.test(s)) blocks.push({ kind: "eq", text: s });
  else blocks.push({ kind: "p", text: s });
}

const body = [];
let firstHeading = true;
blocks.forEach((b, i) => {
  const next = blocks[i + 1] || {};
  if (b.kind === "h") {
    body.push(new Paragraph({ heading: HeadingLevel.HEADING_1, pageBreakBefore: firstHeading, children: inline(b.text) }));
    firstHeading = false;
  } else if (b.kind === "bul" || b.kind === "num") {
    body.push(new Paragraph({
      numbering: { reference: b.kind === "bul" ? "bullets" : "refs", level: 0 },
      alignment: b.kind === "bul" ? AlignmentType.JUSTIFIED : AlignmentType.LEFT,
      spacing: { after: 60, line: 276 }, children: inline(b.text),
    }));
  } else if (b.kind === "eq") {
    body.push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 60, after: 180 }, keepLines: true,
                              keepNext: next.kind === "eq", children: inline(b.text) }));
  } else {
    const fig = Object.keys(FIGS).find((k) => b.text.startsWith(`**${k}**`));
    if (fig) {
      body.push(new Paragraph({ alignment: AlignmentType.CENTER, keepNext: true, spacing: { before: 120, after: 120 },
                                children: [image(FIGS[fig], TEXT_W_MM)] }));
    }
    const leadIn = b.text.endsWith(":") && next.kind === "eq";
    const refs = b.text.startsWith("**Other sources") || b.text.startsWith("**Data and code");
    body.push(new Paragraph({
      alignment: refs ? AlignmentType.LEFT : AlignmentType.JUSTIFIED, keepNext: leadIn || next.kind === "bul",
      spacing: { after: 120, line: 276 }, children: inline(b.text),
    }));
  }
});

// ---------------- document ----------------
const listLevel = (format, text) => ({
  level: 0, format, text, alignment: AlignmentType.LEFT,
  style: { paragraph: { indent: { left: 567, hanging: 340 } } },
});
const mm = (v) => Math.round(v * TWIP_PER_MM);
const doc = new Document({
  creator: "Prathmesh Walimbe",
  lastModifiedBy: "Prathmesh Walimbe",
  title: "Reformulating the Lake Problem for Powai Lake, Mumbai",
  description: "CE766 Watershed Management: final project report",
  styles: {
    default: {
      document: { run: { font: FONT, size: 24 } },
      heading1: {
        run: { font: FONT, size: 28, bold: true, color: HEAD },
        paragraph: { spacing: { before: 280, after: 120 }, keepNext: true, keepLines: true },
      },
    },
  },
  numbering: {
    config: [
      { reference: "bullets", levels: [listLevel(LevelFormat.BULLET, "•")] },
      { reference: "refs", levels: [listLevel(LevelFormat.DECIMAL, "%1.")] },
    ],
  },
  sections: [{
    properties: {
      titlePage: true,
      page: { size: { width: 11906, height: 16838 },
              margin: { top: mm(25), bottom: mm(25), left: mm(25), right: mm(25), header: mm(7), footer: mm(10) } },
    },
    headers: { default: header, first: blank.header },
    footers: { default: footer, first: blank.footer },
    children: [...cover, ...body],
  }],
});

Packer.toBuffer(doc).then((buf) => {
  fs.writeFileSync(OUT, buf);
  console.log("saved", OUT);
});
