""" External package imports """
import re
from typing import List

import pandas as pd
from reportlab.platypus import Paragraph, PageBreak, Spacer

import src.generate_pdf.form_classes as cl
import src.generate_pdf.styles as style
from src.generate_pdf.form_construct import construct_medication_form, construct_standard_row, construct_testing_form

LINE_PLACEHOLDER = '_' * 40

# So at the moment, one table is made and added to our elements array, before returning the elements array.

# I am interested in chunking this into new tables for each

'''

How generate_form() Works Now:

 To make the form, the data is split into forms which are split into sections.

 - Each variable from the original data is now put into a Field, which acts as a Heading or a Question/Answer pair in the table.
    Fields both store the Paragraphs that display to look all nice, as well as the original data from the data_dic csv.
 - Sections are now a class. Each is made from a list of fields and has a method to divide it into subsections.
 - Subsections are a class.  Each is made from a list of fields and a style choice.  They have a method to divide their fields into rows.
 - Rows are a class.  Each is made from a list of fields and has methods to create the styled columns and widths to be output by ReportLab.  



So it goes like this: Form > Section > Subsection > Subsubsection > Row > Field > Dependency

    1) Break data dictionary into Forms. Each form goes on its own page.
    2) Break form from into Section classes. Each section gets some spacing between it.
    3) Break sections into Subsection classes. Each subsection is styled as normal, light bordered, or a heading.
    4) Break subsections into Row classes.  Each row has a columns and widths property, which are used to create to the document.
    5) Add each row to elements as its own table using its custom styling choices.

'''


def format_choices(choices_str, field_type, threshold=65, is_units=False):
    """
    Format the choices string. If the combined length exceeds the threshold, use line breaks instead of commas.
    Prepend symbols based on the field type.
    """
    if type(choices_str) != str:
        return None

    if field_type == 'radio':
        symbol = "○ "
    elif field_type == 'list':
        symbol = "○ "
    elif field_type == 'user_list':
        symbol = "○ "
    elif field_type == 'checkbox':
        symbol = "□ "
    elif field_type == 'dropdown':
        symbol = "↧ "
    else:
        symbol = ""

    if is_units:
        symbol = symbol.strip(" ")

    choices = ''
    if len(choices_str.split('|')) <= 15:
        choices = [symbol + choice.split(',', 1)[-1].strip().replace("Â", "") for choice in choices_str.split('|')]
        for choice in choices:
            if len(choice) > 1 and choice[1] == 'Â':
                choice.pop()
        combined_choices = '   '.join(choices).strip()

    else:
        combined_choices = LINE_PLACEHOLDER
    if len(combined_choices) > threshold:
        combined_choices = "\n".join(choices).strip()
    return combined_choices


