from pathlib import Path
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import PageBreak, Paragraph, Preformatted, SimpleDocTemplate, Spacer


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "docs" / "PROJECT_HISTORY.md"
OUTPUT = ROOT / "docs" / "PROJECT_HISTORY.pdf"
FONT_DIR = Path("C:/Windows/Fonts")


def register_fonts():
    regular = FONT_DIR / "segoeui.ttf"
    bold = FONT_DIR / "segoeuib.ttf"
    if regular.exists() and bold.exists():
        pdfmetrics.registerFont(TTFont("SegoeUI", str(regular)))
        pdfmetrics.registerFont(TTFont("SegoeUI-Bold", str(bold)))
        return "SegoeUI", "SegoeUI-Bold"
    return "Helvetica", "Helvetica-Bold"


def clean_markdown(text: str) -> str:
    return text.replace("`", "").replace("**", "").replace("*", "")


def build():
    regular, bold = register_fonts()
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle("DocTitle", parent=styles["Title"], fontName=bold, fontSize=22,
                              leading=28, alignment=TA_CENTER, textColor=colors.HexColor("#253858"),
                              spaceAfter=12))
    styles.add(ParagraphStyle("H1Custom", parent=styles["Heading1"], fontName=bold, fontSize=16,
                              leading=20, textColor=colors.HexColor("#253858"), spaceBefore=15, spaceAfter=7))
    styles.add(ParagraphStyle("H2Custom", parent=styles["Heading2"], fontName=bold, fontSize=12,
                              leading=16, textColor=colors.HexColor("#3b5b8a"), spaceBefore=10, spaceAfter=5))
    styles.add(ParagraphStyle("BodyCustom", parent=styles["BodyText"], fontName=regular, fontSize=9.2,
                              leading=13, textColor=colors.HexColor("#263238"), spaceAfter=6))
    styles.add(ParagraphStyle("BulletCustom", parent=styles["BodyText"], fontName=regular, fontSize=9.2,
                              leading=13, leftIndent=14, firstLineIndent=-8, bulletIndent=3, spaceAfter=3))
    styles.add(ParagraphStyle("Meta", parent=styles["BodyText"], fontName=regular, fontSize=8,
                              leading=11, textColor=colors.HexColor("#607d8b"), alignment=TA_CENTER))

    doc = SimpleDocTemplate(str(OUTPUT), pagesize=A4, rightMargin=18 * mm, leftMargin=18 * mm,
                            topMargin=16 * mm, bottomMargin=16 * mm, title="Project History")
    story = []
    lines = SOURCE.read_text(encoding="utf-8").splitlines()
    in_code = False
    code_lines = []
    first_title = True
    for line in lines:
        if line.strip().startswith("```"):
            if in_code:
                story.append(Preformatted("\n".join(code_lines), ParagraphStyle("Code", fontName="Courier", fontSize=7.5, leading=10,
                                                                            backColor=colors.HexColor("#f1f5f9"), borderColor=colors.HexColor("#cbd5e1"),
                                                                            borderWidth=0.5, borderPadding=6, spaceBefore=4, spaceAfter=8)))
                code_lines = []
                in_code = False
            else:
                in_code = True
            continue
        if in_code:
            code_lines.append(line)
            continue
        stripped = line.strip()
        if not stripped:
            story.append(Spacer(1, 3))
            continue
        if stripped.startswith("# "):
            title = escape(clean_markdown(stripped[2:]))
            story.append(Paragraph(title, styles["DocTitle"] if first_title else styles["H1Custom"]))
            first_title = False
        elif stripped.startswith("## "):
            story.append(Paragraph(escape(clean_markdown(stripped[3:])), styles["H1Custom"]))
        elif stripped.startswith("### "):
            story.append(Paragraph(escape(clean_markdown(stripped[4:])), styles["H2Custom"]))
        elif stripped.startswith("- "):
            story.append(Paragraph(escape(clean_markdown(stripped[2:])), styles["BulletCustom"], bulletText="•"))
        else:
            story.append(Paragraph(escape(clean_markdown(stripped)), styles["BodyCustom"]))
    doc.build(story, onFirstPage=footer, onLaterPages=footer)
    print(f"Created {OUTPUT}")


def footer(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 7)
    canvas.setFillColor(colors.HexColor("#78909c"))
    canvas.drawString(18 * mm, 9 * mm, "Runtime Security and Threat Mitigation for Autonomous LLM Agents")
    canvas.drawRightString(A4[0] - 18 * mm, 9 * mm, f"Page {doc.page}")
    canvas.restoreState()


if __name__ == "__main__":
    build()
