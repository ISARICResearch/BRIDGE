""" This Generate Form script is for generating custom forms and tables, specifically for Medication and Pathogen Testing """

from typing import List

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import Table, TableStyle, Paragraph, Spacer

import generate_pdf.styles as style
from generate_pdf.form_classes import Field, SubsectionStyle, Row, Subsubsection

grey_70 = colors.hsl2rgb(0, 0, .7)
grey_80 = colors.hsl2rgb(0, 0, .8)
grey_90 = colors.hsl2rgb(0, 0, .9)
grey_95 = colors.hsl2rgb(0, 0, .95)
grey_97 = colors.hsl2rgb(0, 0, .97)

''' Function to generate each row of the form as a table '''


# each row is a table to allow any number of columns and structure changing.
def construct_standard_row(
        row: Row,
        row_index: int,
        rows_len: int,
        subsubsection: Subsubsection,
        subsub_index: int,
        subsubs_len: int,
        subsectionStyle: SubsectionStyle
):
    width, height = letter
    line_width = .75

    colWidths = [w * width for w in row.widths]
    table = Table([row.columns], colWidths=colWidths)
    row_length = len(row.columns)

    if subsectionStyle == SubsectionStyle.HEADING:
        # Set the style to the table
        table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (0, -1), 30),
            ('LINEAFTER', (0, 0), (0, -1), line_width, colors.black),
            ('LINEBEFORE', (-1, 0), (-1, -1), line_width, colors.black),
            ('BACKGROUND', (1, 0), (-2, 0), grey_70),
            ('SPAN', (1, 0), (-2, 0)),
            ('LINEBELOW', (1, 0), (-2, -1), line_width, colors.black),
            ('LINEABOVE', (1, 0), (-2, 0), line_width, colors.black),
        ]))

        table.keepWithNext = True

        return table

    # Apply base style
    table_style = TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (0, -1), 30),
        ('LINEAFTER', (0, 0), (0, -1), line_width, colors.black),
        ('LINEBEFORE', (-1, 0), (-1, -1), line_width, colors.black),
    ])

    ''' === Row Styling ===  handles if row should be shaded or not '''
    # If row is shaded, apply the shaded style and add line under it
    if row.shade == "conditional":
        subsectionStyle = SubsectionStyle.QA_BOARDERLESS
        table_style.add('BACKGROUND', (1, 0), (-2, 0), grey_95)
        if row_index == rows_len - 1 and not subsub_index == subsubs_len - 1:
            table_style.add('LINEBELOW', (1, 0), (-2, -1), line_width, grey_80)

    # If row is shaded, apply the shaded style and add line under it
    if row.shade == "descriptive":
        subsectionStyle = SubsectionStyle.QA_BOARDERLESS
        table_style.add('BACKGROUND', (1, 0), (-2, 0), grey_80)
        table_style.add('LINEABOVE', (1, 0), (-2, -1), line_width, colors.black)
        if row_index == rows_len - 1 and not subsub_index == subsubs_len - 1:
            table_style.add('LINEBELOW', (1, 0), (-2, -1), line_width, grey_80)

    ''' === Subsubsection Styling ===  handles if row needs internal lines and adding lines above/below it '''
    # If row is a little header, add line above and below if just one line
    if bool(subsubsection.header != None):
        subsectionStyle = SubsectionStyle.QA_BOARDERLESS
        if row_index == 0 and subsub_index > 1:
            # if not rows[row_index-1].is_shaded:
            table_style.add('LINEABOVE', (1, 0), (-2, -1), line_width, grey_80)
            if row_index == rows_len - 1 and not subsub_index == subsubs_len - 1:
                table_style.add('LINEBELOW', (1, 0), (-2, -1), line_width, grey_80)

    # if row is part of a condtional group, add line above and/or below if starting or ending row
    if (subsubsection.is_conditional == True):
        subsectionStyle = SubsectionStyle.QA_BOARDERLESS
        if row_index == 0 and subsub_index > 1:
            table_style.add('LINEABOVE', (1, 0), (-2, -1), line_width, grey_80)
            table_style.add('LINEBELOW', (1, 0), (-2, -1), line_width, grey_80)

    ''' === Subsection Styling ===  handles drawing internal lines as grey or black'''
    # if style is grey, add grey lines
    if subsectionStyle == SubsectionStyle.QA_GREY:
        # Handle left & right borders
        if len(row.fields) == 3:
            for i in range(row_length - 2):
                x = i * 2
                table_style.add('LINEBEFORE', (x + 1, 0), (x + 1, -1), line_width,
                                grey_80)  # should depend on row_length
        elif len(row.fields) == 2:
            table_style.add('LINEBEFORE', (int(row_length / 2), 0), (int(row_length / 2), -1), line_width,
                            grey_80)  # should depend on row_length

        if not (row_index == rows_len - 1 and subsub_index == subsubs_len - 1):
            table_style.add('LINEBELOW', (1, 0), (-2, -1), line_width, grey_80)
        if not (row_index == 0 and subsub_index == 0):
            table_style.add('LINEABOVE', (1, 0), (-2, 0), line_width, grey_80)

    # If style is black, add black lines
    if subsectionStyle == SubsectionStyle.QA_BLACK:
        # Handle left & right borders
        if len(row.fields) == 3:
            for i in range(row_length - 2):
                x = i * 2
                table_style.add('LINEBEFORE', (x + 1, 0), (x + 1, -1), line_width,
                                colors.black)  # should depend on row_length
        elif len(row.fields) == 2:
            table_style.add('LINEBEFORE', (int(row_length / 2), 0), (int(row_length / 2), -1), line_width,
                            colors.black)  # should depend on row_length

        if not (row_index == rows_len - 1):
            table_style.add('LINEBELOW', (1, 0), (-2, -1), line_width, colors.black)
        if not (row_index == 0):
            table_style.add('LINEABOVE', (1, 0), (-2, 0), line_width, colors.black)

    ''' === Section Styling === '''

    # Add top and bottom borders to section
    if row_index == rows_len - 1 and subsub_index == subsubs_len - 1:
        table_style.add('LINEBELOW', (1, 0), (-2, -1), line_width, colors.black)
    if row_index == 0 and subsub_index == 0:
        table_style.add('LINEABOVE', (1, 0), (-2, -1), line_width, colors.black)

    # Add left and right borders to section
    table_style.add('LINEAFTER', (0, 0), (0, -1), line_width, colors.black)
    table_style.add('LINEBEFORE', (-1, 0), (-1, -1), line_width, colors.black)

    # Add padding
    table_style.add('TOPPADDING', (1, 0), (-2, -1), 5)
    table_style.add('BOTTOMPADDING', (1, 0), (-2, -1), 5)

    # Set the style to the table
    table.setStyle(table_style)

    return table


