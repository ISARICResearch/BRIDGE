import re
import traceback
from copy import deepcopy
from functools import partial
from typing import Tuple

import numpy as np
import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, PropertySet
from reportlab.lib.units import inch
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.platypus import (
    Paragraph,
    PageBreak,
    BaseDocTemplate,
    PageTemplate,
    Frame,
    Flowable,
)
from reportlab.platypus import Spacer, NextPageTemplate

from bridge.generate_pdf.header_footer import generate_completion_guide_header_footer
from bridge.logging.logger import setup_logger

logger = setup_logger(__name__)

REGISTERED_FONT = "DejaVuSans"


class StyleSet:
    def __init__(self):
        styles = getSampleStyleSheet()

        blue = colors.hsl2rgb(0.57, 0.6, 0.35)
        self.hex_blue = "#%02x%02x%02x" % tuple(int(c * 255) for c in blue)

        self.normal = deepcopy(styles["Normal"])
        self.normal.fontSize = 7
        self.normal.leading = 9
        self.normal.firstLineIndent = -2
        self.normal.leftIndent = 5
        self.normal.fontName = REGISTERED_FONT

        self.form = deepcopy(styles["Heading1"])
        self.form.fontSize = 12
        self.form.leading = 12
        self.form.fontName = REGISTERED_FONT
        self.form.textColor = blue

        self.section = deepcopy(styles["Heading1"])
        self.section.fontSize = 9
        self.section.leading = 10
        self.section.fontName = REGISTERED_FONT
        self.section.textColor = blue


STYLE = StyleSet()


class TrackingParagraph(Paragraph):
    """
    TrackingParagraph is an extension of the ReportLab Paragraph Class.
    This lets us go back for each item and get what page it is on.

    Attributes:
        key: name of the form or section
        kind: 'form' or 'section'
    """

    def __init__(
        self,
        text: str,
        style: PropertySet,
        name: str = None,
        key: str = None,
        kind: str = None,
        **kwargs,
    ):
        logger.debug(f"TrackingParagraph init: kind={kind} key={key} name={name}")
        super().__init__(text, style, **kwargs)
        self.name = name
        self.key = key
        self.kind = kind

        assert self.kind in [None, "form", "section"]

    def split(self, avail_width, avail_height) -> list:
        """
        Preserve the bookmark key on the first fragment only,
        so at least one part defines the destination when drawn.
        """
        parts = super().split(avail_width, avail_height)
        if len(parts) > 1:
            logger.debug(
                f"TrackingParagraph {self.key} split into {len(parts)}, keeping key on first fragment."
            )
            for index, paragraph in enumerate(parts):
                if isinstance(paragraph, TrackingParagraph):
                    if index == 0:
                        # first fragment keeps the key for bookmark registration
                        paragraph.key = self.key
                        paragraph.kind = self.kind
                    else:
                        # other fragments should not trigger afterflowable
                        paragraph.key = None
                        paragraph.kind = None
        return parts


class TrackingDocTemplate(BaseDocTemplate):
    """
    TrackingDocTemplate an extension of the ReportLab BaseDocTemplate Class.
    After each Tracking Paragraph is drawn, it adds an entry to table of contents entries.
    Each entry has kind, key, title, and page number.
    """

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

        logger.debug(
            f"afterFlowable: page={page_num} key={key!r} kind={getattr(flowable, 'kind', None)} title={title}"
        )

        # Detect missing keys early
        if not key:
            logger.warning(f"afterFlowable: Missing key for {title[:50]}")
            return

        # Try to add the bookmark and outline entry, log any failures
        try:
            self.canv.bookmarkPage(key)
            self.created_bookmarks.add(key)
            self.canv.addOutlineEntry(title, key, level=0, closed=False)
            self.toc_entries.append(
                {
                    "kind": getattr(flowable, "kind", ""),
                    "title": title,
                    "key": key,
                    "page": page_num,
                    "paragraph": flowable,
                }
            )
            logger.debug(f"afterFlowable: registered bookmark {key} on page {page_num}")
        except Exception as e:
            # Log the failure in detail
            tb = traceback.format_exc(limit=1).strip()
            logger.error(
                f"afterFlowable: FAILED for key={key!r} on page {page_num}: {e} ({tb})"
            )

        # Check if multiple bookmarks share this key
        if key in [t["key"] for t in self.toc_entries[:-1]]:
            logger.warning(f"afterFlowable: duplicate bookmark key detected -> {key}")


