""" This Generate Form script is for defining the classes, properties, and methods needed to create the forms """

''' 
It defines:
Section >               a group of questions in a form, all under on Section Header (usually)
  Subsection >          a group of all connected or all disconnected questions within a section
  SubsectionStyle           simply an enum for the subsection to define how it should be styled (BL, Heading, or neither)
    Subsubsection >     a group of questions in a subsection. Only matter if connected by Branching Logic
      Row >             a row of fields on the final sheet
        Field >         a single item on the form. Can be a question / answer pair or a Heading
          Dependency    each field can have dependencies, this holds the dependencies from the Branching Logic in a clear and reproducable way

'''

from enum import Enum
from typing import List, Union

from reportlab.platypus import Paragraph

import src.generate_pdf.styles as style

line_placeholder = '_' * 40


# Custom class to store a dependency
class Dependency:
    def __init__(self, field_name: str, operator: str, value: str):
        self.field_name = field_name  # The question this depends on (e.g. 'expo14_yn')
        self.operator = operator  # Comparison operator (e.g. '=', '>', etc.)
        self.value = value  # Required value (e.g. '1')


# Custom class to store data, question, and answer for form.
class Field:
    def __init__(self,
                 name: str,
                 data: List,
                 dependencies: List[Dependency] = [],
                 is_heading: bool = False,
                 is_text: bool = False,
                 is_descriptive: bool = False,
                 title: Paragraph = None,
                 question: Paragraph = None,
                 answer: List[Paragraph] = None,
                 ):
        self.name = name
        self.data = data  # List of rows
        self.dependencies = dependencies
        self.is_heading = is_heading
        self.is_text = is_text
        self.is_descriptive = is_descriptive
        self.title = title  # Paragraph object for Headings
        self.question = question  # Paragraph object
        self.answer = answer  # List of Paragraph objects
        self.question_width: float = None  # 1/6 or 2/6 of total width
        self.answer_width: float = None  # 1/6 or 2/6 of total width
        self.q_rows: List[int] = None  # number of rows for Q at width 1/6 and 2/6
        self.a_rows: List[int] = None  # number of rows for A at width 1/6 and 2/6

    @property
    def parent_questions(self) -> List[str]:
        """Returns list of parent question names this field depends on"""
        return [d.field_name for d in self.dependencies if d.field_name]

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
                        current_line_length += len(word) + (
                            1 if current_line_length > 0 else 0)  # Add a space if not the first word

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
        if a_dif == 0:                  return 1 / 6

        # if answer is 2 rows longer...
        if a_dif > 2:
            # then as long as question stays within normal range, A is long
            if (q_16 - a_26) < 3:       return 2 / 6
            return 2 / 6

        return 1 / 6

    def get_question_width(self, q_16, q_26, a_16, a_26, a_16_bool):
        a_dif = a_16 - a_26
        q_dif = q_16 - q_26

        # if no difference between question lengths, keep it short
        if q_dif == 0:                  return 1 / 6

        # if A is long, Q is short
        if a_16_bool == False:          return 1 / 6

        # if 
        if (q_16 - a_16) >= 2:           return 2 / 6

        return 1 / 6

    def calc_question_answer_widths(self):

        # first, handle exceptions; places we already can know the width before starting.

        # If a date
        if self.data[0]['Text Validation Type OR Show Slider Number'] == 'date_dmy':
            self.question_width = 1 / 6
            self.answer_width = 2 / 6
            return

        # If a short answer:
        if self.answer[0].text.startswith(line_placeholder):
            self.question_width = 1 / 6
            self.answer_width = 2 / 6
            return

        # if not an exception, calculate widths procedurally

        # Get Answer Width first, as it is useful to determine question width
        self.answer_width = self.get_answer_width(self.q_rows[0], self.q_rows[1], self.a_rows[0], self.a_rows[1])

        # Get Question Width, knowing the length of the answer
        a_isShort = (self.answer_width == 1 / 6)
        self.question_width = self.get_question_width(self.q_rows[0], self.q_rows[1], self.a_rows[0], self.a_rows[1],
                                                      a_isShort)

        return

    def setup_field(self):

        # If a descriptive header
        if self.is_descriptive:
            self.question_width = 1  # Make question take up the entire row
            self.answer_width = 0  # No answer text
            self.q_rows: List[int] = [0, 0]  # number of rows for Q at width 1/6 and 2/6
            self.a_rows: List[int] = [0, 0]  # number of rows for A at width 1/6 and 2/6
            return

            # If a text branching logic gate
        if self.is_text:
            self.question_width = 2 / 6  # 1/6 or 2/6 of total width
            self.answer_width = 0  # 1/6 or 2/6 of total width
            self.q_rows: List[int] = [0, 0]  # number of rows for Q at width 1/6 and 2/6
            self.a_rows: List[int] = [0, 0]  # number of rows for A at width 1/6 and 2/6
            return

        # Step 1: calculate rows for each field
        self.calc_row_lengths()
        # Step 2: calculate widths for each field
        self.calc_question_answer_widths()


