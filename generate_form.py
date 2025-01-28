import math
import pandas as pd
from decimal import Decimal
from typing import List, Union
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import Table, TableStyle, Paragraph, PageBreak, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from copy import deepcopy
from enum import Enum

line_placeholder='_' * 40
   
# So at the moment, one table is made and added to our elements array, before returning the elements array.

# I am interested in chunking this into new tables for each 

# Get the predefined styles
styles = getSampleStyleSheet()

normal_style = styles['Normal']
normal_style.fontSize = 8
normal_style.fontName = 'DejaVuSans'  # Use the registered font
normal_style.leading = 10

center_style = deepcopy(styles['Normal'])
center_style.alignment = 1  # Center alignment

section_header_style = deepcopy(styles['Normal'])
section_header_style.fontSize = 10
section_header_style.fontName = 'DejaVuSans-Bold'

form_header_style = styles['Heading1']
form_header_style.fontSize = 12
form_header_style.leading = 12
form_header_style.fontName = 'DejaVuSans-Bold'  # Use the registered font
form_header_style.leftIndent = -2

title_style = styles['Title']
title_style.fontSize = 16
title_style.leading = 20
title_style.fontName = 'DejaVuSans-Bold'

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


# Custom class to store data, question, and answer for form.
class Field:
    def __init__(self, 
                 data: List, 
                 isHeading: bool,
                 title: Paragraph=None, 
                 question: Paragraph=None, 
                 answer: List[Paragraph]=None,
                 ):
        self.data = data                    # List of rows
        self.isHeading = isHeading
        self.title = title                  # Paragraph object
        self.question = question            # Paragraph object
        self.answer = answer                # List of Paragraph objects
        self.question_width: float = None   # 1/6 or 2/6 of total width
        self.answer_width: float = None     # 1/6 or 2/6 of total width
        self.q_rows: List[int] = None       # number of rows for Q at width 1/6 and 2/6
        self.a_rows: List[int] = None       # number of rows for A at width 1/6 and 2/6
    
    '''
        These two functions (get answer width and get question width) are both pretty simple. They take the number
        of rows that the question and answer occupy at 1/6 width and 2/6 width, making stylistic descisions based on
        the number of rows that are being used.  
        
        At default, both will return 1/6, as this looks best. 

        Despite that, logic is added so that for X condition, Y length is chosen. 
        For clarity, add logic for conditions that return 1/6 as well as 2/6
    '''
    
    # Get how many rows to be used when short or long 
    def calc_row_lengths(self):    

        # function takes a string, and row character length, and returns number of rows
        def string_to_rows(string: str, row_length: int):
            current_line_length = 0
            rows = 1  # Start with one row
            words = string.split()
            for word in words:
                if len(word) > row_length:
                    # Handle words longer than row_length
                    if current_line_length > 0:
                        # Finish the current line if not empty
                        rows += 1
                        current_line_length = 0
                    # Add as many rows as needed for the long word
                    rows += len(word) // row_length
                    current_line_length = len(word) % row_length  # Remainder for the next line
                else:
                    # Check if the word fits in the current line
                    if current_line_length + len(word) + (1 if current_line_length > 0 else 0) > row_length:
                        # Move to the next row
                        rows += 1
                        current_line_length = len(word)  # Start the new line with the current word
                    else:
                        # Add the word to the current line
                        current_line_length += len(word) + (1 if current_line_length > 0 else 0)  # Add a space if not the first word

      
            return rows


        # Adjust these values when the overall width, margins, or font change
            # they hold how many characters can fit in each row
        len_16 = 20
        len_26 = 43 

        # Holds Question number of rows when short or long
        q_text_len = len(self.question.text)
        q_16 = string_to_rows(self.question.text, len_16)
        q_26 = string_to_rows(self.question.text, len_26)

        # Holds Answer number of rows when short or long
        a_16 = 0
        a_26 = 0
        for line in self.answer:
            a_16 += string_to_rows(line.text, len_16)
            a_26 += string_to_rows(line.text, len_26)

        # Save final answers
        self.q_rows = [q_16, q_26]
        self.a_rows = [a_16, a_26]
        return


    def get_answer_width(self, q_16, q_26, a_16, a_26):
        a_dif = a_16 - a_26 
        q_dif = q_16 - q_26

        # if no difference between lengths, A is short
        if a_dif == 0:                  return 1/6
        
        # if answer is 2 rows longer...
        if a_dif > 2: 
            # then as long as question stays within normal range, A is long
            if (q_16 - a_26) < 3:       return 2/6
            return 2/6

        return 1/6
    
    def get_question_width(self, q_16, q_26, a_16, a_26, a_16_bool):
        a_dif = a_16 - a_26 
        q_dif = q_16 - q_26

        # if no difference between question lengths, keep it short
        if q_dif == 0:                  return 1/6 
            
        # if A is long, Q is short
        if a_16_bool == False:          return 1/6 
            
        # if 
        if (q_16 - a_16) >= 2:           return 2/6

        return 1/6
        
    def calc_question_answer_widths(self):
        # first, handle exceptions; places we already can know the width before starting.

        # If a date
        if self.data[0]['Text Validation Type OR Show Slider Number'] == 'date_dmy':
            self.question_width = 1/6
            self.answer_width = 2/6
            return
        
        # If a short answer:
        if self.answer[0].text.startswith(line_placeholder):
            self.question_width = 1/6
            self.answer_width = 2/6
            return

        # if not an exception, calculate widths procedurally

        # Get Answer Width first, as it is useful to determine question width
        self.answer_width = self.get_answer_width(self.q_rows[0], self.q_rows[1], self.a_rows[0], self.a_rows[1])

        # Get Question Width, knowing the length of the answer
        a_isShort = ( self.answer_width == 1/6 )
        self.question_width = self.get_question_width(self.q_rows[0], self.q_rows[1], self.a_rows[0], self.a_rows[1], a_isShort)

        return

    def setup_field(self):
        # Step 1: calculate rows for each field
        self.calc_row_lengths()
        # Step 2: calculate widths for each field
        self.calc_question_answer_widths()

