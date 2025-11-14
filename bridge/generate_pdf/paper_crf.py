from functools import partial
from io import BytesIO
from os.path import join, dirname, abspath

import numpy as np
import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.pdfmetrics import registerFontFamily
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle

from bridge.arc.arc_core import ArcApiClient
from bridge.generate_pdf.form import generate_form
from bridge.generate_pdf.guide import generate_guide_doc
from bridge.generate_pdf.header_footer import generate_paperlike_header_footer
from bridge.generate_pdf.opener import generate_opener
from bridge.logging.logger import setup_logger

pd.options.mode.copy_on_write = True

logger = setup_logger(__name__)

ASSETS_DIR_FULL = join(dirname(dirname(dirname(abspath(__file__)))), 'assets')
FONTS_DIR_FULL = join(ASSETS_DIR_FULL, 'fonts')

pdfmetrics.registerFont(TTFont('DejaVuSans', join(FONTS_DIR_FULL, 'DejaVuSans.ttf')))
pdfmetrics.registerFont(TTFont('DejaVuSans-Bold', join(FONTS_DIR_FULL, 'DejaVuSans-Bold.ttf')))

# Register font family
registerFontFamily(
    'DejaVuSans',
    normal='DejaVuSans',
    bold='DejaVuSans-Bold'
)


def create_table(data):
    table = Table(data, colWidths=[2.5 * inch, 4 * inch])
    style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('SPAN', (0, 0), (-1, 0))
    ])

    for idx, _ in enumerate(data):
        if len(data[idx]) == 1:  # it's a section
            style.add('BACKGROUND', (0, idx), (-1, idx), colors.grey)
            style.add('SPAN', (0, idx), (-1, idx))

    table.setStyle(style)
    return table


def generate_paperlike_pdf(data_dictionary, version, db_name, language):
    buffer = BytesIO()  # Use BytesIO object for in-memory PDF generation

    # Remove rows where 'Field Label' starts with '>' or '->'
    data_dictionary = data_dictionary[~data_dictionary['Field Label'].str.startswith(('>', '->'))]

    # Get Paper-Like details and supplemental phrases from the specified language and version
    details = ArcApiClient().get_dataframe_paper_like_details(version, language)
    supplemental_phrases = ArcApiClient().get_dataframe_supplemental_phrases(version, language)

    # Locate the phrase in the supplemental phrases DataFrame
    def locate_phrase(variable: str) -> dict:
        try:
            phrase = supplemental_phrases.loc[supplemental_phrases['variable'] == variable, 'text'].values[0]
            return {"error": False, "text": phrase}
        except IndexError:
            logger.warning(f"Variable '{variable}' not found in supplemental phrases.")
            return {"error": True, "text": ""}

    # Define margin widths for the document as a whole
    left_margin = 0.3 * inch
    right_margin = 0.3 * inch
    top_margin = 0.7 * inch
    bottom_margin = 0.7 * inch

    # Create new document from template with defined margins
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        leftMargin=left_margin,
        rightMargin=right_margin,
        topMargin=top_margin,
        bottomMargin=bottom_margin
    )

    # elements is an array holding each item to be added to the pdf from "generate_opener" and "generate_form"
    elements = []

    # Generates the opening information for the PaperCRF
    elements = generate_opener(elements, details, db_name)

    # Grouping by 'Section Header' instead of 'Form Name'
    data_dictionary['Section Header'] = data_dictionary['Section Header'].replace({'': np.nan})

    # Generates the form for the PaperCRF
    elements = generate_form(data_dictionary, elements, locate_phrase)

    # Finally, generate the header_footer and bild the document with it
    header_footer_partial = partial(generate_paperlike_header_footer, title=db_name)
    doc.build(elements, onFirstPage=header_footer_partial, onLaterPages=header_footer_partial)

    buffer.seek(0)
    return buffer.getvalue()  # Return the PDF data


# Function to generate separate completion guide pdf document.
def generate_completion_guide(data_dictionary, version, db_name):
    data_dictionary = data_dictionary.copy()

    buffer = BytesIO()  # Use BytesIO object for in-memory PDF generation

    generate_guide_doc(data_dictionary, version, db_name, buffer)

    # If production, save the pdf from memory
    buffer.seek(0)  # Move the cursor of the BytesIO object to the beginning
    return buffer.getvalue()  # Return the PDF data
