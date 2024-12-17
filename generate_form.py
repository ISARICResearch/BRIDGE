import pandas as pd
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import Table, TableStyle, Paragraph, PageBreak
from reportlab.lib.styles import getSampleStyleSheet
from copy import deepcopy

line_placeholder='_' * 30

# Aidan: Format choices was moved into here to not reference paperCRF
    # This is required because we cannot have 'circular imports'
def format_choices(choices_str, field_type, threshold=30, same_line=False):

    """
    Format the choices string. If the combined length exceeds the threshold, use line breaks instead of commas.
    Prepend symbols based on the field type.
    """
    if field_type == 'radio':
        symbol = "○ "
    elif field_type=='list':
        symbol="○ "
    elif field_type=='user_list':
        symbol="○ " 
    elif field_type=='multi_list':
        symbol=  "□ "         
    elif field_type == 'checkbox' :
        symbol = "□ "
    elif field_type=='dropdown':
        symbol="↧ "
    else: 
        symbol = ""

    if True:
        if len(choices_str.split('|'))<=15:
            choices = [symbol + choice.split(',', 1)[-1].strip() for choice in choices_str.split('|')]
            combined_choices = '   '.join(choices).strip()
        else:
            combined_choices = line_placeholder
        if len(combined_choices) > threshold:
            # This doesn't work.  Need a new system to add new lines
            combined_choices = "\n".join(choices).strip()
        return combined_choices
    
    else:
        if len(choices_str.split('|'))<=15:
            choices = [symbol + choice.split(',', 1)[-1].strip() for choice in choices_str.split('|')]
            #combined_choices = choices
            #combined_choices = '   '.join(choices).strip()
            #print("Choices: " + str(choices))
            combined_choices = ''
            for choice in choices:
                combined_choices += Paragraph(choice)
            return combined_choices
        else:
            combined_choices = line_placeholder
        if len(combined_choices) > threshold:
            combined_choices = "\n".join(choices).strip()
        return combined_choices


