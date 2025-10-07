import re
from copy import deepcopy
from functools import partial

import numpy as np
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.platypus import Paragraph, PageBreak, BaseDocTemplate, \
    PageTemplate, Frame, Flowable
from reportlab.platypus import Spacer, NextPageTemplate

from bridge.generate_pdf.header_footer import generate_guide_header_footer

from bridge.logging.logger import setup_logger
logger = setup_logger(__name__)

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


### TrackingParagraph is an extenstion of the ReportLab Paragraph Class
# key is the the name of either the form or section
# kind is whether it is a form or section
# This lets us go back for each item and get what page it is on
class TrackingParagraph(Paragraph):
    def __init__(self, text, style, name=None, key=None, kind=None, **kwargs):
        logger.debug(f"TrackingParagraph init: kind={kind} key={key} name={name}")
        super().__init__(text, style, **kwargs)
        self.name = name
        self.key = key  # the form or section name
        self.kind = kind  # either 'form' or 'section'
    def split(self, availWidth, availHeight):
        """
        Preserve the bookmark key on the first fragment only,
        so at least one part defines the destination when drawn.
        """
        parts = super().split(availWidth, availHeight)
        if len(parts) > 1:
            logger.debug(f"TrackingParagraph {self.key} split into {len(parts)}, keeping key on first fragment.")
            for i, p in enumerate(parts):
                if isinstance(p, TrackingParagraph):
                    if i == 0:
                        # first fragment keeps the key for bookmark registration
                        p.key = self.key
                        p.kind = self.kind
                    else:
                        # other fragments should not trigger afterflowable
                        p.key = None
                        p.kind = None
        return parts


### Tracking Doc Template is an extension of the ReportLab BaseDocTemplate Class
# After eacbh Tracking Paragraph is drawn, it adds an entry to table of contents entries.
# Each entry has kind, key, title, and page number.
class TrackingDocTemplate(BaseDocTemplate):
    def __init__(self, *args, **kwargs):
        self.toc_entries = []
        self.created_bookmarks = set()
        super().__init__(*args, **kwargs)

    def afterFlowable(self, flowable):
        if not isinstance(flowable, TrackingParagraph):
            return

        key = getattr(flowable, "key", None)
        title = flowable.getPlainText()
        page_num = self.page

        logger.debug(f"afterFlowable: page={page_num} key={key!r} kind={getattr(flowable,'kind',None)} title={title}")

        # Detect missing keys early
        if not key:
            logger.warning(f"afterFlowable: Missing key for {title[:50]}")
            return

        # Try to add the bookmark and outline entry, log any failures
        try:
            self.canv.bookmarkPage(key)
            self.created_bookmarks.add(key)
            self.canv.addOutlineEntry(title, key, level=0, closed=False)
            self.toc_entries.append({
                "kind": getattr(flowable, "kind", ""),
                "title": title,
                "key": key,
                "page": page_num,
                "paragraph": flowable,
            })
            logger.debug(f"afterFlowable: registered bookmark {key} on page {page_num}")
        except Exception as e:
            # Log the failure in detail
            import traceback
            tb = traceback.format_exc(limit=1).strip()
            logger.error(f"afterFlowable: FAILED for key={key!r} on page {page_num}: {e} ({tb})")

        # Check if multiple bookmarks share this key
        if key in [t["key"] for t in self.toc_entries[:-1]]:
            logger.warning(f"afterFlowable: duplicate bookmark key detected -> {key}")




### TOCEntry is a ReportLab Flowable to handle the fancy styling of each entry in the table of contents
# Handles color, width, everything.
# Most of the complexity comes from finding the width of the line and creating it.
class TOCEntry(Flowable):
    def __init__(self, title, page, style, width, key, paragraph, dot_color=colors.black, line_y=4):
        Flowable.__init__(self)
        self.title = title
        self.page = str(page)
        self.style = style
        self.width = width
        self.key = key
        self.paragraph = paragraph
        self.dot_color = dot_color
        self.line_y = line_y  # vertical offset of dotted line
        self.valid_bookmark = True  # Assume valid by default

    def wrap(self, availWidth, availHeight):
        self.height = self.style.leading
        return availWidth, self.height

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
        title_width = stringWidth(strip_tags(
            title_plain), self.style.fontName, self.style.fontSize)

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

        # if paragraph, draw the link, else don't draw link
        if self.paragraph:
            # Draw link rectangle
            canvas.linkRect(
                '',  # contents
                self.key,  # destination
                (0, 0, self.width, self.height),  # rect
                relative=1,
                thickness=0
            )
        else:
            # If no paragraph, just draw a rectangle without a link
            canvas.rect(0, 0, self.width, self.height, fill=1, stroke=1)

        canvas.restoreState()


### generate_guide_doc is our main funciton. Handles input dictionary, doc margins, creating 2 columns and
# when to use them, generating the doc twice, once to get page numbers and once to add TOC.
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

    header_footer_partial = partial(
        generate_guide_header_footer, title=guide_title)

    # First page: single column, same margins
    frame_one_col = Frame(left_margin, bottom_margin,
                          usable_width, column_height, id='one_col')
    template_one_col = PageTemplate(
        id='OneCol', frames=[frame_one_col], onPage=header_footer_partial)

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
    logger.info("Generating Table of Contents")
    toc = create_table_of_contents(doc.toc_entries, 560, page_height - top_margin - bottom_margin)

    header_footer_partial = partial(
        generate_guide_header_footer, title=guide_title, toc_pages=toc["pages"])
    
    logger.info("Rebuilding one col document")
    template_one_col = PageTemplate(
        id='OneCol', frames=[frame_one_col], onPage=header_footer_partial)
    logger.info("Rebuilding two col document")
    template_two_col = PageTemplate(
        id='TwoCol', frames=[frame1, frame2], onPage=header_footer_partial)

    final_elements = toc['elements'] + [NextPageTemplate('TwoCol'), PageBreak()] + generate_guide_content(
        data_dictionary)

    doc = TrackingDocTemplate(
        buffer,
        pagesize=letter,
        leftMargin=left_margin,
        rightMargin=right_margin,
        topMargin=top_margin,
        bottomMargin=bottom_margin
    )

    doc.addPageTemplates([template_one_col, template_two_col])
    logger.info("Building final document")
    doc.build(final_elements)
    logger.info("Final guide document build complete")


