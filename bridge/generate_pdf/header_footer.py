from datetime import datetime
import dash
from reportlab.lib.units import inch


def generate_header_footer(canvas, doc, title):
    current_date = datetime.now()
    formatted_date = current_date.strftime("%d%b%y").upper()

    # - Header Content - #
    # Draw the first logo
    logo_scale_isaric = 0.87

    # Moves image to X, Y with 0,0 being bottom left hand corner.
    canvas.drawInlineImage("assets/ISARIC_logo.png", 25, 752, width=69 * logo_scale_isaric,
                           height=30 * logo_scale_isaric)  # change for deploy

    # Change: now the text in header and footer is a shade of grey, like in paper version
    canvas.setFillGray(0.4)

    # Now, for the text, ensure it's positioned after the second logo + some spacing
    text_x_position = 283  # 160 + 100 + 10
    canvas.setFont("DejaVuSans", 8)
    canvas.drawString(text_x_position, 760,
                      "PARTICIPANT IDENTIFICATION #: [___][___][___][___][___]-­‐ [___][___][___][___]")

    # - Footer content - #
    canvas.setFont("DejaVuSans", 8)
    canvas.drawString(.4 * inch, 0.45 * inch, "ISARIC " + title.upper() + " CASE REPORT FORM " + formatted_date.upper())
    canvas.setFont("DejaVuSans", 6)
    canvas.drawString(.4 * inch, 0.3 * inch,
                      "Licensed under a Creative Commons Attribution-ShareAlike 4.0 International License by ISARIC on behalf of the University of Oxford.")

    # Draw page number on the bottom right
    canvas.setFont("DejaVuSans", 9)
    page_text = str(doc.page)
    canvas.drawRightString(8 * inch, .4 * inch, page_text)


def generate_guide_header_footer(canvas, doc, title, toc_pages=0):
    current_date = datetime.now()
    formatted_date = current_date.strftime("%d%b%y").upper()

    # - Header Content - #
    # Draw the first logo
    logo_scale_isaric = 0.7

    # Moves image to X, Y with 0,0 being bottom left hand corner.
    canvas.drawInlineImage("assets/ISARIC_logo.png", 25, 755, width=69 * logo_scale_isaric,
                           height=30 * logo_scale_isaric)  # change for deploy

    # Change: now the text in header and footer is a shade of grey, like in paper version
    canvas.setFillGray(0.4)

    # Now, for the text, ensure it's positioned after the second logo + some spacing
    canvas.setFont("DejaVuSans", 8)

    # - Footer content - #
    canvas.setFont("DejaVuSans", 8)
    canvas.drawString(.4 * inch, 0.45 * inch, "ISARIC " + title.upper() + " COMPLETION GUIDE " + formatted_date.upper())
    canvas.setFont("DejaVuSans", 6)
    canvas.drawString(.4 * inch, 0.3 * inch,
                      "Licensed under a Creative Commons Attribution-ShareAlike 4.0 International License by ISARIC on behalf of the University of Oxford.")

    # Draw page number on the bottom right
    canvas.setFont("DejaVuSans", 9)

    def pageNum():
        if doc.page <= toc_pages:
            if doc.page == 1: return "i"
            if doc.page == 2: return "ii"
            if doc.page == 3: return "iii"
            if doc.page == 4: return "iv"
            if doc.page == 5: return "v"
            if doc.page == 6: return "vi"
            if doc.page == 7: return "vii"
            if doc.page == 8: return "viii"
            if doc.page == 9: return "ix"
            if doc.page == 10: return "x"
            return "_"
        else:
            return str(doc.page - toc_pages)

    page_text = pageNum()
    canvas.drawRightString(8 * inch, .4 * inch, page_text)
