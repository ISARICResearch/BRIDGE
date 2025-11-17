""" This Generate Form script is for generating and storing styles """

from copy import deepcopy
from typing import Literal

from reportlab.lib.styles import getSampleStyleSheet

registered_font = 'DejaVuSans'
registered_font_bold = 'DejaVuSans-Bold'

line_placeholder = '_' * 40

styles = getSampleStyleSheet()

normal = styles['Normal']
normal.fontSize = 8
normal.fontName = registered_font
normal.leading = 10

center = deepcopy(styles['Normal'])
center.alignment = 1

conditional_text = deepcopy(styles['Normal'])
conditional_text.fontSize = 8

section_header = deepcopy(styles['Normal'])
section_header.fontSize = 10
section_header.fontName = 'DejaVuSans-Bold'

form_header = styles['Heading1']
form_header.fontSize = 12
form_header.leading = 12
form_header.fontName = registered_font_bold
form_header.leftIndent = -2

title = styles['Title']
title.fontSize = 16
title.leading = 20
title.fontName = registered_font_bold

RowShade = Literal[
    'none',
    'conditional',
    'descriptive',
]

SectionType = Literal[
    'standard',
    'medication',
    'testing',
]

SubsubsectionType = Literal[
    'separate_items',
    'conditional_group',
    'conditional_isolates',
    'section_header',
    'descriptive_header',
]