### generate_guide_content actually generates the completion guide from a data_dictionary json
def generate_guide_content(data_dictionary):
    def sanitize_key(text):
        if text is None:
            raise ValueError("Cannot create key from None")
        # Convert to string if not already
        text = str(text)
        # Remove special characters and limit length
        safe_text = re.sub(r'[^a-zA-Z0-9_]', '_', text)
        return safe_text[:100]

    elements = []

    # Assume 'header_footer' function is defined elsewhere
    # and 'data_dictionary' processing is as before

    # Process data_dictionary and add Paragraphs to elements
    data_dictionary['Section'] = data_dictionary['Section'].replace({'': np.nan})

    current_form = ""
    current_section = ""

    items = []
    guide_to_omit = ""

    for index, row in data_dictionary.iterrows():
        form = row['Form']
        section = row['Section']
        variable = row['Variable']
        question = row['Question'].strip(" :")
        definition = row['Definition']
        guide = row['Completion Guideline']

        ### Omit needless rows.
        # No not add others those long >-> additional variables.
        if '_oth' in variable:                  continue
        if '_units' in variable:                continue
        if (question.startswith(('>', '->'))):  continue
        if (variable.endswith('addi')):         continue

        ### Add Form and Section Headers when needed
        # we track when needed with current_form and current_section
        # Add a new Form header
        if isinstance(form, str):
            if form != current_form:
                items = []
                key = sanitize_key(f"form_{index}_{form}_{section}")
                # New Form
                current_form = form
                elements.append(Spacer(1, 0.07 * inch))
                # is my tracking paragraph correct?
                elements.append(TrackingParagraph(form.upper() + " FORM", style.form, form, key, 'form'))
                elements.append(Spacer(1, 0.07 * inch))

        # Add a new Section header
        if isinstance(section, str):
            if section != current_section:
                if (variable.startswith(('sign_'))):
                    guides = []
                    for index, row in data_dictionary.iterrows():
                        if variable.startswith(('sign_')):
                            guides.append(row['Completion Guideline'])

                    guide_to_omit = max(set(guides), key=guides.count)
                elif (variable.startswith(('sympt_'))):
                    guides = []
                    for index, row in data_dictionary.iterrows():
                        if variable.startswith(('sympt_')):
                            guides.append(row['Completion Guideline'])

                    guide_to_omit = max(set(guides), key=guides.count)
                else:
                    guide_to_omit = ""

                items = []
                current_section = section

                key = sanitize_key(f"sec_{index}_{form}_{section}")

                elements.append(TrackingParagraph(
                    section.title(),
                    style.section,
                    section,
                    key,
                    "section"
                ))
                elements.append(Spacer(1, 0.07 * inch))

        if variable.startswith(('sign_', 'sympt_')):
            if guide == guide_to_omit:
                guide = ""

        item = question + definition + guide

        if item in items:
            # Finally, add the paragraph element for the specific varibale and its guide.
            elements.append(Paragraph("<b>" + question + ":</b> See Above.", style.normal))
            elements.append(Spacer(1, 0.07 * inch))

        else:
            items.append(item)

            # Finally, add the paragraph element for the specific varibale and its guide.
            elements.append(Paragraph("<b>" + question + ":</b> " +
                                      definition + " " + guide, style.normal))
            elements.append(Spacer(1, 0.07 * inch))

    return elements


### generates a table of contents for the completion guide based on the generated
# toc_entries (a list of dictionaries to hold key information (key, kind, title, page_num))
def create_table_of_contents(toc_entries, total_width, total_height):
    styles = getSampleStyleSheet()
    toc_style = styles["Normal"]
    toc_style.fontName = 'DejaVuSans'
    toc_style.fontSize = 9
    toc_style.leading = 13
    toc_style.leftIndent = 5

    # Track the height used for the TOC to know number of pages
    height_used = 2

    header_paragraph = Paragraph("<b>Table of Contents</b>", styles["Heading1"])
    elements = [header_paragraph, Spacer(1, 0.1 * inch)]

    header_paragraph.height = header_paragraph.wrap(total_width, 0)[1]
    height_used += header_paragraph.height + 0.1 * inch  # Add height

    height_used += 0.1 * inch

    for entry in toc_entries:
        if not entry["key"]:
            continue  # Skip entries with None/empty keys
        title = entry["title"].split(':')[0].strip()
        kind = entry["kind"]
        indent = "&nbsp;&nbsp;&nbsp;&nbsp;" if kind == "section" else ""
        entry_text = f"{indent}<font color={style.hex_blue}>{title}</font>"
        if kind == "form":
            elements.append(Spacer(1, 0.1 * inch))
            height_used += 0.1 * inch

        toc_entry = TOCEntry(entry_text, entry["page"], toc_style, total_width, entry["key"], entry["paragraph"])
        elements.append(toc_entry)
        height_used += 13  # Height of each TOC entry is 13

    page_total = int((height_used + total_height - 1) // total_height)

    return {"elements": elements, "pages": page_total}
