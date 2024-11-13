import pandas as pd
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, PageBreak
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from copy import deepcopy
from reportlab.platypus import Spacer
from io import BytesIO
from functools import partial
from datetime import datetime

# custom functions to generate sections of paperCRF
from generate_form import generate_form
from generate_opener import generate_opener


try:
# Register the font
    pdfmetrics.registerFont(TTFont('DejaVuSans', 'BRIDGE/assets/fonts/DejaVuSans.ttf'))
    pdfmetrics.registerFont(TTFont('DejaVuSans-Bold', 'BRIDGE/assets/fonts/DejaVuSans-Bold.ttf'))
except:
    pdfmetrics.registerFont(TTFont('DejaVuSans', 'assets/fonts/DejaVuSans.ttf'))
    pdfmetrics.registerFont(TTFont('DejaVuSans-Bold', 'assets/fonts/DejaVuSans-Bold.ttf'))
line_placeholder='_' * 30

def header_footer(canvas, doc,title):
    # Add two logos in the header
    # Get the current date
    current_date = datetime.now()

    # Format the date as required
    formatted_date = current_date.strftime("%d%b%y").upper()

    # Draw the first logo
    canvas.drawInlineImage("assets/ISARIC_logo.png", 50, 730, width=69, height=30)  #change for deploy# adjust the width and height accordingly
    #canvas.drawInlineImage("BRIDGE/assets/ISARIC_logo.png", 50, 730, width=69, height=30)  

    # For the second logo, make sure it's positioned after the first logo + some spacing
    #canvas.drawInlineImage("assets/who_logo.png", 130, 730, width=98, height=30)  # adjust the width and height
    #canvas.drawInlineImage("BRIDGE/assets/who_logo.png", 130, 730, width=98, height=30)  #modify for deploy

    # Now, for the text, ensure it's positioned after the second logo + some spacing
    text_x_position = 270  # 160 + 100 + 10
    canvas.setFont("DejaVuSans", 8)
    canvas.drawString(text_x_position, 730, "PARTICIPANT IDENTIFICATION #: [___][___][___][___][___]-­‐ [___][___][___][___]")
    # Footer content

    canvas.setFont("DejaVuSans", 8)
    canvas.drawString(inch, 0.95 * inch, "ISARIC "+title.upper()+" CASE REPORT FORM "+formatted_date.upper())
    canvas.setFont("DejaVuSans", 6)
    canvas.drawString(inch, 0.75 * inch, "Licensed under a Creative Commons Attribution-ShareAlike 4.0 International License by ISARIC on behalf of the University of Oxford.")


def create_table(data):
    table = Table(data, colWidths=[2.5*inch, 4*inch])
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

def generate_pdf(data_dictionary, version, db_name):
    if isinstance(db_name, list):
        db_name=db_name[0]

    data_dictionary = data_dictionary[~data_dictionary['Field Label'].str.startswith(('>', '->'))]



    #root='https://raw.githubusercontent.com/ISARICResearch/DataPlatform/main/ARCH/'
    root='ARC/'
    icc_version_path = root+version
    details = pd.read_csv(icc_version_path+'/paper_like_details.csv', encoding='latin-1')


    buffer = BytesIO()  # Use BytesIO object for in-memory PDF generation
    doc = SimpleDocTemplate(buffer, pagesize=letter)

    elements = []


    # Aidan: I created two new files and dedicated functions: generate_opener and generate_form
    # This simple refactor will help me as I go on 

    # Generates the opening information for the PaperCRF
    elements = generate_opener(elements, details, db_name)


    ###########################################################################
    #elements.append(PageBreak()) # Aidan: I removed this following Yannik Update
    #doc = SimpleDocTemplate(output_pdf_path, pagesize=letter)
    #elements = []

    # Get the predefined styles
    #styles = getSampleStyleSheet() # Aidan: I removed this following Yannik Update

    data_dictionary['Section Header'].replace('', pd.NA, inplace=True)
    data_dictionary['Section Header'].fillna(method='ffill', inplace=True)


    # Grouping by 'Section Header' instead of 'Form Name'

    # Generates the fillable form for the PaperCRF
    elements = generate_form(doc, data_dictionary, elements)

    #doc.build(elements, onFirstPage=header_footer, onLaterPages=header_footer)
    header_footer_partial = partial(header_footer, title=db_name)
    doc.build(elements, onFirstPage=header_footer_partial, onLaterPages=header_footer_partial)
    buffer.seek(0)

    return buffer.getvalue()  # Return the PDF data



def generate_completionguide(data_dictionary, version, db_name):
    data_dictionary = data_dictionary.copy()
    #root = 'https://raw.githubusercontent.com/ISARICResearch/DataPlatform/main/ARCH/'
    root = 'ARC/'
    icc_version_path = root + version
    details = pd.read_csv(icc_version_path + '/paper_like_details.csv', encoding='latin-1')

    buffer = BytesIO()  # Use BytesIO object for in-memory PDF generation
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    elements = []

    # Get the predefined styles and configure them
    styles = getSampleStyleSheet()
    normal_style = deepcopy(styles['Normal'])
    normal_style.fontSize = 8
    normal_style.leading = 10
    normal_style.fontName = 'DejaVuSans'

    header_style = deepcopy(styles['Heading1'])
    header_style.fontSize = 10
    header_style.leading = 12
    header_style.fontName = 'DejaVuSans-Bold'

    # Assume 'header_footer' function is defined elsewhere
    # and 'data_dictionary' processing is as before

    # Process data_dictionary and add Paragraphs to elements
    data_dictionary['Section'].replace('', pd.NA, inplace=True)
    data_dictionary['Section'].fillna(method='ffill', inplace=True)

    for index, row in data_dictionary.iterrows():
        elements.append(Paragraph(row['Question'], header_style))
        elements.append(Paragraph(row['Definition'], normal_style))
        elements.append(Paragraph(row['Completion Guideline'], normal_style))

    # Build the document
    doc.build(elements)  # Removed the onFirstPage and onLaterPages for simplicity

    # Move the cursor of the BytesIO object to the beginning
    buffer.seek(0)
    return buffer.getvalue()  # Return the PDF data