class TOCEntry(Flowable):
    """
    OCEntry is a ReportLab Flowable to handle the fancy styling of each entry in the table of contents.
    Handles color, width, everything.
    Most of the complexity comes from finding the width of the line and creating it.
    """

    def __init__(
        self,
        title: str,
        page: int,
        style: PropertySet,
        width: float,
        key: str,
        paragraph: TrackingParagraph,
        dot_color: colors.Color = colors.black,
        line_y: int = 4,
    ):
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

    def wrap(self, avail_width: float, avail_height: float) -> Tuple[float, float]:
        self.height = self.style.leading
        return (
            avail_width,
            self.height,
        )

    @staticmethod
    def _strip_tags(text: str) -> str:
        return re.sub(r"<[^>]*>", "", text)

    def draw(self):
        canvas = self.canv
        canvas.saveState()

        # Draw title Paragraph
        text_obj = Paragraph(self.title, self.style)
        text_obj.wrap(self.width - 50, self.height)
        text_obj.drawOn(canvas, 0, 0)

        # Accurately measure raw string width (strip HTML if needed)
        title_plain = self.title.replace("&nbsp;", " ")
        title_width = stringWidth(
            self._strip_tags(title_plain),
            self.style.fontName,
            self.style.fontSize,
        )

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
                "",  # contents
                self.key,  # destination
                (0, 0, self.width, self.height),  # rect
                relative=1,
                thickness=0,
            )
        else:
            # If no paragraph, just draw a rectangle without a link
            canvas.rect(0, 0, self.width, self.height, fill=1, stroke=1)

        canvas.restoreState()


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
        generate_completion_guide_header_footer, title=guide_title
    )

    # First page: single column, same margins
    frame_one_col = Frame(
        left_margin, bottom_margin, usable_width, column_height, id="one_col"
    )
    template_one_col = PageTemplate(
        id="OneCol", frames=[frame_one_col], onPage=header_footer_partial
    )

    # Two-column page (already defined)
    frame1 = Frame(
        left_margin, bottom_margin, column_width, column_height, id="two_col1"
    )
    frame2 = Frame(
        left_margin + column_width + 0.2 * inch,
        bottom_margin,
        column_width,
        column_height,
        id="two_col2",
    )
    template_two_col = PageTemplate(
        id="TwoCol", frames=[frame1, frame2], onPage=header_footer_partial
    )

    # Create the document with the custom template
    doc = TrackingDocTemplate(
        buffer,
        pagesize=letter,
        leftMargin=left_margin,
        rightMargin=right_margin,
        topMargin=top_margin,
        bottomMargin=bottom_margin,
    )
    doc.addPageTemplates([template_one_col, template_two_col])

    # First pass: Build and collect TOC data
    element_list = [NextPageTemplate("TwoCol")] + _generate_guide_content(
        data_dictionary
    )

    try:
        doc.build(element_list)
    except ValueError as e:
        logger.error(e)
        raise RuntimeError("Failed to build Completion Guide")

    # Second pass: Rebuild with TOC inserted at the top
    logger.info("Generating Table of Contents")
    toc = _create_table_of_contents(
        doc.toc_entries, 560, page_height - top_margin - bottom_margin
    )

    header_footer_partial = partial(
        generate_completion_guide_header_footer,
        title=guide_title,
        toc_pages=toc["pages"],
    )

    logger.info("Rebuilding one col document")
    template_one_col = PageTemplate(
        id="OneCol", frames=[frame_one_col], onPage=header_footer_partial
    )
    logger.info("Rebuilding two col document")
    template_two_col = PageTemplate(
        id="TwoCol", frames=[frame1, frame2], onPage=header_footer_partial
    )

    final_element_list = (
        toc["elements"]
        + [NextPageTemplate("TwoCol"), PageBreak()]
        + _generate_guide_content(data_dictionary)
    )

    doc = TrackingDocTemplate(
        buffer,
        pagesize=letter,
        leftMargin=left_margin,
        rightMargin=right_margin,
        topMargin=top_margin,
        bottomMargin=bottom_margin,
    )

    doc.addPageTemplates([template_one_col, template_two_col])
    logger.info("Building final Completion Guide")
    try:
        doc.build(final_element_list)
    except ValueError as e:
        logger.error(e)
        raise RuntimeError("Failed to build Completion Guide")
    logger.info("Final Completion Guide build complete")


def _sanitize_key(text: str) -> str:
    if text is None:
        raise ValueError("Cannot create key from None")
    text = str(text)
    # Remove special characters and limit length
    safe_text = re.sub(r"[^a-zA-Z0-9_]", "_", text)
    return safe_text[:100]