# Custom class to store a row to be added to the PDF with both fields and 
class Row:
    # Width of the table, change if the overall form width changes
    table_width = 0.92

    def __init__(self, 
                 fields: List[Field]
                ):
        self.fields = fields
        self.columns: List[Union[Paragraph, List[Paragraph]]] = []
        self.widths: List[float] = []

    # For each row, run setup row to get column ready for adding onto the table by adding columns and setting widths for those columns   
    def setup_row(self):
        self.fill_columns()         # 1. Populate the columns with Paragraph(s) for that row
        self.reformat_row()
        self.fill_widths()          # 2. Decide column widths for that row
        self.add_spacers()          # 3. Add spacing to fill column width
        self.add_end_columns()      # 4. Add ends to column

    # Step 1 : Populate the columns with Paragraph(s) for that row
    def fill_columns(self):
        for field in self.fields:
            if field.isHeading:
                self.columns.append(field.title)
            else:
                self.columns.append(field.question)
                self.columns.append(field.answer)
                
    # Function to run AFTER everything has been distributed. 
    # This one looks at each question, and if it can be longer, make it longer.
    def reformat_row(self):
        # Dismiss if isHeading
        if self.fields[0].isHeading: return

        # if one variable
        if (len(self.fields) == 1):
            field = self.fields[0]
            if field.answer_width == 1/6:
                if field.a_rows[0] > field.a_rows[1]:
                    field.answer_width = 2/6

            if field.question_width == 1/6:
                if (field.q_rows[0] - field.q_rows[1]) > 0:
                    if (field.q_rows[0] > field.a_rows[1]):
                        field.question_width = 2/6

        # if two variables
        if (len(self.fields) == 2):
            l_field = self.fields[0] # left field
            r_field = self.fields[1] # right field

            
            if l_field.answer_width == 1/6 and l_field.question_width == 1/6:
                if l_field.a_rows[0] > l_field.a_rows[1]:
                    l_field.answer_width = 2/6

            if r_field.answer_width == 1/6 and r_field.question_width == 1/6:
                if r_field.a_rows[0] > r_field.a_rows[1]:
                    r_field.answer_width = 2/6

        # regardless of number of fields, center Q when needed
        for field in self.fields:
            isShort = field.question_width == 1/6
            if isShort:
                if field.q_rows[0] <= 3:
                    field.question.style = center_style
            else:
                if field.q_rows[1] <= 2:
                    field.question.style = center_style


    # Step 2 : Find column widths for that row
    def fill_widths(self):
        for field in self.fields:
            if field.isHeading:
                self.widths.append(self.table_width)
            else:
                self.widths.append(field.question_width  * self.table_width)
                self.widths.append(field.answer_width  * self.table_width)
                

    # Step 3 : Add spacing to fill column width
    def add_spacers(self):
        
        # don't add spacers to headings
        if self.fields[0].isHeading:
            return
        
        # Get total width
        total_width = 0
        for width in self.widths:
            total_width += width

        # if total width is a full row, move on.
        if total_width >= (self.table_width - .001):
            return
        
        if len(self.fields) == 1:
            left_spacer_width = (self.table_width * 0.5) - ( total_width )
            right_spacer_width = (self.table_width * 0.5) + (self.table_width * 0.5) - ( total_width )
            spacer_width = ( (self.table_width / 2) - ( total_width / 2 ) )

            # Add widths to list
            self.widths.insert(0, 0)           # Set width left column
            self.widths.append(right_spacer_width)             # Set width right column
            # Add blank columns to list
            self.columns.insert(0, None)                # Add column before first column
            self.columns.append(None)                   # Add column after last column

            return
        
        if len(self.fields) == 2:
        
            left_width = (self.fields[0].question_width +  self.fields[0].answer_width) * self.table_width
            right_width = (self.fields[1].question_width +  self.fields[1].answer_width) * self.table_width
           
            if (self.fields[0].question_width + self.fields[0].answer_width + self.fields[1].question_width +  self.fields[1].answer_width) == 14/6:
                left_spacer = 0
                right_spacer = 2/6 * self.table_width
            else:
                left_spacer = ( (self.table_width / 2) - ( left_width ) )
                right_spacer = ( (self.table_width / 2) - ( right_width ) )
            
            # Add widths to list
            self.widths.insert(4, right_spacer)         # Set width left column
            self.widths.insert(2, 0)                    # Set width right column
            # Add blank columns to list
            self.columns.insert(4, None)                # Add column before first column
            self.columns.insert(2, None)                # Add column after last column
            # Add widths to list
            self.widths.insert(2, left_spacer)          # Set width left column
            self.widths.insert(0, 0)                    # Set width right column
            # Add blank columns to list
            self.columns.insert(2, None)                # Add column before first column
            self.columns.insert(0, None)                # Add column after last column

            return

        
    # Step 4 : Add ends to column
    def add_end_columns(self):
        self.columns.insert(0, None)                # Add column before first column
        self.columns.append(None)                   # Add column after last column
        end_width = (1 - self.table_width) / 2;     # Get end width
        self.widths.insert(0, end_width)            # Set width first column
        self.widths.append(end_width)               # Set width last column



