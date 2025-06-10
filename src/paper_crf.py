from functools import partial
from io import BytesIO

import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.pdfmetrics import registerFontFamily
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle

from generate_pdf.form import generate_form
from generate_pdf.guide import generate_guide_doc
from generate_pdf.header_footer import generate_header_footer
from generate_pdf.opener import generate_opener

# Register the font
try:
    pdfmetrics.registerFont(TTFont('DejaVuSans', 'BRIDGE/assets/fonts/DejaVuSans.ttf'))
    pdfmetrics.registerFont(TTFont('DejaVuSans-Bold', 'BRIDGE/assets/fonts/DejaVuSans-Bold.ttf'))
except:
    pdfmetrics.registerFont(TTFont('DejaVuSans', '../assets/fonts/DejaVuSans.ttf'))
    pdfmetrics.registerFont(TTFont('DejaVuSans-Bold', '../assets/fonts/DejaVuSans-Bold.ttf'))

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


def generate_pdf(data_dictionary, version, db_name, language, is_test=False):
    if isinstance(db_name, list):
        db_name = db_name[0]

    # Set buffer (changes based on production or test)
    if is_test:
        buffer = "Tests/" + db_name + ".pdf"  # Use BytesIO object for in-memory PDF generation
    else:
        buffer = BytesIO()  # Use BytesIO object for in-memory PDF generation

    # Remove rows where 'Field Label' starts with '>' or '->'
    data_dictionary = data_dictionary[~data_dictionary['Field Label'].str.startswith(('>', '->'))]

    root = f'https://raw.githubusercontent.com/ISARICResearch/ARC-Translations/main/{version}/{language}'

    # Get Paper-Like details and supplemental phrases from the specified language and version
    details = pd.read_csv(root + '/paper_like_details.csv', encoding='utf-8')
    supplemental_phrases = pd.read_csv(root + '/supplemental_phrases.csv', encoding='utf-8')

    # Locate the phrase in the supplemental phrases DataFrame
    def locate_phrase(variable: str) -> dict:
        try:
            phrase = supplemental_phrases.loc[supplemental_phrases['variable'] == variable, 'text'].values[0]
            return {"error": False, "text": phrase}
        except IndexError:
            print(f"Variable '{variable}' not found in supplemental phrases.")
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
    data_dictionary['Section Header'].replace('', pd.NA, inplace=True)
    data_dictionary['Section Header'].fillna(method='ffill', inplace=True)

    # Generates the form for the PaperCRF
    elements = generate_form(data_dictionary, elements, locate_phrase)

    # Finally, generate the header_footer and bild the document with it
    header_footer_partial = partial(generate_header_footer, title=db_name)
    doc.build(elements, onFirstPage=header_footer_partial, onLaterPages=header_footer_partial)

    # If production, save the pdf from memory
    if is_test:
        return None

    buffer.seek(0)
    return buffer.getvalue()  # Return the PDF data


# Function to generate separate completion guide pdf document.
def generate_completionguide(data_dictionary, version, db_name, is_test=False):
    data_dictionary = data_dictionary.copy()

    # Set buffer (changes based on production or test)
    if is_test:
        buffer = "Tests/" + version + "_completionGuide.pdf"  # Set local test pdf path
    else:
        buffer = BytesIO()  # Use BytesIO object for in-memory PDF generation

    generate_guide_doc(data_dictionary, version, db_name, buffer)

    # if test, return
    if is_test:
        return None
    # If production, save the pdf from memory
    buffer.seek(0)  # Move the cursor of the BytesIO object to the beginning
    return buffer.getvalue()  # Return the PDF data
