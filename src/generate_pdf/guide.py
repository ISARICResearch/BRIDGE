import re
from copy import deepcopy
from functools import partial

import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.platypus import Paragraph, PageBreak, BaseDocTemplate, \
    PageTemplate, Frame, Flowable
from reportlab.platypus import Spacer, NextPageTemplate

from src.generate_pdf.header_footer import generate_guide_header_footer


class StyleSet:
    def __init__(self):
        styles = getSampleStyleSheet()

        blue = colors.hsl2rgb(.57, .6, .35)
        self.hex_blue = '#%02x%02x%02x' % tuple(int(c * 255) for c in blue)

        self.normal = deepcopy(styles['Normal'])
        self.normal.fontSize = 7
        self.normal.leading = 9
        self.normal.firstLineIndent = -2
        self.normal.leftIndent = 5
        self.normal.fontName = 'DejaVuSans'

        self.form = deepcopy(styles['Heading1'])
        self.form.fontSize = 12
        self.form.leading = 12
        self.form.fontName = 'DejaVuSans'
        self.form.textColor = blue

        self.section = deepcopy(styles['Heading1'])
        self.section.fontSize = 9
        self.section.leading = 10
        self.section.fontName = 'DejaVuSans'
        self.section.textColor = blue


# Instantiate once, then reuse
style = StyleSet()


class TrackingParagraph(Paragraph):
    def __init__(self, text, style, key, kind):
        super().__init__(text, style)
        self.key = key  # the form or section name
        self.kind = kind  # either 'form' or 'section'


class TrackingDocTemplate(BaseDocTemplate):
    def __init__(self, *args, **kwargs):
        self.toc_entries = []  # Store TOC entries as (kind, title, key, page_number)
        super().__init__(*args, **kwargs)

    def afterFlowable(self, flowable):
        if isinstance(flowable, TrackingParagraph):
            page_num = self.page
            self.toc_entries.append({
                'kind': flowable.kind,
                'title': flowable.getPlainText(),
                'key': flowable.key,
                'page': page_num
            })


def generate_guide_doc(data_dictionary, version, crf_name, buffer):
    # Define margin widths for the document as a whole
    left_margin = 0.3 * inch
    right_margin = 0.3 * inch
    top_margin = 0.5 * inch
    bottom_margin = 0.5 * inch

    page_width, page_height = letter

    # Two columns: split usable width
    usable_width = page_width - left_margin - right_margin
    column_width = (usable_width - 0.2 * inch) / 2  # small gutter between columns
    column_height = page_height - top_margin - bottom_margin

    guide_title = version + ", " + crf_name

    header_footer_partial = partial(generate_guide_header_footer, title=guide_title)

    # First page: single column, same margins
    frame_one_col = Frame(left_margin, bottom_margin, usable_width, column_height, id='one_col')
    template_one_col = PageTemplate(id='OneCol', frames=[frame_one_col], onPage=header_footer_partial)

    # Two-column page (already defined)
    frame1 = Frame(left_margin, bottom_margin, column_width, column_height, id='two_col1')
    frame2 = Frame(left_margin + column_width + 0.2 * inch, bottom_margin, column_width, column_height, id='two_col2')
    template_two_col = PageTemplate(id='TwoCol', frames=[frame1, frame2], onPage=header_footer_partial)

    # Create the document with the custom template
    doc = TrackingDocTemplate(
        buffer,
        pagesize=letter,
        leftMargin=left_margin,
        rightMargin=right_margin,
        topMargin=top_margin,
        bottomMargin=bottom_margin
    )

    doc.addPageTemplates([template_one_col, template_two_col])

    # First pass: Build and collect TOC data
    elements = [NextPageTemplate('TwoCol')] + generate_guide_content(data_dictionary)
    doc.build(elements)

    # Second pass: Rebuild with TOC inserted at the top
    toc = create_table_of_contents(doc.toc_entries)

    final_elements = toc + [NextPageTemplate('TwoCol'), PageBreak()] + generate_guide_content(data_dictionary)

    doc = TrackingDocTemplate(
        buffer,
        pagesize=letter,
        leftMargin=left_margin,
        rightMargin=right_margin,
        topMargin=top_margin,
        bottomMargin=bottom_margin
    )

    doc.addPageTemplates([template_one_col, template_two_col])
    doc.build(final_elements)