# Define an Enum for subsection types
class SubsectionStyle(Enum):
    HEADING = "heading"
    QA_DEFAULT = "qa_default"
    QA_LIGHTBORDER = "qa_lightborder"
    QA_BOARDERLESS = "qa_boarderless"

# Custom class to store sections of fields
class Subsection:
    def __init__(self,
                 fields: list[Field],
                 style: SubsectionStyle
                 ):
        self.fields = fields
        self.style = style
        self.rows: List[Row] = []
    
    # Function to divide fields into rows that make sense
    def divide_into_rows(self):

        ### Define variables ###
        rows: List[Row] = []
        current_row: Row = Row(fields=[])

        ### Iterate through self.fields ###
        for field in self.fields:

            # If a heading, add it to its own row and be done
            if field.isHeading:
                heading_row: Row = Row(fields=[field])
                rows.append(heading_row)
                continue

           
            
            # Otherwise, treat as a QA pair
            field.setup_field()



            # otherwise, figure out if it fits
            row_width = 0
            field_width = field.answer_width + field.question_width

            for i_field in current_row.fields:
                row_width += i_field.question_width
                row_width += i_field.answer_width

            if (row_width + field_width) <= 1:
                current_row.fields.append(field)

            else:
                rows.append(current_row)
                current_row = Row(
                    fields=[field]
                )

        if current_row.fields:
            rows.append(current_row)

        ### Save and return result ###
        self.rows = rows
        return rows
        