# Generates the array of elements for a pdf of several forms from the data_dictionary
def generate_form(data_dictionary, elements, locate_phrase):
    # Function returns array of sections. each section is an array of Fields
    def get_sections(group):

        # Return section after appending new field to it, or modifying old one
        def add_field_to_section(row, section: list[cl.Field]):

            def create_field(row):

                def parse_branching_logic(logic_str: str) -> List[cl.Dependency]:
                    dependencies = []
                    # Split on boolean operators while keeping the operators
                    tokens = re.split(r'\s+(and|or)\s+', logic_str, flags=re.IGNORECASE)

                    for token in tokens:
                        if token.lower() in ['and', 'or']:
                            continue
                        # Match patterns like [field]='1' or [field] < 5
                        match = re.match(r'\[(\w+)\] ?([!=<>]+) ?[\'"]?(\w+)[\'"]?', token)

                        if match:
                            field, operator, value = match.groups()
                            dependencies.append(cl.Dependency(field, operator, value))
                    return dependencies

                # Get field's name:
                variable_name = row[0]

                # Get field's dependencies:
                branching_logic = row['Branching Logic (Show field only if...)']
                dependencies = []

                if type(branching_logic) == str:
                    dependencies = parse_branching_logic(branching_logic)

                # Create a new field with question and placeholder answer
                new_field = cl.Field(
                    name=variable_name,
                    dependencies=dependencies,
                    data=[row],
                    question=Paragraph(row['Field Label'], style.normal),
                    answer=[]
                )

                # If country, make it a short line
                if variable_name == 'demog_country':
                    new_field.answer = [Paragraph("_" * 18, style.normal)]
                    return new_field

                # if a multi select
                if row['Field Type'] in ['radio', 'dropdown', 'checkbox', 'list', 'user_list', 'multi_list']:

                    # Create multiple-choice answers
                    symbol = {
                        'radio': '○ ',
                        'checkbox': '□ ',
                        'dropdown': '○ ',  # '↧ ',
                        'list': '○ ',
                        'user_list': '○ ',
                        'multi_list': '□ ',
                    }.get(row['Field Type'], '')

                    if type(row['Choices, Calculations, OR Slider Labels']) != str:
                        return None

                    choices = []
                    if new_field.name == 'test_biospecimentype':
                        '''This is a wierd line of code to check when editing variables related to the PATHOGEN TESTING form.  
                        Specifically 'test_biospecimentype' 
                        This just only pulls the answers presented to me to add to the form'''
                        for choice in row['Choices, Calculations, OR Slider Labels'].split('|'):
                            # if choice.split(',', 1)[0].strip() in ['1','2','3','4','5','6', '10']:
                            choices.append(symbol + choice.split(',', 1)[-1].strip())
                    else:
                        choices = [symbol + choice.split(',', 1)[-1].strip() for choice in
                                   row['Choices, Calculations, OR Slider Labels'].split('|')]

                    if len(choices) < 23:
                        new_field.answer = [Paragraph(choice, style.normal) for choice in choices]
                    else:
                        # return None
                        new_field.answer = [Paragraph(LINE_PLACEHOLDER, style.normal)]
                    return new_field

                # else if a text fill
                elif row['Field Type'] == 'text':
                    # Get type of text (date, number, etc.)
                    validation = row['Text Validation Type OR Show Slider Number']

                    # if date
                    if validation == 'date_dmy':
                        # Add a date placeholder
                        date_str = """[<font color="lightgrey">_D_</font>][<font color="lightgrey">_D_</font>]/[<font color="lightgrey">_M_</font>][<font color="lightgrey">_M_</font>]/[_2_][_0_][<font color="lightgrey">_Y_</font>][<font color="lightgrey">_Y_</font>]"""
                        new_field.answer = [Paragraph(date_str, style.normal)]
                    # if time
                    elif validation == 'time':
                        # Add a time placeholder
                        time_str = "_" * 18
                        new_field.answer = [Paragraph(time_str, style.normal)]
                    # if number
                    elif validation == 'number':
                        number_str = "_" * 18
                        new_field.answer = [Paragraph(number_str, style.normal)]
                    else:
                        # Open-ended questions
                        new_field.answer = [Paragraph(LINE_PLACEHOLDER, style.normal)]
                    return new_field

                return None

            variable_name = row['Variable / Field Name']

            # work from here, if descriptive, go do a thing, else...
            if row['Field Type'] == 'descriptive':
                new_field = cl.Field(
                    name=variable_name,
                    dependencies=[],
                    data=[row],
                    question=Paragraph(row['Field Label']),
                    answer=[Paragraph('')],
                    is_descriptive=True
                )
                if type(new_field) == cl.Field: section.append(new_field)
                return section

            ### ! Handle special cases (add to last question) ###

            if "demog_country_other" in variable_name:
                return section

                # if other, oth, otherl3: add "Specify Other" to last field's answer
            if variable_name.endswith(
                    ("lesion_torsoo", "lesion_armso", "lesion_legso", "lesion_palmo", "lesion_soleo", 'lesion_genito',
                     'lesion_perio', 'lesion_ocularo', 'lesion_heado')):
                section[-1].answer.append(Paragraph("_" * 18, style.normal))
                section[-1].data.append(row)

                # if other, oth, otherl3: add "Specify Other" to last field's answer
            elif variable_name.endswith(("_oth", "_otherl3")):
                section[-1].answer.append(Paragraph("_" * 18, style.normal))
                section[-1].data.append(row)

            # if otherl2: ignore (Because these are long lists)
            elif variable_name.endswith("_otherl2"):
                return section

            # if units, add units to last field's answer
            elif variable_name.endswith("_units"):
                # Add "Units" to the last field's answer
                formatted_choices = format_choices(row['Choices, Calculations, OR Slider Labels'], row['Field Type'],
                                                   200, True)

                if type(formatted_choices) == str:
                    section[-1].answer.append(Paragraph(formatted_choices, style.normal))
                else:
                    section[-1].answer.append(Paragraph(f"Units:" + "_" * (18 - len("Units:")), style.normal))

                section[-1].data.append(row)

            ### ! If not a special case, add new field to section ###
            else:
                new_field = create_field(row)
                if type(new_field) == cl.Field: section.append(new_field)

            return section

        # form sections are a list of lists of fields, where then each section is a list of fields
        section_fields: list[list[cl.Field]] = []
        current_section_name = None

        for i, row in group.iterrows():
            if '>' in row['Field Label'][0:2]:
                continue
            if ('_unlisted_' in row['Variable / Field Name']) and not (
                    '_unlisted_0item' in row['Variable / Field Name'] or '_unlisted_type' in row[
                'Variable / Field Name']):
                continue
            if row['Variable / Field Name'].endswith('addi'):
                continue
            # If row part of new section, add Section Header field
            if row['Section Header'] != current_section_name and pd.notna(row['Section Header']):
                section_fields.append([])
                current_section_name = row['Section Header']
                current_section_index = len(section_fields) - 1
                section_fields[current_section_index].append(
                    cl.Field(
                        name=row[0],
                        data=[row],
                        is_heading=True,
                        title=Paragraph(current_section_name, style.section_header)
                    )
                )

            # If form_sections isn't yet started, add
            if len(section_fields) == 0:
                section_fields.append([])

            current_section_index = len(section_fields) - 1

            field_to_add = row
            if '_unlisted_0item' in row['Variable / Field Name'] or '_unlisted_type' in row['Variable / Field Name']:
                field_to_add['Field Label'] = ""

            section_fields[current_section_index] = add_field_to_section(field_to_add,
                                                                         section_fields[current_section_index])

        sections: List[cl.Section] = []
        for fields_list in section_fields:
            section_type = cl.SectionType.STANDARD
            if fields_list[0].name.startswith('medi_'):
                section_type = cl.SectionType.MEDICATION
            elif fields_list[0].name.startswith('test_'):
                section_type = cl.SectionType.TESTING
            sections.append(cl.Section(fields=fields_list, type=section_type))

        return sections

    # Iterate through each form (ie: Presentation, Medication, etc.)
    for form_name in data_dictionary['Form Name'].drop_duplicates():

        group = data_dictionary[data_dictionary['Form Name'] == form_name]

        # Replace "_" in form names with spaces and make it uppercase
        fixed_name = form_name.replace("_", " ").upper()

        # Add form name as a title for each table
        elements.append(PageBreak())
        elements.append(Paragraph(fixed_name, style.form_header))

        # Form Sections are a way of splitting up the data into lists of Fields
        # where each field represents a heading or Question Answer pair.

        sections = get_sections(group)

        # For each section, divide into subsections
        for section in sections:

            if section.type == cl.SectionType.MEDICATION:
                medication_form = construct_medication_form(section.fields)
                for table in medication_form:
                    elements.append(table)

            elif section.type == cl.SectionType.TESTING:
                medication_form = construct_testing_form(section.fields, locate_phrase)
                for table in medication_form:
                    elements.append(table)

            else:
                subsections = section.divide_into_subsections()

                # For each subsection, divide into rows
                for subsection in subsections:

                    subsubsections = subsection.divide_into_subsubsections(
                        bool(subsection.style != cl.SubsectionStyle.QA_BLACK), locate_phrase)

                    for subsub_index, subsubsection in enumerate(subsubsections):

                        rows = subsubsection.divide_into_rows()

                        if rows is None: continue

                        # For each row, setup to get columns and widths
                        # Then, style it and add it to elements
                        for row_index, row in enumerate(rows):

                            if row is None: continue

                            row.setup_row()

                            # Here on is the final step, styling it and adding the row as a table to the page

                            # Scale column widths to fit page width

                            row_table = construct_standard_row(
                                row,
                                row_index,
                                len(rows),
                                subsubsection,
                                subsub_index,
                                len(subsubsections),
                                subsection.style
                            )

                            elements.append(row_table)

            # Add space between form sections
            elements.append(Spacer(1, 12))

    return elements
