from reportlab.lib.styles import getSampleStyleSheet
from copy import deepcopy

line_placeholder='_' * 40
   
# So at the moment, one table is made and added to our elements array, before returning the elements array.

# I am interested in chunking this into new tables for each 

# Get the predefined styles
styles = getSampleStyleSheet()

normal = styles['Normal']
normal.fontSize = 8
normal.fontName = 'DejaVuSans'  # Use the registered font
normal.leading = 10

center = deepcopy(styles['Normal'])
center.alignment = 1  # Center alignment

conditional_text = deepcopy(styles['Normal'])
conditional_text.fontSize = 8

section_header = deepcopy(styles['Normal'])
section_header.fontSize = 10
section_header.fontName = 'DejaVuSans-Bold'

form_header = styles['Heading1']
form_header.fontSize = 12
form_header.leading = 12
form_header.fontName = 'DejaVuSans-Bold'  # Use the registered font
form_header.leftIndent = -2

title = styles['Title']
title.fontSize = 16
title.leading = 20
title.fontName = 'DejaVuSans-Bold'