# Custom class to store a row to be added to the PDF with both fields and
class Row:
    # Width of the table, change if the overall form width changes
    table_width = 0.92

    def __init__(self,
                 fields: List[Field],
                 # We shade based on row because rows are created as Report Lab tables, letting us easily apply a shade to that table
                 # the options below reflect the use, so that rather than saying 'light grey', we just say what we are shading, and make that light grey
                 shade: style.RowShade = "none"
                 ):
        self.fields = fields
        self.shade: style.RowShade = shade  # We shade based on row because rows count as Report Lab tables, letting us easily apply a shade to that table
        self.columns: List[Union[Paragraph, List[Paragraph]]] = []
        self.widths: List[float] = []

    # For each row, run setup row to get column ready for adding onto the table by adding columns and setting widths for those columns   
    def setup_row(self):
        self.fill_columns()  # 1. Populate the columns with Paragraph(s) for that row
        self.reformat_row()
        self.fill_widths()  # 2. Decide column widths for that row
        self.add_spacers()  # 3. Add spacing to fill column width
        self.add_end_columns()  # 4. Add ends to column

    # Step 1 : Populate the columns with Paragraph(s) for that row
    def fill_columns(self):
        for field in self.fields:
            if field.is_heading:
                self.columns.append(field.title)

            else:
                self.columns.append(field.question)
                self.columns.append(field.answer)

    # Function to run AFTER everything has been distributed. 
    # This one looks at each question, and if it can be longer, make it longer.
    def reformat_row(self):
        # Dismiss if is_heading
        if self.fields[0].is_heading: return

        # if one variable
        if (len(self.fields) == 1):
            field = self.fields[0]
            if field.answer_width == 1 / 6:
                if field.a_rows[0] > field.a_rows[1]:
                    field.answer_width = 2 / 6

            if field.question_width == 1 / 6:
                if (field.q_rows[0] - field.q_rows[1]) > 0:
                    if (field.q_rows[0] > field.a_rows[1]):
                        field.question_width = 2 / 6

        # if two variables
        if (len(self.fields) == 2):
            l_field = self.fields[0]  # left field
            r_field = self.fields[1]  # right field

            if l_field.answer_width == 1 / 6 and l_field.question_width == 1 / 6:
                if l_field.a_rows[0] > l_field.a_rows[1]:
                    l_field.answer_width = 2 / 6

            if r_field.answer_width == 1 / 6 and r_field.question_width == 1 / 6:
                if r_field.a_rows[0] > r_field.a_rows[1]:
                    r_field.answer_width = 2 / 6

        # regardless of number of fields, center Q when needed
        for field in self.fields:
            if field.is_text: continue
            if field.is_descriptive: continue
            isShort = field.question_width == 1 / 6
            if isShort:
                if field.q_rows[0] <= 3:
                    field.question.style = style.center
            else:
                if field.q_rows[1] <= 2:
                    field.question.style = style.center

    # Step 2 : Find column widths for that row
    def fill_widths(self):
        for field in self.fields:
            if field.is_heading:
                self.widths.append(self.table_width)
            else:
                self.widths.append(field.question_width * self.table_width)
                self.widths.append(field.answer_width * self.table_width)

    # Step 3 : Add spacing to fill column width
    def add_spacers(self):

        # don't add spacers to headings
        if self.fields[0].is_heading:
            return

        # Get total width
        total_width = 0
        for width in self.widths:
            total_width += width

        # if total width is a full row, move on.
        if total_width >= (self.table_width - .001):
            return

        if len(self.fields) == 1:
            left_spacer_width = (self.table_width * 0.5) - (total_width)
            right_spacer_width = (self.table_width * 0.5) + (self.table_width * 0.5) - (total_width)
            spacer_width = ((self.table_width / 2) - (total_width / 2))

            # Add widths to list
            self.widths.insert(0, 0)  # Set width left column
            self.widths.append(right_spacer_width)  # Set width right column
            # Add blank columns to list
            self.columns.insert(0, None)  # Add column before first column
            self.columns.append(None)  # Add column after last column

            return

        if len(self.fields) == 2:

            left_width = (self.fields[0].question_width + self.fields[0].answer_width) * self.table_width
            right_width = (self.fields[1].question_width + self.fields[1].answer_width) * self.table_width

            if (self.fields[0].question_width + self.fields[0].answer_width + self.fields[1].question_width +
                self.fields[1].answer_width) == 14 / 6:
                left_spacer = 0
                right_spacer = 2 / 6 * self.table_width
            else:
                left_spacer = ((self.table_width / 2) - (left_width))
                right_spacer = ((self.table_width / 2) - (right_width))

            # Add widths to list
            self.widths.insert(4, right_spacer)  # Set width left column
            self.widths.insert(2, 0)  # Set width right column
            # Add blank columns to list
            self.columns.insert(4, None)  # Add column before first column
            self.columns.insert(2, None)  # Add column after last column
            # Add widths to list
            self.widths.insert(2, left_spacer)  # Set width left column
            self.widths.insert(0, 0)  # Set width right column
            # Add blank columns to list
            self.columns.insert(2, None)  # Add column before first column
            self.columns.insert(0, None)  # Add column after last column

            return

    # Step 4 : Add ends to column
    def add_end_columns(self):
        self.columns.insert(0, None)  # Add column before first column
        self.columns.append(None)  # Add column after last column
        end_width = (1 - self.table_width) / 2  # Get end width
        self.widths.insert(0, end_width)  # Set width first column
        self.widths.append(end_width)  # Set width last column