''' Function to generate the custom Medication form '''


def construct_medication_form(fields: List[Field]):
    # Define the page size
    width, height = letter
    table_width = 0.92 * width
    margin_width = ((1 - .92) / 2) * width
    line_width = .75
    answer_col_count: int = 5
    question_col_width = (table_width / 6) * .89

    # Create the heading table
    heading_widths = [margin_width, table_width, margin_width]
    heading_paragraph = fields[0].title
    heading_paragraph.style = style.section_header
    heading = Table([['', heading_paragraph, '']], colWidths=heading_widths)
    heading.keepWithNext = True
    heading.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (0, -1), 30),
        ('LINEAFTER', (0, 0), (0, -1), line_width, colors.black),
        ('LINEBEFORE', (-1, 0), (-1, -1), line_width, colors.black),
        ('BACKGROUND', (1, 0), (-2, 0), grey_70),
        ('LINEBELOW', (1, 0), (-2, -1), line_width, colors.black),
        ('LINEABOVE', (1, 0), (-2, 0), line_width, colors.black),
    ]))

    fields_to_add = ['medi_medtype', 'medi_treat', 'medi_medstartdate', 'medi_medenddate', 'medi_numdays',
                     'medi_frequency', 'medi_dose', 'medi_units', 'medi_numdoses', 'medi_offlab']
    fields_to_add_answer = ['medi_medtype', 'medi_treat', 'medi_offlab', 'medi_dose']

    route_suffix = '_route'
    route_question = "Medication route"
    route_answers = []

    # Initialize the body content
    body_content = []

    # Iterate through the fields and add rows to the body content
    for field in fields:
        if not field.is_heading and field.name in fields_to_add:
            # Create a row with the question paragraph and empty answer columns
            row = ['']  # Left margin

            # Add question
            if field.name == "medi_medtype":
                row.append(Paragraph(text='Type of agent', style=style.normal))
            else:
                row.append(field.question)  # Question column

            # Add answers
            if field.name in fields_to_add_answer:
                row.extend([field.answer] * answer_col_count)  # Empty answer columns
            elif (field.name == "medi_medstartdate") or (field.name == "medi_medenddate"):
                # Modify the text in the copied field.answer
                field.answer[0].text = field.answer[0].text.replace('_', '')

                field_answer_copy = field.answer.copy()

                # Extend the row with the modified copy (not the original field.answer)
                # '[ <font color="lightgrey">DD</font> / <font color="lightgrey">MM</font> / 20<font color="lightgrey">YY</font> ]'
                row.extend([Paragraph(
                    text='<font color="lightgrey">[ DD / MM / 20YY ]</font>'
                )] * answer_col_count)
            else:
                row.extend([''] * answer_col_count)  # Empty answer columns

            row.append('')  # Right margin
            body_content.append(row)

            # Add custom Name row after medi_treat
            if field.name == 'medi_treat':
                row = ['']  # Left margin
                row.append(Paragraph(text='Medication Name', style=style.normal))  # Question column
                # Create a list of Paragraphs for the answer (3 blank lines)
                # answer = [Paragraph(text='', style=style.normal) for _ in range(3)]
                # Create a list of Spacer elements for the answer (3 blank lines)
                answer = [Spacer(1, 10) for _ in range(3)]  # 20 points of space per line
                # Extend the row with the answer repeated for each answer column
                row.extend([answer] * answer_col_count)  # Empty answer columns

                row.append('')  # Right margin
                body_content.append(row)

            # Add custom row for route after numdays
            if field.name == 'medi_numdays':
                row = ['']  # Left margin
                row.append(Paragraph(text=route_question, style=style.normal))
                row.extend([route_answers] * answer_col_count)  # Empty answer columns
                row.append('')  # Right margin
                body_content.append(row)

        elif not field.is_heading and field.name.endswith(route_suffix):
            for answer in field.answer:
                route_answer_texts = []
                for route_answer in route_answers:
                    route_answer_texts.append(route_answer.text)
                if answer.text not in route_answer_texts:
                    if 'Sub' in answer.text:
                        route_answers.insert(1, answer)
                    elif 'IM' in answer.text:
                        route_answers.insert(4, answer)
                    else:
                        route_answers.append(answer)

    # Define the column widths
    body_widths = [margin_width]  # Left margin
    body_widths.append(question_col_width)  # Question column
    body_widths.extend([(table_width - question_col_width) / answer_col_count] * answer_col_count)  # Answer columns
    body_widths.append(margin_width)  # Right margin

    # Create the table
    body = Table(body_content, colWidths=body_widths)

    # Apply a table style to add borders
    body.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),  # Middle align text vertically
        ('LEFTPADDING', (0, 0), (0, -1), 30),  # Left padding for the first column
        ('GRID', (1, 0), (-2, -1), line_width, colors.black),  # Add black grid lines
    ]))

    # Return the table (or add it to your story if you're building a PDF)
    return [heading, body]


