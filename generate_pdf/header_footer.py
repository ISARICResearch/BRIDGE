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

def generate_header_footer(canvas,doc, title):
    # Add two logos in the header
    # Get the current date
    current_date = datetime.now()

    # Format the date as required
    formatted_date = current_date.strftime("%d%b%y").upper()


    # - Header Content - #

    # Draw the first logo
    logo_scale_isaric = 0.87
    logo_scale_contagio0 = 0.165
    logo_scale_contagio1 = 2.2
    logo_scale_euro = .2
    logo_scale_flag = .021


    # Moves image to X, Y with 0,0 being bottom left hand corner.
    canvas.drawInlineImage("assets/ISARIC_logo.png", 25, 752, width=69*logo_scale_isaric, height=30*logo_scale_isaric)  #change for deploy
    
    ''' Here I was adding other logos with a fake 'opacity' applied, but have since removed
    canvas.drawInlineImage("assets/logos/contagio.jpg", 135, 759, width=344*logo_scale_contagio0, height=71*logo_scale_contagio0)  #change for deploy
    #canvas.drawInlineImage("assets/logos/CONTAGIO_Logo.jpg", 135, 747, width=25*logo_scale_contagio1, height=13*logo_scale_contagio1)  #change for deploy
    #canvas.setFillColorRGB(1, 1, 1, alpha=0.3)  # White with 50% opacity
    #canvas.rect(135, 747, width=25*logo_scale_contagio1, height=13*logo_scale_contagio1, fill=1, stroke=0)
    #canvas.drawInlineImage("assets/logos/EuroComm_sm.png", 100, 750, width=114*logo_scale_euro, height=129*logo_scale_euro)  #change for deploy
    canvas.drawInlineImage("assets/logos/FundedbytheEU.png", 97, 754, width=1304*logo_scale_flag, height=919*logo_scale_flag)  #change for deploy
    
    canvas.saveState()
    canvas.setFillColorRGB(1, 1, 1, alpha=0.3)  # White with 50% opacity
    canvas.rect(95, 749, width=100, height=30, fill=1, stroke=0)
    canvas.restoreState()
    ''' 

    #canvas.drawInlineImage("BRIDGE/assets/ISARIC_logo.png", 25, 752, width=69*logo_scale, height=30*logo_scale) 

    # Change: now the text in header and footer is a shade of grey, like in paper version
    canvas.setFillGray(0.4)

    # For the second logo, make sure it's positioned after the first logo + some spacing
    #canvas.drawInlineImage("assets/who_logo.png", 130, 730, width=98, height=30)  # adjust the width and height
    #canvas.drawInlineImage("BRIDGE/assets/who_logo.png", 130, 730, width=98, height=30)  #modify for deploy

    # Now, for the text, ensure it's positioned after the second logo + some spacing
    text_x_position = 283  # 160 + 100 + 10
    canvas.setFont("DejaVuSans", 8)
    canvas.drawString(text_x_position, 760, "PARTICIPANT IDENTIFICATION #: [___][___][___][___][___]-­‐ [___][___][___][___]")
    
    
    # - Footer content - #
    canvas.setFont("DejaVuSans", 8)
    canvas.drawString(.4 * inch, 0.45 * inch, "ISARIC "+title.upper()+" CASE REPORT FORM "+formatted_date.upper())
    canvas.setFont("DejaVuSans", 6)
    canvas.drawString(.4* inch, 0.3 * inch, "Licensed under a Creative Commons Attribution-ShareAlike 4.0 International License by ISARIC on behalf of the University of Oxford.")

    # Draw page number on the bottom right
    canvas.setFont("DejaVuSans", 9)     
    page_text = str(doc.page)
    canvas.drawRightString(8 * inch, .4 * inch, page_text)