def generate_guide_content(data_dictionary):
    elements = []

    # Assume 'header_footer' function is defined elsewhere
    # and 'data_dictionary' processing is as before

    # Process data_dictionary and add Paragraphs to elements
    data_dictionary['Section'].replace('', pd.NA, inplace=True)
    data_dictionary['Section'].fillna(method='ffill', inplace=True)

    current_form = ""
    current_section = ""

    for index, row in data_dictionary.iterrows():
        if '_oth' in row['Variable']: continue
        if '_units' in row['Variable']: continue

        # Add a new Form header
        if type(row['Form']) == str:
            if row['Form'] != current_form:
                current_form = row['Form']
                elements.append(Spacer(1, 0.07 * inch))
                elements.append(TrackingParagraph(row['Form'].upper() + " FORM", style.form, row['Form'],
                                                  'form'))  # is my tracking paragraph correct?
                elements.append(Spacer(1, 0.07 * inch))
        # Add a new Section header
        if type(row['Section']) == str:
            if row['Section'] != current_section:
                current_section = row['Section']
                elements.append(TrackingParagraph(row['Section'].title(), style.section, row['Section'],
                                                  'section'))  # is my tracking paragraph correct?
        elements.append(
            Paragraph(("<b>" + row['Question'] + "</b>: " + row['Definition'] + " " + row['Completion Guideline']),
                      style.normal))
        elements.append(Spacer(1, 0.07 * inch))

    return elements


class TOCEntry(Flowable):
    def __init__(self, title, page, style, width, dot_color=colors.black, line_y=4):
        Flowable.__init__(self)
        self.title = title
        self.page = str(page)
        self.style = style
        self.width = width
        self.dot_color = dot_color
        self.line_y = line_y  # vertical offset of dotted line

    def wrap(self, avail_width, avail_height):
        self.height = self.style.leading
        return avail_width, self.height

    def draw(self):
        canvas = self.canv
        canvas.saveState()

        # Draw title Paragraph
        text_obj = Paragraph(self.title, self.style)
        tw, th = text_obj.wrap(self.width - 50, self.height)
        text_obj.drawOn(canvas, 0, 0)

        def strip_tags(text):
            return re.sub(r'<[^>]*>', '', text)

        # Accurately measure raw string width (strip HTML if needed)
        title_plain = self.title.replace('&nbsp;', ' ')
        title_width = stringWidth(strip_tags(title_plain), self.style.fontName, self.style.fontSize)

        # Page number
        page_obj = Paragraph(self.page, self.style)
        pw, ph = page_obj.wrap(50, self.height)
        page_x = self.width - pw

        # Dotted line between title and page number
        canvas.setStrokeColor(self.dot_color)
        canvas.setDash(1, 2)
        canvas.line(title_width + 10, self.line_y, page_x - 2, self.line_y)
        canvas.setDash(1, 0)

        # Draw page number
        page_obj.drawOn(canvas, page_x, 0)

        canvas.restoreState()


def create_table_of_contents(toc_entries, total_width=560):
    styles = getSampleStyleSheet()
    toc_style = styles["Normal"]
    toc_style.fontName = 'DejaVuSans'
    toc_style.fontSize = 9
    toc_style.leading = 13
    toc_style.leftIndent = 5

    elements = [Paragraph("<b>Table of Contents</b>", styles["Heading1"]), Spacer(1, 0.1 * inch)]

    for entry in toc_entries:
        title = entry["title"].split(':')[0].strip()
        kind = entry["kind"]
        indent = "&nbsp;&nbsp;&nbsp;&nbsp;" if kind == "section" else ""
        entry_text = f"{indent}<font color={style.hex_blue}>{title}</font>"
        if kind == "form":
            elements.append(Spacer(1, 0.1 * inch))
        elements.append(TOCEntry(entry_text, entry["page"], toc_style, total_width))

    return elements
