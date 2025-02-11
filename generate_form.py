import generate_form_classes as cl
import generate_form_styles as style
import re
import pandas as pd
from typing import List
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import Table, TableStyle, Paragraph, PageBreak, Spacer


line_placeholder='_' * 40

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

 

So it goes like this:

    1) Break data dictionary into Forms. Each form goes on its own page.
    2) Break each from into Section classes. Each section gets some spacing between it.
    3) Break sections into Subsection classes. Each subsection is styled as normal, borderless, or a heading.
    4) Break subsections into Row classes.  Each row has a columns and widths property, which are used to create to the document.
    5) Add each row to elements as its own table using its custom styling choices.

'''

# Return array of sections where each section of a form is an array of Fields
def get_sections(group):
    # form sections are a list of lists of fields, where then each section is a list of fields
    section_fields: list[list[cl.Field]]  = []
    current_section_name = None

    for _, row in group.iterrows():
        if '>' in row['Field Label'][0:2]:
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
                    name=current_section_name,
                    data=[row],
                    is_heading=True,
                    title=Paragraph(current_section_name, style.section_header)
                )
            )
        # If form_sections isn't yet started, add 
        if len(section_fields) == 0:
            section_fields.append([])

        current_section_index = len(section_fields) - 1
        section_fields[current_section_index] = add_field_to_section(row, section_fields[current_section_index])

    sections: List[cl.Section] = []
    for fields_list in section_fields:
        sections.append(cl.Section(fields=fields_list))

    return sections

# Return section after appending new field to it, or modifying old one
def add_field_to_section(row, section: list[cl.Field]):

    variable_name = row['Variable / Field Name']

    ### ! Handle special cases (add to last question) ###

    if "demog_country_other" in variable_name:
        return section   

    # if other, oth, otherl3: add "Specify Other" to last field's answer
    if variable_name.endswith(("lesion_torsoo", "lesion_armso", "lesion_legso", "lesion_palmo", "lesion_soleo", 'lesion_genito', 'lesion_perio', 'lesion_ocularo', 'lesion_heado')):
        #section[-1].answer.text = section[-1].answer.text + '</br>' + 'Specify Other: ' + line_placeholder
        section[-1].answer.append(Paragraph('<i>Specify Other: </i> ' + "_" * 18, style.normal))
        section[-1].data.append(row) 

    # if other, oth, otherl3: add "Specify Other" to last field's answer
    elif variable_name.endswith(("_oth", "_other", "_otherl3")):
        #section[-1].answer.text = section[-1].answer.text + '</br>' + 'Specify Other: ' + line_placeholder
        section[-1].answer.append(Paragraph('<i>Specify Other: </i> ' + "_" * 18, style.normal))
        section[-1].data.append(row)
        
    # if otherl2: ignore
    elif variable_name.endswith("_otherl2"):
        return section
    
    # if units, add units to last field's answer
    elif variable_name.endswith("_units"):
        # Add "Units" to the last field's answer
        formatted_choices = format_choices(row['Choices, Calculations, OR Slider Labels'], row['Field Type'], 200, True)
        
        if type(formatted_choices) == str:
            section[-1].answer.append(Paragraph(formatted_choices, style.normal))   
        else:
            section[-1].answer.append(Paragraph(f"Units:" + "_" * (18-len("Units:")), style.normal))              
        
        section[-1].data.append(row)

    ### ! If not a special case, add new field to section ###
    else:
        new_field = create_field(row, section)

        if type (new_field) == cl.Field: section.append(new_field)

    return section

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

def create_field(row, section):
    # Get field's name:
    variable_name = row[0]

    # Get field's dependencies:
    branching_logic = row['Branching Logic (Show field only if...)']
    dependencies = []
    if type(branching_logic) == str:
        dependencies = parse_branching_logic(branching_logic)

    # Create a new field with question and placeholder answer
    new_field = cl.Field (
        name = variable_name,
        dependencies = dependencies,
        data=[row],
        question = Paragraph(row['Field Label'], style.normal),
        answer=[]
    )

    # If country, make it a short line
    if variable_name == 'demog_country':
        new_field.answer = [Paragraph("_"*18, style.normal)]
        return new_field

    # if a multi select
    if row['Field Type'] in ['radio', 'dropdown', 'checkbox', 'list', 'user_list', 'multi_list']:
        # Create multiple-choice answers
        symbol = {
            'radio': '○ ',
            'checkbox': '□ ',
            'dropdown': '○ ',#'↧ ',
            'list': '○ ',
            'user_list': '○ ',
            'multi_list': '□ ',
        }.get(row['Field Type'], '')

        if type(row['Choices, Calculations, OR Slider Labels']) != str:
            return None

        choices = [symbol + choice.split(',', 1)[-1].strip() for choice in row['Choices, Calculations, OR Slider Labels'].split('|')]

        if len(choices) < 15:
            new_field.answer = [Paragraph(choice, style.normal) for choice in choices]
        else:
            return None
            new_field.answer = [Paragraph(line_placeholder, normal)]
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
            time_str = "_"*18
            new_field.answer = [Paragraph(time_str, style.normal)]
        # if number
        elif validation == 'number':
            number_str = "_"*18
            new_field.answer = [Paragraph(number_str, style.normal)]
        else:
            # Open-ended questions
            new_field.answer = [Paragraph(line_placeholder, style.normal)]
        return new_field

    return None

def format_choices(choices_str, field_type, threshold=65, is_units=False):

    """
    Format the choices string. If the combined length exceeds the threshold, use line breaks instead of commas.
    Prepend symbols based on the field type.
    """
    if (type(choices_str) != str): return

    if field_type == 'radio':
        symbol = "○ "
    elif field_type=='list':
        symbol="○ "
    elif field_type=='user_list':
        symbol="○ "            
    elif field_type == 'checkbox' :
        symbol = "□ "
    elif field_type=='dropdown':
        symbol="↧ "
    else: 
        symbol = ""

    if is_units:
        symbol = symbol.strip(" ")

    if len(choices_str.split('|'))<=15:
        choices = [symbol + choice.split(',', 1)[-1].strip().replace("Â","") for choice in choices_str.split('|')]
        for choice in choices:
            if choice[1] == 'Â':    
                print(choice)
                choice.pop()
        combined_choices = '   '.join(choices).strip()
        

    else:
        line_placeholder='_' * 40
        combined_choices = line_placeholder
    if len(combined_choices) > threshold:
        combined_choices = "\n".join(choices).strip()
    return combined_choices

# Generates the array of elements for a pdf of several forms from the data_dictionary
def generate_form(doc, data_dictionary, elements):
    # Iterate through each form (ie: Presentation, Medication, etc.)
    for form_name in data_dictionary['Form Name'].drop_duplicates():

        group = data_dictionary[data_dictionary['Form Name'] == form_name]

        # Add form name as a title for each table
        elements.append(PageBreak())
        elements.append(Paragraph(form_name.upper(), style.form_header))
      
        # Form Sections are a way of splitting up the data into lists of Fields
            # where each field represents a heading or Question Answer pair.

        sections = get_sections(group)

        # For each section, divide into subsections
        for section in sections:   

            subsections = section.divide_into_subsections()

            # For each subsection, divide into rows
            for subsection in subsections:

                subsubsections = subsection.divide_into_subsubsections(bool(subsection.style == cl.SubsectionStyle.QA_BOARDERLESS)) 

                for subsub_index, subsubsection in enumerate(subsubsections):

                    rows = subsubsection.divide_into_rows()

                    if rows is None: continue
                        

                    # For each row, setup to get columns and widths
                        # Then, style it and add it to elements
                    for row_index,row in enumerate(rows):

                        if row is None: continue

                        row.setup_row()

                        # Here on is the final step, styling it and adding the row as a table to the page

                        # Scale column widths to fit page width
                        width, height = letter
                        line_width = .75

                        colWidths = [w * width for w in row.widths]
                        table = Table([row.columns], colWidths = colWidths)
                        row_length = len(row.columns)

                        grey_0 = colors.hsl2rgb(0, 0, .7)
                        grey_1 = colors.hsl2rgb(0, 0, .9)
                        grey_2 = colors.hsl2rgb(0, 0, .95)
                        grey_3 = colors.hsl2rgb(0, 0, .97)
                        

                        # Apply base style
                        table_style = TableStyle([
                            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                            ('LEFTPADDING', (0, 0), (0, -1), 30),
                            ('LINEAFTER', (0, 0), (0, -1), line_width, colors.black),
                            ('LINEBEFORE', (-1, 0), (-1, -1), line_width, colors.black),
                        ])

                        if len(row.fields) == 3:
                            for i in range(row_length-2):
                                x=i*2
                                #style.add('LEFTPADDING', (x+1, 0), (x+1, -1), 20),
                                #style.add('RIGHTPADDING', (x+2, 0), (x+2, -1), 0),
                                #style.add('LINEBEFORE', (x+1, 0), (x+1, -1), line_width, colors.black), # should depend on row_length
                    
                        # 
                        if row.is_shaded:
                            table_style.add('BACKGROUND', (1, 0), (-2, 0), grey_2)
                            if row_index == len(rows) - 1 and not subsub_index == len(subsubsections) - 1:
                                table_style.add('LINEBELOW', (1, 0), (-2, -1), line_width * .5, grey_1)
                            #if row_index == 1:
                                #table_style.add('LINEABOVE', (1, 0), (-2, -1), line_width, grey_3)

                        # 
                        if bool(subsubsection.header != None):
                            print('Header!', subsubsection.header)
                            if row_index == 0 and subsub_index > 1:
                                #if not rows[row_index-1].is_shaded:
                                table_style.add('LINEABOVE', (1, 0), (-2, -1), line_width, grey_1)
                                if row_index == len(rows) - 1 and not subsub_index == len(subsubsections) - 1:
                                    table_style.add('LINEBELOW', (1, 0), (-2, -1), line_width * .5, grey_1)

                        
                            
                        # Apply specific styles based on subsection type
                        if subsection.style == cl.SubsectionStyle.QA_DEFAULT:
                            table_style.add('TOPPADDING', (1, 0), (-2, -1), 5)
                            table_style.add('BOTTOMPADDING', (1, 0), (-2, -1), 5)

                            # Handle left & right borders
                            if len(row.fields) == 3:
                                for i in range(row_length-2):
                                    x=i*2
                                    table_style.add('LINEBEFORE', (x+1, 0), (x+1, -1), line_width, grey_0) # should depend on row_length
                            elif len(row.fields) == 2:
                                table_style.add('LINEBEFORE', (int(row_length/2), 0), (int(row_length/2), -1), line_width, grey_0) # should depend on row_length
                            
                            # Handle top & bottom borders
                            if row_index == len(rows) - 1 and subsub_index == len(subsubsections) - 1:
                                table_style.add('LINEBELOW', (1, 0), (-2, -1), line_width, colors.black)
                            else: 
                                table_style.add('LINEBELOW', (1, 0), (-2, -1), line_width, colors.grey)
                            
                            if row_index == 0 and subsub_index == 0:
                                table_style.add('LINEABOVE', (1, 0), (-2, -1), line_width, colors.black)
                            else:
                                table_style.add('LINEABOVE', (1, 0), (-2, 0), line_width, grey_0)
                            table_style.add('ALIGN', (1, 0), (-2, 0), 'RIGHT'),
                                

                        elif subsection.style == cl.SubsectionStyle.QA_LIGHTBORDER:
                            table_style.add('TOPPADDING', (1, 0), (-2, -1), 5)
                            table_style.add('BOTTOMPADDING', (1, 0), (-2, -1), 5)

                            # Handle left & right borders
                            if len(row.fields) == 3:
                                for i in range(row_length-2):
                                    x=i*2
                                    table_style.add('LINEBEFORE', (x+1, 0), (x+1, -1), line_width, grey_0) # should depend on row_length
                            elif len(row.fields) == 2:
                                table_style.add('LINEBEFORE', (int(row_length/2), 0), (int(row_length/2), -1), line_width, grey_0) # should depend on row_length
                            
                            # Handle top & bottom borders
                            if row_index == len(rows) - 1 and subsub_index == len(subsubsections) - 1:
                                table_style.add('LINEABOVE', (1, 0), (-2, 0), line_width, grey_0)
                                table_style.add('LINEBELOW', (1, 0), (-2, -1), line_width, colors.black)
                            elif row_index == 0 and subsub_index == 0:
                                table_style.add('LINEABOVE', (1, 0), (-2, -1), line_width, colors.black)
                                table_style.add('LINEBELOW', (1, 0), (-2, -1), line_width, grey_0)
                            else:
                                table_style.add('LINEBELOW', (1, 0), (-2, -1), line_width, grey_0)
                                table_style.add('LINEABOVE', (1, 0), (-2, 0), line_width, grey_0)
                            table_style.add('ALIGN', (1, 0), (-2, 0), 'RIGHT'),

                        elif subsection.style == cl.SubsectionStyle.QA_BOARDERLESS:
                            table_style.add('TOPPADDING', (1, 0), (-2, -1), 5),
                            table_style.add('BOTTOMPADDING', (1, 0), (-2, -1), 5),
                            # Add a bottom border for the last row
                            if row_index == len(rows) - 1 and subsub_index == len(subsubsections) - 1:
                                table_style.add('LINEBELOW', (1, 0), (-2, -1), line_width, colors.black),
                            if row_index == 0 and subsub_index == 0:
                                table_style.add('LINEABOVE', (1, 0), (-2, -1), line_width, colors.black),
                        

                        elif subsection.style == cl.SubsectionStyle.HEADING:
                            table_style.add('BACKGROUND', (1, 0), (-2, 0), grey_0)
                            table_style.add('SPAN', (1, 0), (-2, 0))
                            table_style.add('LINEBELOW', (1, 0), (-2, -1), line_width, colors.black),
                            table_style.add('LINEABOVE', (1, 0), (-2, 0), line_width, colors.black),
                        
                            table.keepWithNext = True
                            

                        table_style.add('LINEAFTER', (0, 0), (0, -1), line_width, colors.black),
                        table_style.add('LINEBEFORE', (-1, 0), (-1, -1), line_width, colors.black),

                        # Set the style to the table
                        table.setStyle(table_style)

                                            
                        elements.append(table)

            
            # Add space between form sections
            elements.append(Spacer(1, 12))

    return elements