# Custom class section
class Section:
    def __init__(self,
                 fields: list[Field]
                 ):
        self.fields = fields
        self.subsections: List[Subsection] = []

    def divide_by_branchingLogic(self):
        """Divides self.fields into subsections based on headings and dependencies."""

        ### Define variables ###
        subsections: List[Subsection] = []
        subsection_fields: List[Field] = []
        subsection_dependencies_set = set()
        subsection_names_set = set()

        ### Define local functions ###
        def extract_dependencies(branching_logic: str):
            """Extract dependencies from a branching logic string."""
            if not branching_logic:
                return set()
            import re
            pattern = r'\[([^\]]+)\]'  # Matches content within square brackets
            matches = re.findall(pattern, branching_logic)
            
            for match in matches:
                if match.endswith('t(88)'):
                    matches.append(match.removesuffix('t(88)'))
                    
            return set(matches)

        def finalize_subsection(style):
            """Finalize the current subsection and reset tracking variables."""
            nonlocal subsection_fields, subsection_dependencies_set, subsection_names_set
            if subsection_fields:
                if len(subsection_fields) <= 10:
                    subsections.append(Subsection(subsection_fields, style=SubsectionStyle.QA_BOARDERLESS))
                else: 
                    subsections.append(Subsection(subsection_fields, style=style))
            subsection_fields = []
            subsection_dependencies_set = set()
            subsection_names_set = set()

        ### Iterate through self.fields ###
        for i, field in enumerate(self.fields):
            # Handle headings
            if field.isHeading:

                if subsection_fields:
                    if subsection_dependencies_set == set():
                        finalize_subsection(SubsectionStyle.QA_DEFAULT)
                    else:
                        finalize_subsection(SubsectionStyle.QA_LIGHTBORDER)

                subsections.append(Subsection([field], SubsectionStyle.HEADING))
                continue

            ### Get field variables ###
            field_name: str = field.data[0].get('Variable / Field Name')
            branching_logic: str = (
                field.data[0].get('Branching Logic (Show field only if...)')
                if isinstance(field.data[0].get('Branching Logic (Show field only if...)'), str)
                else None
            )
            dependencies = extract_dependencies(branching_logic)

            # Get next field's dependencies
            next_logic: str = (
                self.fields[i + 1].data[0].get('Branching Logic (Show field only if...)')
                if (i + 1 < len(self.fields) and isinstance(self.fields[i + 1].data[0].get('Branching Logic (Show field only if...)'), str))
                else None
            )
            next_dependencies = extract_dependencies(next_logic)
            subsection_started = len(subsection_fields) > 0


            ### Process subsection logic ###
            if subsection_started:
                # Default subsection (no dependencies)
                if not subsection_dependencies_set:
                    if not dependencies and not next_dependencies:
                        subsection_fields.append(field)
                        subsection_names_set.add(field_name)
                    elif subsection_names_set.isdisjoint(dependencies):
                        finalize_subsection(SubsectionStyle.QA_DEFAULT)
                        subsection_fields.append(field)
                        subsection_names_set.add(field_name)
                        subsection_dependencies_set.update(dependencies, next_dependencies)
                    else:
                        
                        subsection_fields.append(field)
                        subsection_names_set.add(field_name)
                        subsection_dependencies_set.update(dependencies, next_dependencies)
                # Dependency-rich subsection
                else:                 
                    # if current subsection has dependencies AND name is IN dependencies
                    # if current subsection has dependencies and last de
                    
                    # if current dependencies overlap with last dependencies, keep it going
                    # if current dependencies overlap with subsection names, keep it going

                    #
                    dependency_overlap = not subsection_dependencies_set.isdisjoint(dependencies)
                    name_overlap = not subsection_names_set.isdisjoint(dependencies)

                    if not dependency_overlap and not name_overlap:
                        finalize_subsection(SubsectionStyle.QA_LIGHTBORDER)

                    subsection_fields.append(field)
                    subsection_names_set.add(field_name)
                    subsection_dependencies_set.update(dependencies, next_dependencies)
            else:
                # Start a new subsection
                subsection_fields.append(field)
                subsection_names_set.add(field_name)
                subsection_dependencies_set.update(dependencies, next_dependencies)

        ### Finalize the last subsection ###
        if subsection_fields:
            if subsection_dependencies_set == set():
                finalize_subsection(SubsectionStyle.QA_DEFAULT)
            else:
                finalize_subsection(SubsectionStyle.QA_LIGHTBORDER)

        ### Save and return result ###
        self.subsections = subsections
        return subsections

    def divide_all(self):
        """Divides self.fields into subsections based on group field type."""

        ### Define variables ###
        subsections: List[Subsection] = []
        subsection_fields: List[Field] = []

        ### Define local functions ###
        def finalize_subsection(style):
            nonlocal subsection_fields, subsections
            """Finalize the current subsection and reset tracking variables."""
            if subsection_fields:
                if len(subsection_fields) <= 10:
                    subsections.append(Subsection(subsection_fields, style=SubsectionStyle.QA_BOARDERLESS))
                else: 
                    subsections.append(Subsection(subsection_fields, style=style))
            subsection_fields = []



        ### Iterate through self.fields ###
        for i, field in enumerate(self.fields):
            # Handle headings
            if field.isHeading:
                # if currently a subsection, finish it
                if subsection_fields:
                    finalize_subsection(SubsectionStyle.QA_DEFAULT)
                # then add heading subsection
                subsections.append(Subsection([field], SubsectionStyle.HEADING))
                continue

            ### Get field variables ###
            subsection_fields.append(field)

        ### Finalize the last subsection ###
        if subsection_fields:

            finalize_subsection(SubsectionStyle.QA_DEFAULT)

        ### Save and return result ###
        self.subsections = subsections
        return subsections
    
    def divide_into_subsections(self):
        return self.divide_by_branchingLogic()

