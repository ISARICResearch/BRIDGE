"""This Generate Form script is for generating custom forms and tables, specifically for Medication and Pathogen Testing"""

from typing import List, Callable

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import Table, TableStyle, Paragraph, Spacer

import bridge.generate_pdf.styles as style
from bridge.generate_pdf.form_classes import Field, SubsectionStyle, Row, Subsubsection

GREY_70 = colors.hsl2rgb(0, 0, 0.7)
GREY_80 = colors.hsl2rgb(0, 0, 0.8)
GREY_90 = colors.hsl2rgb(0, 0, 0.9)
GREY_95 = colors.hsl2rgb(0, 0, 0.95)
GREY_97 = colors.hsl2rgb(0, 0, 0.97)

# Define the page size
WIDTH, HEIGHT = letter
TABLE_WIDTH = 0.92 * WIDTH
MARGIN_WIDTH = ((1 - 0.92) / 2) * WIDTH
LINE_WIDTH = 0.75
ANSWER_COL_COUNT: int = 5
QUESTION_COL_WIDTH = (TABLE_WIDTH / 6) * 0.89


def construct_standard_row(
    row: Row,
    row_index: int,
    rows_len: int,
    subsubsection: Subsubsection,
    subsub_index: int,
    subsubs_len: int,
    subsection_style: SubsectionStyle,
) -> Table:
    """
    Function to generate each row of the form as a table.
    Each row is a table to allow any number of columns and structure changing.
    """
    width, height = letter
    line_width = 0.75

    col_widths = [w * width for w in row.widths]
    table = Table([row.columns], colWidths=col_widths)
    row_length = len(row.columns)

    if subsection_style == SubsectionStyle.HEADING:
        # Set the style to the table
        table.setStyle(
            TableStyle(
                [
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("LEFTPADDING", (0, 0), (0, -1), 30),
                    ("LINEAFTER", (0, 0), (0, -1), line_width, colors.black),
                    ("LINEBEFORE", (-1, 0), (-1, -1), line_width, colors.black),
                    ("BACKGROUND", (1, 0), (-2, 0), GREY_70),
                    ("SPAN", (1, 0), (-2, 0)),
                    ("LINEBELOW", (1, 0), (-2, -1), line_width, colors.black),
                    ("LINEABOVE", (1, 0), (-2, 0), line_width, colors.black),
                ]
            )
        )

        table.keepWithNext = True

        return table

    # Apply base style
    table_style = TableStyle(
        [
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING", (0, 0), (0, -1), 30),
            ("LINEAFTER", (0, 0), (0, -1), line_width, colors.black),
            ("LINEBEFORE", (-1, 0), (-1, -1), line_width, colors.black),
        ]
    )

    """ === Row Styling ===  handles if row should be shaded or not """
    # If row is shaded, apply the shaded style and add line under it
    if row.shade == "conditional":
        subsection_style = SubsectionStyle.QA_BORDERLESS
        table_style.add("BACKGROUND", (1, 0), (-2, 0), GREY_95)
        if row_index == rows_len - 1 and not subsub_index == subsubs_len - 1:
            table_style.add("LINEBELOW", (1, 0), (-2, -1), line_width, GREY_80)

    # If row is shaded, apply the shaded style and add line under it
    if row.shade == "descriptive":
        subsection_style = SubsectionStyle.QA_BORDERLESS
        table_style.add("BACKGROUND", (1, 0), (-2, 0), GREY_80)
        table_style.add("LINEABOVE", (1, 0), (-2, -1), line_width, colors.black)
        if row_index == rows_len - 1 and not subsub_index == subsubs_len - 1:
            table_style.add("LINEBELOW", (1, 0), (-2, -1), line_width, GREY_80)

    """ === Subsubsection Styling ===  handles if row needs internal lines and adding lines above/below it """
    # If row is a little header, add line above and below if just one line
    if subsubsection.header:
        subsection_style = SubsectionStyle.QA_BORDERLESS
        if row_index == 0 and subsub_index > 1:
            # if not rows[row_index-1].is_shaded:
            table_style.add("LINEABOVE", (1, 0), (-2, -1), line_width, GREY_80)
            if row_index == rows_len - 1 and not subsub_index == subsubs_len - 1:
                table_style.add("LINEBELOW", (1, 0), (-2, -1), line_width, GREY_80)

    # if row is part of a conditional group, add line above and/or below if starting or ending row
    if subsubsection.is_conditional:
        subsection_style = SubsectionStyle.QA_BORDERLESS
        if row_index == 0 and subsub_index > 1:
            table_style.add("LINEABOVE", (1, 0), (-2, -1), line_width, GREY_80)
            table_style.add("LINEBELOW", (1, 0), (-2, -1), line_width, GREY_80)

    """ === Subsection Styling ===  handles drawing internal lines as grey or black"""
    # if style is grey, add grey lines
    if subsection_style == SubsectionStyle.QA_GREY:
        # Handle left & right borders
        if len(row.fields) == 3:
            for i in range(row_length - 2):
                x = i * 2
                table_style.add(
                    "LINEBEFORE", (x + 1, 0), (x + 1, -1), line_width, GREY_80
                )  # should depend on row_length
        elif len(row.fields) == 2:
            table_style.add(
                "LINEBEFORE",
                (int(row_length / 2), 0),
                (int(row_length / 2), -1),
                line_width,
                GREY_80,
            )  # should depend on row_length

        if not (row_index == rows_len - 1 and subsub_index == subsubs_len - 1):
            table_style.add("LINEBELOW", (1, 0), (-2, -1), line_width, GREY_80)
        if not (row_index == 0 and subsub_index == 0):
            table_style.add("LINEABOVE", (1, 0), (-2, 0), line_width, GREY_80)

    # If style is black, add black lines
    if subsection_style == SubsectionStyle.QA_BLACK:
        # Handle left & right borders
        if len(row.fields) == 3:
            for i in range(row_length - 2):
                x = i * 2
                table_style.add(
                    "LINEBEFORE", (x + 1, 0), (x + 1, -1), line_width, colors.black
                )  # should depend on row_length
        elif len(row.fields) == 2:
            table_style.add(
                "LINEBEFORE",
                (int(row_length / 2), 0),
                (int(row_length / 2), -1),
                line_width,
                colors.black,
            )  # should depend on row_length

        if not (row_index == rows_len - 1):
            table_style.add("LINEBELOW", (1, 0), (-2, -1), line_width, colors.black)
        if not (row_index == 0):
            table_style.add("LINEABOVE", (1, 0), (-2, 0), line_width, colors.black)

    """ === Section Styling === """
    # Add top and bottom borders to section
    if row_index == rows_len - 1 and subsub_index == subsubs_len - 1:
        table_style.add("LINEBELOW", (1, 0), (-2, -1), line_width, colors.black)
    if row_index == 0 and subsub_index == 0:
        table_style.add("LINEABOVE", (1, 0), (-2, -1), line_width, colors.black)

    # Add left and right borders to section
    table_style.add("LINEAFTER", (0, 0), (0, -1), line_width, colors.black)
    table_style.add("LINEBEFORE", (-1, 0), (-1, -1), line_width, colors.black)

    # Add padding
    table_style.add("TOPPADDING", (1, 0), (-2, -1), 5)
    table_style.add("BOTTOMPADDING", (1, 0), (-2, -1), 5)

    # Set the style to the table
    table.setStyle(table_style)
    return table


