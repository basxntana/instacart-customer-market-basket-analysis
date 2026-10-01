"""Minimal Markdown -> PDF renderer (reportlab). Handles the subset used by the report:
headings, paragraphs, bullet/numbered lists, pipe tables, fenced blocks, blockquotes, rules."""
import re, sys, pathlib, html
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.lib.enums import TA_LEFT
from reportlab.platypus import (BaseDocTemplate, PageTemplate, Frame, Paragraph, Spacer,
                                Table, TableStyle, HRFlowable, KeepTogether, Preformatted)

INK, MUT, GRID, S1, S2 = colors.HexColor("#0B0B0B"), colors.HexColor("#52514E"), \
                         colors.HexColor("#E6E5E1"), colors.HexColor("#2A78D6"), colors.HexColor("#EB6834")
BODY = "Helvetica"; BOLD = "Helvetica-Bold"; ITAL = "Helvetica-Oblique"; MONO = "Courier"

S = {
 "h1": ParagraphStyle("h1", fontName=BOLD, fontSize=21, leading=25, textColor=INK, spaceBefore=4, spaceAfter=7),
 "h2": ParagraphStyle("h2", fontName=BOLD, fontSize=14.5, leading=18, textColor=INK, spaceBefore=17, spaceAfter=7),
 "h3": ParagraphStyle("h3", fontName=BOLD, fontSize=11.6, leading=14.5, textColor=INK, spaceBefore=12, spaceAfter=5),
 "h4": ParagraphStyle("h4", fontName=BOLD, fontSize=10.2, leading=13, textColor=S1, spaceBefore=9, spaceAfter=3),
 "p":  ParagraphStyle("p", fontName=BODY, fontSize=9.5, leading=13.6, textColor=INK, spaceAfter=6.5, alignment=TA_LEFT),
 "li": ParagraphStyle("li", fontName=BODY, fontSize=9.5, leading=13.4, textColor=INK,
                      leftIndent=13, bulletIndent=3, spaceAfter=3.5),
 "quote": ParagraphStyle("quote", fontName=ITAL, fontSize=9.8, leading=14, textColor=INK,
                         leftIndent=11, borderPadding=(5,5,5,8), spaceBefore=6, spaceAfter=8,
                         backColor=colors.HexColor("#FFF6EE")),
 "sub": ParagraphStyle("sub", fontName=BODY, fontSize=10.5, leading=14, textColor=MUT, spaceAfter=10),
 "cell": ParagraphStyle("cell", fontName=BODY, fontSize=7.9, leading=10.2, textColor=INK),
 "cellb": ParagraphStyle("cellb", fontName=BOLD, fontSize=7.9, leading=10.2, textColor=colors.white),
 "pre": ParagraphStyle("pre", fontName=MONO, fontSize=7, leading=8.6, textColor=MUT),
}

def inline(t: str) -> str:
    t = html.escape(t)
    t = re.sub(r"`([^`]+)`", r'<font face="Courier" size="8.6">\1</font>', t)
    t = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", t)
    t = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"<i>\1</i>", t)
    t = t.replace("—", "\u2014").replace("→", "\u2192").replace("↔", "\u2194")
    return t

def split_row(line):
    return [c.strip() for c in line.strip().strip("|").split("|")]

