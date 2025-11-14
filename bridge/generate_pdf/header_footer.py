from datetime import datetime

from reportlab.lib.units import inch
from reportlab.pdfgen.canvas import Canvas
from reportlab.platypus.doctemplate import SimpleDocTemplate

CURRENT_DATE = datetime.now()
FORMATTED_DATE = CURRENT_DATE.strftime("%d%b%y").upper()
ISARIC_LOGO = 'assets/ISARIC_logo.png'
LICENSE_TEXT = "Licensed under a Creative Commons Attribution-ShareAlike 4.0 International License by ISARIC on behalf of the University of Oxford."


def set_paperlike_header_content(canvas: Canvas):
    # Draw the first logo
    logo_scale_isaric = 0.87

    # Moves image to X, Y with 0,0 being bottom left hand corner.
    canvas.drawInlineImage(
        ISARIC_LOGO,
        25,
        752,
        width=69 * logo_scale_isaric,
        height=30 * logo_scale_isaric,
    )

    # Text in header and footer is a shade of grey, like in paper version
    canvas.setFillGray(0.4)

    # Ensure it's positioned after the second logo + some spacing
    canvas.setFont("DejaVuSans", 8)
    canvas.drawString(
        283,
        760,
        "PARTICIPANT IDENTIFICATION #: [___][___][___][___][___]-­‐ [___][___][___][___]",
    )


def set_paperlike_footer_content(canvas: Canvas,
                                 title: str):
    canvas.setFont("DejaVuSans", 8)
    canvas.drawString(
        .4 * inch, 0.45 * inch,
        f'ISARIC {title.upper()} CASE REPORT FORM {FORMATTED_DATE}',
    )
    canvas.setFont("DejaVuSans", 6)
    canvas.drawString(
        .4 * inch, 0.3 * inch,
        LICENSE_TEXT,
    )


def draw_paperlike_page_number(canvas: Canvas,
                               doc: SimpleDocTemplate):
    # Draw page number on the bottom right
    canvas.setFont("DejaVuSans", 9)
    page_text = str(doc.page)
    canvas.drawRightString(
        8 * inch,
        .4 * inch,
        page_text,
    )


def generate_paperlike_header_footer(canvas: Canvas,
                                     doc: SimpleDocTemplate,
                                     title: str):
    set_paperlike_header_content(canvas)
    set_paperlike_footer_content(canvas, title)
    draw_paperlike_page_number(canvas, doc)


def set_completion_guide_header_content(canvas: Canvas):
    # Draw the first logo
    logo_scale_isaric = 0.7

    # Moves image to X, Y with 0,0 being bottom left hand corner.
    canvas.drawInlineImage(
        ISARIC_LOGO,
        25,
        755,
        width=69 * logo_scale_isaric,
        height=30 * logo_scale_isaric,
    )

    # Text in header and footer is a shade of grey, like in paper version
    canvas.setFillGray(0.4)

    # Ensure it's positioned after the second logo + some spacing
    canvas.setFont("DejaVuSans", 8)


def set_completion_guide_footer_content(canvas: Canvas,
                                        title: str):
    canvas.setFont("DejaVuSans", 8)
    canvas.drawString(
        .4 * inch, 0.45 * inch,
        f'ISARIC {title.upper()} COMPLETION GUIDE {FORMATTED_DATE}',
    )
    canvas.setFont("DejaVuSans", 6)
    canvas.drawString(
        .4 * inch, 0.3 * inch,
        LICENSE_TEXT,
    )

    # Draw page number on the bottom right
    canvas.setFont("DejaVuSans", 9)


def get_page_numeral(page_number: int) -> str:
    match page_number:
        case 1:
            return "i"
        case 2:
            return "ii"
        case 3:
            return "iii"
        case 4:
            return "iv"
        case 5:
            return "v"
        case 6:
            return "vi"
        case 7:
            return "vii"
        case 8:
            return "viii"
        case 9:
            return "ix"
        case 10:
            return "x"
        case _:
            return "_"


def get_page_number_text(doc: SimpleDocTemplate,
                         toc_pages: int) -> str:
    if doc.page <= toc_pages:
        page_numeral = get_page_numeral(doc.page)
        return page_numeral
    else:
        page_number = str(doc.page - toc_pages)
        return page_number


def draw_completion_guide_page_number(canvas: Canvas,
                                      doc: SimpleDocTemplate,
                                      toc_pages: int):
    page_text = get_page_number_text(doc, toc_pages)
    canvas.drawRightString(
        8 * inch,
        .4 * inch,
        page_text,
    )


def generate_completion_guide_header_footer(canvas: Canvas,
                                            doc: SimpleDocTemplate,
                                            title: str,
                                            toc_pages: int = 0):
    set_completion_guide_header_content(canvas)
    set_completion_guide_footer_content(canvas, title)
    draw_completion_guide_page_number(canvas, doc, toc_pages)