# Custom class to store sections of fields
class Subsubsection:
    def __init__(self,
                 fields: list[Field],
                 parent: str = None,
                 header: list[Field] = None,
                 is_conditional: bool = False,
                 ):
        self.fields = fields
        self.header = header
        self.parent = parent
        self.is_conditional = is_conditional
        self.rows: List[Row] = []

    # Function to divide fields into rows that make sense
    def divide_into_rows(self):
        rows: List[Row] = []

        is_header = bool(self.header)

        shade = is_header

        def get_shade(is_header: bool, is_descriptive: bool) -> style.RowShade:
            return "conditional" if is_header else "descriptive" if is_descriptive else "none"

        # this is honestly confusing
        # It's checking if it's a top row in a conditional section, so it has to reset the shading.
        if is_header:
            self.header[0].setup_field()
            self.header[1].setup_field()
            heading_row: Row = Row(fields=[self.header[0], self.header[1]], shade="none")
            rows.append(heading_row)

        ### Define variables ###
        current_row: Row = Row(fields=[])

        ### Iterate through self.fields ###
        for field in self.fields:

            is_descriptive = field.is_descriptive

            # If a heading, add it to its own row and be done
            if field.is_heading:
                heading_row: Row = Row(fields=[field])
                heading_row.shade = "conditional"
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
                current_row.shade = get_shade(is_header, is_descriptive)
                current_row.fields.append(field)

            else:
                rows.append(current_row)
                current_row = Row(
                    fields=[field],
                    shade=get_shade(is_header, is_descriptive)
                )

        if current_row.fields:
            rows.append(current_row)

        ### Save and return result ###
        self.rows = rows
        return rows


# Define an Enum for subsection types
class SubsectionStyle(Enum):
    HEADING = "heading"
    QA_BLACK = "QA_BLACK"
    QA_GREY = "QA_GREY"
    QA_BOARDERLESS = "qa_boarderless"