# Generates the array of elements for a pdf of several forms from the data_dictionary
def generate_form(doc, data_dictionary, elements):
    # Iterate through each form (ie: Presentation, Medication, etc.)
    for form_name in data_dictionary['Form Name'].drop_duplicates():

        group = data_dictionary[data_dictionary['Form Name'] == form_name]

        # Add form name as a title for each table
        elements.append(PageBreak())
        elements.append(Paragraph(form_name.upper(), form_header_style))
      
        # Form Sections are a way of splitting up the data into lists of Fields
            # where each field represents a heading or Question Answer pair.

        sections = get_sections(group)

        # For each section, divide into subsections
        for section in sections:   

            subsections = section.divide_into_subsections()

            # For each subsection, divide into rows
            for subsection in subsections:

                rows = subsection.divide_into_rows()

                if rows is None:
                    continue

                # For each row, setup to get columns and widths
                    # Then, style it and add it to elements
                for row_index,row in enumerate(rows):

                    if row is None:
                        continue

                    row.setup_row()

                    # Here on is the final step, styling it and adding the row as a table to the page

                    # Scale column widths to fit page width
                    width, height = letter
                    line_width = .75

                    colWidths = [w * width for w in row.widths]
                    table = Table([row.columns], colWidths = colWidths)
                    row_length = len(row.columns)

                    crfgrey = colors.hsl2rgb(0, 0, .7)

                    # Apply base style
                    style = TableStyle([
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
                
                    # Apply specific styles based on subsection type
                    if subsection.style == SubsectionStyle.QA_DEFAULT:
                        style.add('TOPPADDING', (1, 0), (-2, -1), 5)
                        style.add('BOTTOMPADDING', (1, 0), (-2, -1), 5)

                        # Handle left & right borders
                        if len(row.fields) == 3:
                            for i in range(row_length-2):
                                x=i*2
                                style.add('LINEBEFORE', (x+1, 0), (x+1, -1), line_width, crfgrey) # should depend on row_length
                        elif len(row.fields) == 2:
                            style.add('LINEBEFORE', (int(row_length/2), 0), (int(row_length/2), -1), line_width, crfgrey) # should depend on row_length
                        
                        # Handle top & bottom borders
                        if row_index == len(rows) - 1:
                            style.add('LINEABOVE', (1, 0), (-2, 0), line_width, crfgrey)
                            style.add('LINEBELOW', (1, 0), (-2, -1), line_width, colors.black)
                        elif row_index == 0:
                            style.add('LINEABOVE', (1, 0), (-2, -1), line_width, colors.black)
                            style.add('LINEBELOW', (1, 0), (-2, -1), line_width, crfgrey)
                        else:
                            style.add('LINEBELOW', (1, 0), (-2, -1), line_width, colors.grey)
                            style.add('LINEABOVE', (1, 0), (-2, 0), line_width, crfgrey)
                        style.add('ALIGN', (1, 0), (-2, 0), 'RIGHT'),
                            

                    elif subsection.style == SubsectionStyle.QA_LIGHTBORDER:
                        style.add('TOPPADDING', (1, 0), (-2, -1), 5)
                        style.add('BOTTOMPADDING', (1, 0), (-2, -1), 5)

                        # Handle left & right borders
                        if len(row.fields) == 3:
                            for i in range(row_length-2):
                                x=i*2
                                style.add('LINEBEFORE', (x+1, 0), (x+1, -1), line_width, crfgrey) # should depend on row_length
                        elif len(row.fields) == 2:
                            style.add('LINEBEFORE', (int(row_length/2), 0), (int(row_length/2), -1), line_width, crfgrey) # should depend on row_length
                        
                        # Handle top & bottom borders
                        if row_index == len(rows) - 1:
                            style.add('LINEABOVE', (1, 0), (-2, 0), line_width, crfgrey)
                            style.add('LINEBELOW', (1, 0), (-2, -1), line_width, colors.black)
                        elif row_index == 0:
                            style.add('LINEABOVE', (1, 0), (-2, -1), line_width, colors.black)
                            style.add('LINEBELOW', (1, 0), (-2, -1), line_width, crfgrey)
                        else:
                            style.add('LINEBELOW', (1, 0), (-2, -1), line_width, crfgrey)
                            style.add('LINEABOVE', (1, 0), (-2, 0), line_width, crfgrey)
                        style.add('ALIGN', (1, 0), (-2, 0), 'RIGHT'),

                    elif subsection.style == SubsectionStyle.QA_BOARDERLESS:
                        style.add('TOPPADDING', (1, 0), (-2, -1), 5),
                        style.add('BOTTOMPADDING', (1, 0), (-2, -1), 5),
                        # Add a bottom border for the last row
                        if row_index == len(rows) - 1:
                            style.add('LINEBELOW', (1, 0), (-2, -1), line_width, colors.black),
                        if row_index == 0:
                            style.add('LINEABOVE', (1, 0), (-2, -1), line_width, colors.black),
                    

                    elif subsection.style == SubsectionStyle.HEADING:
                        style.add('BACKGROUND', (1, 0), (-2, 0), crfgrey)
                        style.add('SPAN', (1, 0), (-2, 0))
                        style.add('LINEBELOW', (1, 0), (-2, -1), line_width, colors.black),
                        style.add('LINEABOVE', (1, 0), (-2, 0), line_width, colors.black),
                        

                    style.add('LINEAFTER', (0, 0), (0, -1), line_width, colors.black),
                    style.add('LINEBEFORE', (-1, 0), (-1, -1), line_width, colors.black),

                    # Set the style to the table
                    table.setStyle(style)

                                        
                    elements.append(table)

            # Add space between form sections
            elements.append(Spacer(1, 12))

    return elements

# Return array of sections where each section of a form is an array of Fields
def get_sections(group):
    # form sections are a list of lists of fields, where then each section is a list of fields
    section_fields: list[list[Field]]  = []
    current_section_name = None

    for _, row in group.iterrows():
        if '>' in row['Field Label'][0:2]:
            continue

        # If row part of new section, add Section Header field
        if row['Section Header'] != current_section_name and pd.notna(row['Section Header']):
            section_fields.append([])
            current_section_name = row['Section Header']
            current_section_index = len(section_fields) - 1
            section_fields[current_section_index].append(
                Field(
                    data=[row],
                    isHeading=True,
                    title=Paragraph(current_section_name, section_header_style)
                )
            )
        # If form_sections isn't yet started, add 
        if len(section_fields) == 0:
            section_fields.append([])

        current_section_index = len(section_fields) - 1
        section_fields[current_section_index] = add_field_to_section(row, section_fields[current_section_index])

    sections: List[Section] = []
    for fields_list in section_fields:
        sections.append(Section(fields=fields_list))

    return sections

# Return section after appending new field to it, or modifying old one
def add_field_to_section(row, section: list[Field]):

    # Create a new field with question and placeholder answer
    new_field = Field(
        data=[row],
        isHeading = False,
        question = Paragraph(row['Field Label'], normal_style),
        answer=[]
    )

    validation = row['Text Validation Type OR Show Slider Number']

    ### ! Handle special cases (add to last question) ###
    # if other (main)
    if row['Variable / Field Name'].endswith(("_oth", "_other", "oth", "_otherl3")):
        # Add "Specify Other" to the last field's answer
        #section[-1].answer.text = section[-1].answer.text + '</br>' + 'Specify Other: ' + line_placeholder
        section[-1].answer.append(Paragraph('<i>Specify Other: </i> ' + "_" * 18, normal_style))
        section[-1].data.append(row)

    # if other (extras)
    elif row['Variable / Field Name'].endswith("_otherl2"):
        return section
    
    # if units
    elif row['Variable / Field Name'].endswith("_units"):
        # Add "Units" to the last field's answer
        section[-1].answer.append(Paragraph(f"Units:" + "_" * (18-len("Units:")), normal_style))
        section[-1].data.append(row)
        #section[-1].answer.text = section[-1].answer.text + '</br>' + 'Units: ' + "_" * 20
    


    ### ! Handle most cases (add as new question) ###
    # if a multi select
    elif row['Field Type'] in ['radio', 'dropdown', 'checkbox', 'list', 'user_list', 'multi_list']:
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
            return section

        choices = [symbol + choice.split(',', 1)[-1].strip() for choice in row['Choices, Calculations, OR Slider Labels'].split('|')]
        if len(choices) < 15:
            new_field.answer = [Paragraph(choice, normal_style) for choice in choices]
        else:
            return section
            new_field.answer = [Paragraph(line_placeholder, normal_style)]
        section.append(new_field)
    
    # if a date


    elif row['Field Type'] == 'text':
        # if date
        if validation == 'date_dmy':
            # Add a date placeholder
            date_str = """[<font color="lightgrey">_D_</font>][<font color="lightgrey">_D_</font>]/[<font color="lightgrey">_M_</font>][<font color="lightgrey">_M_</font>]/[_2_][_0_][<font color="lightgrey">_Y_</font>][<font color="lightgrey">_Y_</font>]"""
            new_field.answer = [Paragraph(date_str, normal_style)]
            section.append(new_field)
        # if time
        elif validation == 'time':
            # Add a time placeholder
            time_str = "_"*18
            new_field.answer = [Paragraph(time_str, normal_style)]
            section.append(new_field)
        # if number
        elif validation == 'number':
            number_str = "_"*18
            new_field.answer = [Paragraph(number_str, normal_style)]
            section.append(new_field)
        else:
            # Open-ended questions
            new_field.answer = [Paragraph(line_placeholder, normal_style)]
            section.append(new_field)

    return section



def format_choices(choices_str, field_type, threshold=65):
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
    elif field_type == 'checkbox' :
        symbol = "□ "
    elif field_type=='dropdown':
        symbol="↧ "
    else: 
        symbol = ""
    if len(choices_str.split('|'))<=15:
        choices = [symbol + choice.split(',', 1)[-1].strip() for choice in choices_str.split('|')]
        combined_choices = '   '.join(choices).strip()
    else:
        line_placeholder='_' * 40
        combined_choices = line_placeholder
    if len(combined_choices) > threshold:
        combined_choices = "\n".join(choices).strip()
    return combined_choices