def build(md: str):
    flow, lines, i = [], md.split("\n"), 0
    while i < len(lines):
        ln = lines[i]
        if ln.startswith("```"):
            i += 1; buf = []
            while i < len(lines) and not lines[i].startswith("```"):
                buf.append(lines[i]); i += 1
            i += 1
            flow.append(Preformatted("\n".join(buf), S["pre"])); flow.append(Spacer(1, 6)); continue
        if re.match(r"^\|.*\|\s*$", ln) and i+1 < len(lines) and re.match(r"^\|[\s:\-|]+\|\s*$", lines[i+1]):
            hdr = split_row(ln); i += 2; rows = []
            while i < len(lines) and re.match(r"^\|.*\|\s*$", lines[i]):
                rows.append(split_row(lines[i])); i += 1
            n = len(hdr)
            data = [[Paragraph(inline(c), S["cellb"]) for c in hdr]]
            for r in rows:
                r = (r + [""]*n)[:n]
                data.append([Paragraph(inline(c), S["cell"]) for c in r])
            # Width by content: a "#" column should not get the same space as a sentence.
            avail = 168*mm
            raw = []
            for c in range(n):
                longest = max([len(hdr[c])] + [len((r + [""]*n)[c]) for r in rows])
                words = [w for cell in [hdr[c]] + [(r + [""]*n)[c] for r in rows]
                         for w in cell.split()]
                longest_word = max([len(w) for w in words] + [4])
                raw.append(max(4.0, min(float(longest), 62.0)))
                raw[c] = max(raw[c], float(longest_word), 7.0)
            tot = sum(raw)
            widths = [avail * w / tot for w in raw]
            # never let a column fall below ~11mm or it wraps one character per line
            floor = 16*mm
            short = [i2 for i2, w in enumerate(widths) if w < floor]
            if short:
                need = sum(floor - widths[i2] for i2 in short)
                donors = [i2 for i2 in range(n) if widths[i2] > floor]
                pool = sum(widths[i2] - floor for i2 in donors) or 1
                for i2 in donors:
                    widths[i2] -= need * (widths[i2] - floor) / pool
                for i2 in short:
                    widths[i2] = floor
            t = Table(data, colWidths=widths, repeatRows=1, hAlign="LEFT")
            t.setStyle(TableStyle([
                ("BACKGROUND",(0,0),(-1,0), S1),
                ("TEXTCOLOR",(0,0),(-1,0), colors.white),
                ("VALIGN",(0,0),(-1,-1),"TOP"),
                ("TOPPADDING",(0,0),(-1,-1),3.4), ("BOTTOMPADDING",(0,0),(-1,-1),3.4),
                ("LEFTPADDING",(0,0),(-1,-1),4.5), ("RIGHTPADDING",(0,0),(-1,-1),4.5),
                ("LINEBELOW",(0,0),(-1,-1),0.4, GRID),
                ("ROWBACKGROUNDS",(0,1),(-1,-1),[colors.white, colors.HexColor("#FAFAF8")]),
            ]))
            flow.append(Spacer(1,3)); flow.append(t); flow.append(Spacer(1,9)); continue
        if re.match(r"^---+\s*$", ln):
            flow.append(Spacer(1,5)); flow.append(HRFlowable(width="100%", thickness=0.6, color=GRID))
            flow.append(Spacer(1,7)); i += 1; continue
        m = re.match(r"^(#{1,4})\s+(.*)$", ln)
        if m:
            lvl = len(m.group(1)); flow.append(Paragraph(inline(m.group(2)), S[f"h{lvl}"])); i += 1; continue
        if ln.startswith(">"):
            buf = []
            while i < len(lines) and lines[i].startswith(">"):
                buf.append(lines[i].lstrip("> ").rstrip()); i += 1
            flow.append(Paragraph(inline(" ".join(buf)), S["quote"])); continue
        m = re.match(r"^(\s*)([-*]|\d+\.)\s+(.*)$", ln)
        if m:
            indent = len(m.group(1))
            bullet = "\u2022" if m.group(2) in "-*" else m.group(2)
            buf = [m.group(3)]; i += 1
            while i < len(lines) and lines[i].strip() \
                  and not re.match(r"^\s*([-*]|\d+\.)\s+", lines[i]) \
                  and not lines[i].startswith(("#", "|", ">", "```")) \
                  and not re.match(r"^---+\s*$", lines[i]):
                buf.append(lines[i].strip()); i += 1
            st = ParagraphStyle("x", parent=S["li"], leftIndent=13+indent*8, bulletIndent=3+indent*8)
            flow.append(Paragraph(inline(" ".join(buf)), st, bulletText=bullet)); continue
        if not ln.strip():
            i += 1; continue
        buf = [ln.strip()]; i += 1
        # NB: test for a real list marker, not merely a leading "*" — a continuation line
        # that begins with **bold** is still the same paragraph.
        while i < len(lines) and lines[i].strip() \
              and not lines[i].startswith(("#", "|", ">", "```")) \
              and not re.match(r"^\s*([-*]|\d+\.)\s+", lines[i]) \
              and not re.match(r"^---+\s*$", lines[i]):
            buf.append(lines[i].strip()); i += 1
        txt = " ".join(buf)
        style = S["sub"] if txt.startswith("###") else S["p"]
        flow.append(Paragraph(inline(txt), style))
    return flow

def render(md_path, pdf_path, title, footer):
    doc = BaseDocTemplate(str(pdf_path), pagesize=A4,
                          leftMargin=21*mm, rightMargin=21*mm, topMargin=18*mm, bottomMargin=17*mm,
                          title=title, author="Data Analyst")
    frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id="n")
    def deco(canvas, d):
        canvas.saveState()
        canvas.setFont(BODY, 7.4); canvas.setFillColor(MUT)
        canvas.drawString(doc.leftMargin, 10*mm, footer)
        canvas.drawRightString(A4[0]-doc.leftMargin, 10*mm, f"{canvas.getPageNumber()}")
        canvas.setStrokeColor(GRID); canvas.setLineWidth(0.4)
        canvas.line(doc.leftMargin, 13*mm, A4[0]-doc.leftMargin, 13*mm)
        canvas.restoreState()
    doc.addPageTemplates([PageTemplate(id="n", frames=[frame], onPage=deco)])
    doc.build(build(pathlib.Path(md_path).read_text()))
    print(f"wrote {pdf_path} ({pathlib.Path(pdf_path).stat().st_size/1024:.0f} KB)")

if __name__ == "__main__":
    render(sys.argv[1], sys.argv[2], sys.argv[3] if len(sys.argv)>3 else "Report",
           sys.argv[4] if len(sys.argv)>4 else "")