def _generate_guide_content(df_datadicc: pd.DataFrame) -> list:
    """
    Generates the completion guide from a data_dictionary json.
    """

    element_list = []

    # Process data_dictionary and add Paragraphs to elements
    df_datadicc["Section"] = df_datadicc["Section"].replace({"": np.nan})

    current_form = ""
    current_section = ""

    items = []
    guide_to_omit = ""

    for index, row in df_datadicc.iterrows():
        form = row["Form"]
        section = row["Section"]
        variable = row["Variable"]
        question = row["Question"].strip(" :")
        definition = row["Definition"]
        guide = row["Completion Guideline"]

        ### Omit needless rows.
        # No not add others those long >-> additional variables.
        if "_oth" in variable:
            continue
        if "_units" in variable:
            continue
        if question.startswith((">", "->")):
            continue
        if variable.endswith("addi"):
            continue

        ### Add Form and Section Headers when needed
        # we track when needed with current_form and current_section
        # Add a new Form header
        if isinstance(form, str):
            if form != current_form:
                items = []
                key = _sanitize_key(f"form_{index}_{form}_{section}")
                # New Form
                current_form = form
                element_list.append(Spacer(1, 0.07 * inch))
                # is my tracking paragraph correct?
                element_list.append(
                    TrackingParagraph(
                        f"{form.upper()} FORM",
                        STYLE.form,
                        form,
                        key,
                        "form",
                    )
                )
                element_list.append(Spacer(1, 0.07 * inch))

        # Add a new Section header
        if isinstance(section, str):
            if section != current_section:
                if variable.startswith("sign_"):
                    guides = []
                    for _, row_data in df_datadicc.iterrows():
                        if variable.startswith("sign_"):
                            guides.append(row_data["Completion Guideline"])

                    guide_to_omit = max(set(guides), key=guides.count)
                elif variable.startswith("sympt_"):
                    guides = []
                    for _, row_data in df_datadicc.iterrows():
                        if variable.startswith("sympt_"):
                            guides.append(row_data["Completion Guideline"])

                    guide_to_omit = max(set(guides), key=guides.count)
                else:
                    guide_to_omit = ""

                items = []
                current_section = section

                key = _sanitize_key(f"sec_{index}_{form}_{section}")

                element_list.append(
                    TrackingParagraph(
                        str(section.title()), STYLE.section, section, key, "section"
                    )
                )
                element_list.append(Spacer(1, 0.07 * inch))

        if variable.startswith(("sign_", "sympt_")):
            if guide == guide_to_omit:
                guide = ""

        item = question + definition + guide

        if item in items:
            # Finally, add the paragraph element for the specific variable and its guide.
            element_list.append(
                Paragraph(f"<b>{question}:</b> See Above.", STYLE.normal)
            )
            element_list.append(Spacer(1, 0.07 * inch))

        else:
            items.append(item)

            # Finally, add the paragraph element for the specific variable and its guide.
            element_list.append(
                Paragraph(f"<b>{question}:</b> {definition} {guide}", STYLE.normal)
            )
            element_list.append(Spacer(1, 0.07 * inch))

    return element_list


def _create_table_of_contents(
    toc_entries: list, total_width: float, total_height: float
) -> dict:
    """
    Generates a table of contents for the completion guide based on the generated
    toc_entries (a list of dictionaries to hold key information (key, kind, title, page_num))
    """
    styles = getSampleStyleSheet()
    toc_style = styles["Normal"]
    toc_style.fontName = REGISTERED_FONT
    toc_style.fontSize = 9
    toc_style.leading = 13
    toc_style.leftIndent = 5

    # Track the height used for the TOC to know number of pages
    height_used = 2

    header_paragraph = Paragraph("<b>Table of Contents</b>", styles["Heading1"])
    element_list = [header_paragraph, Spacer(1, 0.1 * inch)]

    header_paragraph.height = header_paragraph.wrap(total_width, 0)[1]
    height_used += header_paragraph.height + 0.1 * inch  # Add height

    height_used += 0.1 * inch

    for entry in toc_entries:
        if not entry["key"]:
            continue  # Skip entries with None/empty keys
        title = entry["title"].split(":")[0].strip()
        kind = entry["kind"]
        indent = "&nbsp;&nbsp;&nbsp;&nbsp;" if kind == "section" else ""
        entry_text = f"{indent}<font color={STYLE.hex_blue}>{title}</font>"
        if kind == "form":
            element_list.append(Spacer(1, 0.1 * inch))
            height_used += 0.1 * inch

        toc_entry = TOCEntry(
            entry_text,
            entry["page"],
            toc_style,
            total_width,
            entry["key"],
            entry["paragraph"],
        )
        element_list.append(toc_entry)
        height_used += 13  # Height of each TOC entry is 13

    page_total = int((height_used + total_height - 1) // total_height)

    return {
        "elements": element_list,
        "pages": page_total,
    }