def create_heading_table(
    fields: list, table_width: float, margin_width: float, line_width: float
) -> Table:
    heading_widths = [margin_width, table_width, margin_width]
    heading_paragraph = fields[0].title
    heading_paragraph.style = style.section_header
    heading = Table([["", heading_paragraph, ""]], colWidths=heading_widths)
    heading.keepWithNext = True
    heading.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (0, -1), 30),
                ("LINEAFTER", (0, 0), (0, -1), line_width, colors.black),
                ("LINEBEFORE", (-1, 0), (-1, -1), line_width, colors.black),
                ("BACKGROUND", (1, 0), (-2, 0), GREY_70),
                ("LINEBELOW", (1, 0), (-2, -1), line_width, colors.black),
                ("LINEABOVE", (1, 0), (-2, 0), line_width, colors.black),
            ]
        )
    )
    return heading


def create_table(body_content) -> Table:
    # Define the column widths
    body_widths = [MARGIN_WIDTH, QUESTION_COL_WIDTH]  # Left margin
    body_widths.extend(
        [(TABLE_WIDTH - QUESTION_COL_WIDTH) / ANSWER_COL_COUNT] * ANSWER_COL_COUNT
    )  # Answer columns
    body_widths.append(MARGIN_WIDTH)  # Right margin

    body = Table(body_content, colWidths=body_widths)

    # Apply a table style to add borders
    body.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),  # Middle align text vertically
                (
                    "LEFTPADDING",
                    (0, 0),
                    (0, -1),
                    30,
                ),  # Left padding for the first column
                (
                    "GRID",
                    (1, 0),
                    (-2, -1),
                    LINE_WIDTH,
                    colors.black,
                ),  # Add black grid lines
            ]
        )
    )
    return body