''' Function to generate the custom Pathogen Testing form '''


def construct_testing_form(fields: List[Field], locate_phrase):
    # Define the page size
    width, height = letter
    table_width = 0.92 * width
    margin_width = ((1 - .92) / 2) * width
    line_width = .75
    answer_col_count: int = 5
    question_col_width = (table_width / 6) * .89

    # Create the heading table
    heading_widths = [margin_width, table_width, margin_width]
    heading_paragraph = fields[0].title
    heading_paragraph.style = style.section_header
    heading = Table([['', heading_paragraph, '']], colWidths=heading_widths)
    heading.keepWithNext = True
    heading.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (0, -1), 30),
        ('LINEAFTER', (0, 0), (0, -1), line_width, colors.black),
        ('LINEBEFORE', (-1, 0), (-1, -1), line_width, colors.black),
        ('BACKGROUND', (1, 0), (-2, 0), grey_70),
        ('LINEBELOW', (1, 0), (-2, -1), line_width, colors.black),
        ('LINEABOVE', (1, 0), (-2, 0), line_width, colors.black),
    ]))

    # Initialize the body content
    body_content = []

    fields_to_add = ['test_collectiondate', 'test_biospecimentype', 'test_labtestmethod', 'test_result', 'test_ctvalue',
                     'test_genrep_db', 'test_genrep_ref', 'test_genrep_yn', 'test_pathtested']
    fields_to_add_answer = ['test_collectiondate', 'test_biospecimentype', 'test_labtestmethod', 'test_result',
                            'test_genrep_db', 'test_genrep_yn', 'test_pathtested']
    fields_to_add_other = ['test_biospecimentype', 'test_labtestmethod', 'test_genrep_db', 'test_pathtested']

    # Iterate through the fields and add rows to the body content
    for field in fields:

        if not field.is_heading and field.name in fields_to_add:
            # Create a row with the question paragraph and empty answer columns
            row = ['']  # Left margin

            # Add question           
            row.append(field.question)  # Question column

            # Add answers
            if (field.name == "test_collectiondate"):
                # Create a copy of field.answer (shallow copy)

                # Modify the text in the copied field.answer
                field.answer[0].text = field.answer[0].text.replace('_', '')

                field_answer_copy = field.answer.copy()

                # Extend the row with the modified copy (not the original field.answer)
                # '[ <font color="lightgrey">DD</font> / <font color="lightgrey">MM</font> / 20<font color="lightgrey">YY</font> ]'
                row.extend([Paragraph(
                    text='<font color="lightgrey">[ DD / MM / 20YY ]</font>'
                )] * answer_col_count)


            elif (field.name in fields_to_add_other):

                other_text = locate_phrase('other')['text']

                # Remove line
                if '_' in field.answer[-1].text:
                    field.answer.remove(
                        field.answer[-1])  # Remove the last element if it contains '_'

                for paragraph in field.answer:
                    if other_text.lower() in paragraph.text.lower():
                        field.answer.remove(paragraph)

                field.answer.append(Paragraph(text='○ ' + other_text + ' ' + ('_' * 20), style=style.normal))

                row.extend([field.answer] * answer_col_count)


            elif field.name in fields_to_add_answer:
                row.extend([field.answer] * answer_col_count)  # filled answer columns

            else:
                row.extend([''] * answer_col_count)  # Empty answer columns

            row.append('')  # Right margin
            body_content.append(row)

    # Define the column widths
    body_widths = [margin_width]  # Left margin
    body_widths.append(question_col_width)  # Question column
    body_widths.extend([(table_width - question_col_width) / answer_col_count] * answer_col_count)  # Answer columns
    body_widths.append(margin_width)  # Right margin

    # Create the table
    if (len(body_content) == 0): return []

    body = Table(body_content, colWidths=body_widths)

    # Apply a table style to add borders
    body.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),  # Middle align text vertically
        ('LEFTPADDING', (0, 0), (0, -1), 30),  # Left padding for the first column
        ('GRID', (1, 0), (-2, -1), line_width, colors.black),  # Add black grid lines
    ]))

    # Return the table (or add it to your story if you're building a PDF)
    return [heading, body]