def generate_form(doc, data_dictionary, elements):
        # Get the predefined styles
    styles = getSampleStyleSheet()

    normal_style = styles['Normal']
    normal_style.fontSize = 8
    normal_style.fontName = 'DejaVuSans'  # Use the registered font
    normal_style.leading = 10

    center_style = deepcopy(styles['Normal'])
    center_style.fontSize = 8
    center_style.leading = 10
    center_style.fontName = 'DejaVuSans'  # Use the registered font
    center_style.alignment = 1  # Center alignment

    header_style = styles['Heading1']
    header_style.fontSize = 12
    header_style.leading = 12
    header_style.fontName = 'DejaVuSans-Bold'  # Use the registered font
    header_style.leftIndent = -6

    title_style = styles['Title']
    title_style.fontSize = 16
    title_style.leading = 20
    title_style.fontName = 'DejaVuSans-Bold'

    for form_name in data_dictionary['Form Name'].drop_duplicates():

        group = data_dictionary[data_dictionary['Form Name'] == form_name]

        # Add form name as a title for each table
        elements.append(PageBreak())
        elements.append(Paragraph(form_name.upper(), header_style))
        data = []
        current_section = None

        section_heads = []
        section_index = []
        for index, row in group.iterrows():


            # Debug Lines
            print("\n\nROW: " + str(index))
            print("  Section Header: " + str(row['Section Header']))
            print("  Variable / Field Name: " + str(row['Variable / Field Name']))
            print("  Field Type: " + str(row['Field Type']))

            # Add new section
            if row['Section Header'] != current_section and pd.notna(row['Section Header']):
                current_section = row['Section Header']
                data.append(current_section)

            # On specify other, go back to last element and add new paragraph.
            if row['Variable / Field Name'].endswith(("_oth","_other","oth")):
                data[-1] = [data[-1], Paragraph('Specify Other' + '_' * 16, normal_style)]

            # On unit specification, add new units paragraph.
            elif row['Variable / Field Name'].endswith(("_units")):
                formatted_choices = format_choices(row['Choices, Calculations, OR Slider Labels'], row['Field Type'], True)
                data[-1] = [data[-1], Paragraph(f"Units: {formatted_choices}", normal_style)]

            # If row is a choice, format it as a paragraph.
            #elif row['Field Type'] in ['radio', 'dropdown', 'checkbox']:
            #    formatted_choices = format_choices(row['Choices, Calculations, OR Slider Labels'], row['Field Type'])
            #    data.append(Paragraph(row['Field Label'], normal_style))
            #    data.append(Paragraph(formatted_choices, normal_style))
            #    data[-1] = [data[-1], Paragraph(f"Edit: {formatted_choices}", normal_style)]
            #    data[-1] = [data[-1], Paragraph(f"Edit: {formatted_choices}", normal_style)]

            elif row['Field Type'] in ['radio', 'dropdown', 'checkbox']:
                #print(str(row['Choices, Calculations, OR Slider Labels']))
                #formatted_choices = format_choices(row['Choices, Calculations, OR Slider Labels'], row['Field Type'])
                choices = ["○ " + choice.split(',', 1)[-1].strip() for choice in row['Choices, Calculations, OR Slider Labels'].split('|')]
                data.append(Paragraph(row['Field Label'], normal_style))
                data.append(Paragraph('', normal_style))
                if len(choices) <= 6:
                    for choice in choices:
                        #print(choice)
                        data[-1] = [data[-1], Paragraph(f"{choice}", normal_style)]
                        #data.append(Paragraph(choice))

            elif row['Text Validation Type OR Show Slider Number'] == 'date_dmy':
                date_str = """[<font color="lightgrey">_D_</font>][<font color="lightgrey">_D_</font>]/[<font color="lightgrey">_M_</font>][<font color="lightgrey">_M_</font>]/[_2_][_0_][<font color="lightgrey">_Y_</font>][<font color="lightgrey">_Y_</font>]"""
                data.append(Paragraph(row['Field Label'], normal_style))
                data.append(Paragraph(date_str, normal_style))  # Placeholder for date input
            else:
                data.append(Paragraph(row['Field Label'], normal_style))
                data.append(Paragraph(line_placeholder, normal_style))  # Placeholder for text input

        x = []
        for i in data:
            if isinstance(i, str):
                j = data.index(i)
                if j % 4 == 0:
                    data.insert(j + 1, None)
                    data.insert(j + 2, None)
                    data.insert(j + 3, None)
                    x.append(int((j + 4) / 4))
                elif j % 4 == 1:
                    data.insert(j + 0, None)
                    data.insert(j + 1, None)
                    data.insert(j + 2, None)
                    x.append(int((j + 3) / 4))
                elif j % 4 == 2:
                    data.insert(j + 0, None)
                    data.insert(j + 1, None)
                    x.append(int((j + 2) / 4))
                elif j % 4 == 3:
                    data.insert(j + 0, None)
                    x.append(int((j + 1) / 4))

        datas = [data[i:i+4] for i in range(0, len(data), 4)]

        data = datas
        matching_indices = [i for i, sublist in enumerate(data) if
                            sublist[1:] == [None, None, None] and sublist[0] is not None]

        for inner_list in data:
            inner_list.insert(0, "")
            inner_list.insert(5, "")

        width, height = letter
        line_width = .5
        table_width = width #- 2 * doc.leftMargin
        # Change made: column widths to allow full date input on a line. 
        # From .23/.23 to .17/.29 -- this is minimum answer width to support viewing whole date on one line.
        table = Table(data, colWidths=[width * 0.035, width * 0.175, width * 0.29, width * 0.175, width * 0.29, width * 0.035])
        style = TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (0, -1), 30),
            ('LINEBELOW', (1, 0), (-2, -1), line_width, colors.black),
            ('LINEABOVE', (1, 0), (-2, 0), line_width, colors.black),
            ('LINEBEFORE', (3, 0), (3, -1), line_width, colors.black),
            ('LINEAFTER', (0, 0), (0, -1), line_width, colors.black),
            ('LINEAFTER', (4, 0), (4, -1), line_width, colors.black),
        ])

        for row in matching_indices:
            style.add('BACKGROUND', (1, row), (-2, row), colors.grey)
            style.add('SPAN', (1, row), (-2, row))

        table.setStyle(style)
        elements.append(table)

    return elements