# Custom class to store sub sub sections of fields - most important for branching logic
class Subsection:
    def __init__(self,
                 fields: list[Field],
                 style: SubsectionStyle,
                 special_heading: bool = False,
                 ):
        self.fields = fields  # Holds all fields in subsection
        self.style = style  # Holds style of subsection
        self.special_heading = special_heading  # Holds if 'special heading' should be there (subsection should have "If ___:")
        self.subsubsections: List[
            Subsubsection] = []  # Hold the subsubsections (only more than 1 when Branching Logic requires it)

    # Function to divide fields into rows that make sense  
    def _get_conditional_text(self, dependencies: List[Dependency], locate_phrase):
        if not dependencies: return f"NONE_1"
        if_text = locate_phrase('if')['text']

        conditions = []

        for dependency in dependencies:

            # Find the parent question in previous fields
            parent_question = next((f for f in self.fields if f.name == dependency.field_name), None)

            if not parent_question: continue

            if (type(parent_question.data[0]['Choices, Calculations, OR Slider Labels']) != str):
                return f"" + if_text + " " + parent_question.data[0]['Field Label'] + ":"

            options = parent_question.data[0]['Choices, Calculations, OR Slider Labels'].split("|")

            condition = None

            for i, option in enumerate(options):
                options[i] = option.split(',')
                for j, part in enumerate(options[i]):
                    options[i][j] = part.strip()
                    if options[i][0] == dependency.value:
                        condition = options[i][1]

            if condition: conditions.append(condition)

        if len(conditions) == 0:
            if parent_question: return f"" + if_text + " " + parent_question.data[0]['Field Label'] + ":"

        if len(conditions) == 1: return f"" + if_text + " " + conditions[0] + ":"

        if len(conditions) > 1:

            total_condition = if_text + " "
            conditions_added = []
            for condition in conditions:
                if 'yes' in condition.lower():
                    condition = 'Yes'

                if condition not in conditions_added:
                    total_condition += condition + ', '
                    conditions_added.append(condition)

            total_condition = total_condition[:-2]
            total_condition += ":"

            return total_condition

        return f"NONE_2"

    def divide_into_subsubsections(self, should_divide: bool, locate_phrase) -> List[Subsubsection]:
        if_completeForm_text = locate_phrase('if_completeForm')['text']

        # For only a couple forms with one specific question that leads to "If Yes, complete the form:"
        if self.special_heading:
            text_field = Field(name=self.fields[0].name + 'subsubheader',
                               is_text=True, data=[self.fields[0]],
                               question=Paragraph(text=if_completeForm_text + ':'), answer=[Paragraph(text='')]
                               )
            return ([Subsubsection(fields=[], header=[self.fields[0], text_field])])

        ### If not dividing into subsubsections:
        if not should_divide:
            return ([Subsubsection(fields=self.fields)])

        ''' Step 1: Split fields into subsubsections based on dependencies '''

        ### Define variables ###
        def initial_division(self) -> List[Subsubsection]:
            subsubsections: List[Subsubsection] = []
            current_subsub: Subsubsection = Subsubsection(fields=[])
            subsub_dependencies: List[Dependency] = []

            ### Iterate through self.fields ###
            for i, field in enumerate(self.fields):
                # add field dependencies to total subsection dependencies
                subsub_dependencies += field.dependencies

                # find the current dependencies
                dependency_names = []
                for dependency in field.dependencies:
                    dependency_names.append(dependency.field_name)

                # find next dependencies
                next_dependencies = []
                if i + 1 < len(self.fields):
                    for dependency in self.fields[i + 1].dependencies:
                        next_dependencies.append(dependency.field_name)

                # check_for_special_dependency(current_subsub, dependency_names)

                # if the parent of next field, make a new subsubsection
                if field.name in next_dependencies:
                    # check_for_oneline_dependent()
                    subsubsections.append(current_subsub)  # finish current one
                    '''A subsubsection header is a pair of question paired with an If: ___'''
                    subsub_dependencies = []  # reset dependencies
                    text_field = Field(name=field.name + 'subsubheader',  # add new subsubsection first item
                                       is_text=True, data=[field],
                                       question=Paragraph(text=''), answer=[Paragraph(text='')]
                                       )
                    current_subsub = Subsubsection(parent=field.name, header=[field, text_field], fields=[])
                    continue

                # if parent in field's dependencies, add it to that subsubsection
                if current_subsub.parent in dependency_names:
                    conditional_text = self._get_conditional_text(subsub_dependencies, locate_phrase)
                    current_subsub.header[1].question = Paragraph(text=conditional_text, style=style.conditional_text)
                    current_subsub.fields.append(field)
                    continue

                # if parent is there (but implicitly not correct), finish last subsub and begin a new one (that isn't a parented subsub)
                if current_subsub.parent:
                    # check_for_oneline_dependent()
                    subsubsections.append(current_subsub)
                    subsub_dependencies = []
                    current_subsub = Subsubsection(fields=[field])
                    continue

                # otherwise, finish last subsubsection and make a new one for this field
                else:
                    current_subsub.fields.append(field)
            # if unadded subsubsection, add it
            if current_subsub.fields: subsubsections.append(current_subsub)

            return subsubsections

        initial_subsections = initial_division(self)

        ''' Step 2: Style subsubsections if a oneline dependent '''

        def handle_conditional_subsubsections(self, initial_subsections: List[Subsubsection]) -> List[Subsubsection]:
            # Create list of subsubsections to be added
            final_subsubsections: List[Subsubsection] = []
            # Iterate through current subsubsections
            for subsub in initial_subsections:

                # if there is no header, skip logic and just add it.
                if not subsub.header:
                    final_subsubsections.append(subsub)
                    continue

                # Get subsubsection dependencies 
                # add if not currently in dependencies array
                dependencies = []
                dependency_texts = []
                for field in subsub.fields:
                    if field.dependencies:
                        for dependency in field.dependencies:
                            dependency_text = self._get_conditional_text(field.dependencies, locate_phrase)
                            if dependency_text not in dependency_texts:
                                dependency_texts.append(dependency_text)
                                dependencies.append(dependency)

                # if not the same length, just add it.
                if ((len(subsub.fields) != len(dependencies)) | (len(subsub.fields) == 0)):
                    final_subsubsections.append(subsub)
                    continue

                question_text = subsub.header[1].question.text + ' ' + subsub.fields[0].question.text
                if len(subsub.fields) == 1:
                    new_subsub: Subsubsection = Subsubsection(fields=[subsub.header[0]], is_conditional=True)
                else:
                    emptyField = Field(
                        name='empty',
                        dependencies=subsub.header[0].dependencies,
                        data=subsub.header[0].data,
                        is_text=True,
                        question=Paragraph(text="", style=field.question.style),
                        is_heading=False,
                        answer=[]
                    )
                    new_subsub: Subsubsection = Subsubsection(fields=[], header=[subsub.header[0], emptyField],
                                                              is_conditional=True)

                for field in subsub.fields:
                    question_text = self._get_conditional_text(field.dependencies,
                                                               locate_phrase) + " " + field.question.text
                    new_field = Field(
                        name=field.name,
                        dependencies=field.dependencies,
                        data=field.data,
                        is_text=field.is_text,
                        question=Paragraph(text=question_text, style=field.question.style),
                        is_heading=field.is_heading,
                        answer=field.answer
                    )

                    # new_field.question.text = question_text
                    new_subsub.fields.append(new_field)

                final_subsubsections.append(new_subsub)
                continue

            return final_subsubsections

        final_subsubsections = handle_conditional_subsubsections(self, initial_subsections)

        ### Save and return result ###
        self.subsubsections = final_subsubsections
        return final_subsubsections