def construct_medication_form(fields: List[Field]) -> List[Table]:
    """Function to generate the custom Medication form"""
    heading = create_heading_table(fields, TABLE_WIDTH, MARGIN_WIDTH, LINE_WIDTH)

    fields_to_add = [
        "medi_medtype",
        "medi_treat",
        "medi_medstartdate",
        "medi_medenddate",
        "medi_numdays",
        "medi_frequency",
        "medi_dose",
        "medi_units",
        "medi_numdoses",
        "medi_offlab",
    ]
    fields_to_add_answer = [
        "medi_medtype",
        "medi_treat",
        "medi_offlab",
        "medi_dose",
    ]

    route_suffix = "_route"
    route_question = "Medication route"
    route_answers = []

    # Initialize the body content
    body_content = []

    # Iterate through the fields and add rows to the body content
    for field in fields:
        if not field.is_heading and field.name in fields_to_add:
            # Create a row with the question paragraph and empty answer columns
            row = [""]  # Left margin

            # Add question
            if field.name == "medi_medtype":
                row.append(Paragraph(text="Type of agent", style=style.normal))
            else:
                row.append(field.question)  # Question column

            # Add answers
            if field.name in fields_to_add_answer:
                row.extend([field.answer] * ANSWER_COL_COUNT)  # Empty answer columns
            elif (field.name == "medi_medstartdate") or (
                field.name == "medi_medenddate"
            ):
                # Modify the text in the copied field.answer
                field.answer[0].text = field.answer[0].text.replace("_", "")

                # Extend the row with the modified copy (not the original field.answer)
                row.extend(
                    [
                        Paragraph(
                            text='<font color="lightgrey">[ DD / MM / 20YY ]</font>'
                        )
                    ]
                    * ANSWER_COL_COUNT
                )
            else:
                row.extend([""] * ANSWER_COL_COUNT)  # Empty answer columns

            row.append("")  # Right margin
            body_content.append(row)

            # Add custom Name row after medi_treat
            if field.name == "medi_treat":
                row = [
                    "",
                    Paragraph(text="Medication Name", style=style.normal),
                ]  # Left margin
                # Create a list of Spacer elements for the answer (3 blank lines)
                answer = [
                    Spacer(1, 10) for _ in range(3)
                ]  # 20 points of space per line
                # Extend the row with the answer repeated for each answer column
                row.extend([answer] * ANSWER_COL_COUNT)  # Empty answer columns

                row.append("")  # Right margin
                body_content.append(row)

            # Add custom row for route after numdays
            if field.name == "medi_numdays":
                row = [
                    "",
                    Paragraph(text=route_question, style=style.normal),
                ]  # Left margin
                row.extend([route_answers] * ANSWER_COL_COUNT)  # Empty answer columns
                row.append("")  # Right margin
                body_content.append(row)

        elif not field.is_heading and field.name.endswith(route_suffix):
            for answer in field.answer:
                route_answer_texts = []
                for route_answer in route_answers:
                    route_answer_texts.append(route_answer.text)
                if answer.text not in route_answer_texts:
                    if "Sub" in answer.text:
                        route_answers.insert(1, answer)
                    elif "IM" in answer.text:
                        route_answers.insert(4, answer)
                    else:
                        route_answers.append(answer)

    body = create_table(body_content)

    # Return the table (or add it to your story if you're building a PDF)
    return [heading, body]


def construct_testing_form(fields: List[Field], locate_phrase: Callable) -> List[Table]:
    """Function to generate the custom Pathogen Testing form"""
    heading = create_heading_table(fields, TABLE_WIDTH, MARGIN_WIDTH, LINE_WIDTH)

    # Initialize the body content
    body_content = []

    fields_to_add = [
        "test_collectiondate",
        "test_biospecimentype",
        "test_labtestmethod",
        "test_marker",
        "test_result",
        "test_ctvalue",
        "test_vload",
        "test_genrep_db",
        "test_genrep_ref",
        "test_genrep_yn",
        "test_pathtested",
    ]
    fields_to_add_answer = [
        "test_collectiondate",
        "test_biospecimentype",
        "test_labtestmethod",
        "test_marker",
        "test_result",
        "test_genrep_db",
        "test_genrep_yn",
        "test_pathtested",
    ]
    fields_to_add_other = [
        "test_biospecimentype",
        "test_genrep_db",
        "test_pathtested",
    ]

    # Iterate through the fields and add rows to the body content
    for field in fields:
        if not field.is_heading and field.name in fields_to_add:
            # Create a row with the question paragraph and empty answer columns
            row = ["", field.question]  # Left margin & Question column

            # Add answers
            if field.name == "test_collectiondate":
                # Modify the text in the copied field.answer
                field.answer[0].text = field.answer[0].text.replace("_", "")

                # Extend the row with the modified copy (not the original field.answer)
                row.extend(
                    [
                        Paragraph(
                            text='<font color="lightgrey">[ DD / MM / 20YY ]</font>'
                        )
                    ]
                    * ANSWER_COL_COUNT
                )

            elif field.name in fields_to_add_other:
                other_text = locate_phrase("other")["text"]

                # Remove line
                if "_" in field.answer[-1].text:
                    field.answer.remove(
                        field.answer[-1]
                    )  # Remove the last element if it contains '_'

                for paragraph in field.answer:
                    if other_text.lower() in paragraph.text.lower():
                        field.answer.remove(paragraph)

                field.answer.append(
                    Paragraph(
                        text="○ " + other_text + " " + ("_" * 20), style=style.normal
                    )
                )

                row.extend([field.answer] * ANSWER_COL_COUNT)

            elif field.name in fields_to_add_answer:
                row.extend([field.answer] * ANSWER_COL_COUNT)  # filled answer columns

            else:
                row.extend([""] * ANSWER_COL_COUNT)  # Empty answer columns

            row.append("")  # Right margin
            body_content.append(row)

    # Create the table
    if len(body_content) == 0:
        return []

    body = create_table(body_content)

    # Return the table (or add it to your story if you're building a PDF)
    return [heading, body]