# Define an Enum for subsection types
class SectionType(Enum):
    STANDARD = "standard"
    MEDICATION = "medication"
    TESTING = "testing"


# Custom class section
class Section:
    def __init__(self,
                 fields: list[Field],
                 type: SectionType = SectionType.STANDARD
                 ):
        self.fields = fields
        self.type = type
        self.subsections: List[Subsection] = []

    def divide_by_branchingLogic(self):
        """Divides self.fields into subsections based on headings and dependencies."""

        ### Define variables ###
        subsections: List[Subsection] = []
        subsection_fields: List[Field] = []
        subsection_dependencies_set = set()
        subsection_names_set = set()
        special_form: bool = False
        special_heading: str = None

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

        def finalize_subsection(style, special_header: bool = False):
            """Finalize the current subsection and reset tracking variables."""
            nonlocal subsection_fields, subsection_dependencies_set, subsection_names_set
            if subsection_fields:
                # if len(subsection_fields) <= 10:
                #    subsections.append(Subsection(subsection_fields, style=SubsectionStyle.QA_BOARDERLESS))
                # else:
                #    subsections.append(Subsection(subsection_fields, style=style))
                if special_header:
                    subsections.append(Subsection(subsection_fields, style=style, special_heading=True))
                else:
                    subsections.append(Subsection(subsection_fields, style=style))
            subsection_fields = []
            subsection_dependencies_set = set()
            subsection_names_set = set()

        ### Iterate through self.fields ###
        for i, field in enumerate(self.fields):

            # Handle headings
            if field.is_heading:

                if subsection_fields:
                    if subsection_dependencies_set == set():
                        finalize_subsection(SubsectionStyle.QA_BLACK)
                    else:
                        finalize_subsection(SubsectionStyle.QA_BOARDERLESS)

                subsections.append(Subsection([field], SubsectionStyle.HEADING))
                continue

            # Handle Custom Forms
            special_form_prefixes = ["vital_", "sympt_", "lesion_", "treat_", "critd_", "labs_", "imagi_", "test_"]
            special_form = bool(field.name.startswith(tuple(special_form_prefixes)))
            if ((i == 1) and (special_form == True)):
                special_heading = field.name

            # Handle Special Forms
            special_form_prefixes = ["vital_", "sympt_", "lesion_", "treat_", "critd_", "labs_", "imagi_", "test_"]
            special_form = bool(field.name.startswith(tuple(special_form_prefixes)))
            if ((i == 1) and (special_form == True)):
                special_heading = field.name

            ### Get dependencies from branching_logic ###
            branching_logic: str = (
                field.data[0].get('Branching Logic (Show field only if...)')
                if isinstance(field.data[0].get('Branching Logic (Show field only if...)'), str)
                else None
            )
            dependencies = extract_dependencies(branching_logic)

            # Get next field's dependencies
            next_logic: str = (
                self.fields[i + 1].data[0].get('Branching Logic (Show field only if...)')
                if (i + 1 < len(self.fields) and isinstance(
                    self.fields[i + 1].data[0].get('Branching Logic (Show field only if...)'), str))
                else None
            )
            next_dependencies = extract_dependencies(next_logic)
            subsection_started = len(subsection_fields) > 0

            dependencies.discard(special_heading)
            next_dependencies.discard(special_heading)

            ### Process subsection logic ###
            if subsection_started:
                # Default subsection (no dependencies)
                if not subsection_dependencies_set:
                    # print ('       NOT subsection_dependencies_set', dependencies, next_dependencies)
                    if not dependencies and not next_dependencies:
                        subsection_fields.append(field)
                        subsection_names_set.add(field.name)
                    elif subsection_names_set.isdisjoint(dependencies):
                        finalize_subsection(SubsectionStyle.QA_BLACK)
                        subsection_fields.append(field)
                        subsection_names_set.add(field.name)
                        subsection_dependencies_set.update(dependencies, next_dependencies)
                    else:

                        subsection_fields.append(field)
                        subsection_names_set.add(field.name)
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
                        finalize_subsection(SubsectionStyle.QA_GREY)

                    subsection_fields.append(field)
                    subsection_names_set.add(field.name)
                    subsection_dependencies_set.update(dependencies, next_dependencies)
            else:
                # Start a new subsection
                subsection_fields.append(field)
                subsection_names_set.add(field.name)
                subsection_dependencies_set.update(dependencies, next_dependencies)

            if field.name == special_heading:
                finalize_subsection(SubsectionStyle.QA_BOARDERLESS, True)

        ### Finalize the last subsection ###
        if subsection_fields:
            if subsection_dependencies_set == set():
                finalize_subsection(SubsectionStyle.QA_BLACK)
            else:
                finalize_subsection(SubsectionStyle.QA_BOARDERLESS)

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
            if field.is_heading:
                # if currently a subsection, finish it
                if subsection_fields:
                    finalize_subsection(SubsectionStyle.QA_BLACK)
                # then add heading subsection
                subsections.append(Subsection([field], SubsectionStyle.HEADING))
                continue

            ### Get field variables ###
            subsection_fields.append(field)

        ### Finalize the last subsection ###
        if subsection_fields:
            finalize_subsection(SubsectionStyle.QA_BLACK)

        ### Save and return result ###
        self.subsections = subsections
        return subsections

    def divide_into_subsections(self):
        return self.divide_by_branchingLogic()
