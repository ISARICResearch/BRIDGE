import re
from typing import List, Callable

import pandas as pd
from reportlab.platypus import Paragraph, PageBreak, Spacer

from bridge.generate_pdf import styles
from bridge.generate_pdf.form_classes import (
    Field,
    SectionType,
    Section,
    Dependency,
    SubsectionStyle,
)
from bridge.generate_pdf.form_construct import (
    construct_medication_form,
    construct_standard_row,
    construct_testing_form,
)

"""
How generate_form() works:

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

"""


class Form:
    def __init__(self):
        self.line_placeholder = "_" * 40

    def format_choices(
        self,
        choices_str: str,
        field_type: str,
        threshold: int = 65,
        is_units: bool = False,
    ) -> str | None:
        """
        Format the choices string. If the combined length exceeds the threshold, use line breaks instead of commas.
        Prepend symbols based on the field type.
        """
        if not isinstance(choices_str, str):
            return None

        if field_type == "radio":
            symbol = "○ "
        elif field_type == "list":
            symbol = "○ "
        elif field_type == "user_list":
            symbol = "○ "
        elif field_type == "multi_list":
            symbol = "□ "
        elif field_type == "checkbox":
            symbol = "□ "
        elif field_type == "dropdown":
            symbol = "↧ "
        else:
            symbol = ""

        if is_units:
            symbol = symbol.strip(" ")

        choices = ""
        if len(choices_str.split("|")) <= 15:
            choices = [
                symbol + choice.split(",", 1)[-1].strip().replace("Â", "")
                for choice in choices_str.split("|")
            ]
            combined_choices = "   ".join(choices).strip()
        else:
            combined_choices = self.line_placeholder
        if len(combined_choices) > threshold:
            combined_choices = "\n".join(choices).strip()
        return combined_choices

    @staticmethod
    def _parse_branching_logic(logic_str: str) -> List[Dependency]:
        dependency_list = []

        # Split on boolean operators while keeping the operators
        tokens = re.split(r"\s+(and|or)\s+", logic_str, flags=re.IGNORECASE)

        for token in tokens:
            if token.lower() in ["and", "or"]:
                continue
            # Match patterns like [field]='1' or [field] < 5
            match = re.match(r'\[(\w+)\] ?([!=<>]+) ?[\'"]?(\w+)[\'"]?', token)

            if match:
                field, operator, value = match.groups()
                dependency_list.append(Dependency(field, operator, value))
        return dependency_list

    def _format_multi_choice_field(
        self, row: pd.Series, new_field: Field
    ) -> Field | None:
        symbol = {
            "radio": "○ ",
            "checkbox": "□ ",
            "dropdown": "○ ",  # '↧ ',
            "list": "○ ",
            "user_list": "○ ",
            "multi_list": "□ ",
        }.get(row["Field Type"], "")

        if not isinstance(row["Choices, Calculations, OR Slider Labels"], str):
            return None

        choices = []
        if new_field.name == "test_biospecimentype":
            """This is a wierd line of code to check when editing variables related to the PATHOGEN TESTING form.
            Specifically 'test_biospecimentype'
            This just only pulls the answers presented to me to add to the form"""
            for choice in row["Choices, Calculations, OR Slider Labels"].split("|"):
                choices.append(symbol + choice.split(",", 1)[-1].strip())
        else:
            choices = [
                symbol + choice.split(",", 1)[-1].strip()
                for choice in row["Choices, Calculations, OR Slider Labels"].split("|")
            ]

        if len(choices) < 23:
            new_field.answer = [Paragraph(choice, styles.normal) for choice in choices]
        else:
            new_field.answer = [Paragraph(self.line_placeholder, styles.normal)]
        return new_field

    def _format_text_field(self, row: pd.Series, new_field: Field) -> Field:
        validation = row["Text Validation Type OR Show Slider Number"]

        if validation == "date_dmy":
            # Add a date placeholder
            date_str = """[<font color="lightgrey">_D_</font>][<font color="lightgrey">_D_</font>]/[<font color="lightgrey">_M_</font>][<font color="lightgrey">_M_</font>]/[<font color="lightgrey">_Y_</font>][<font color="lightgrey">_Y_</font>][<font color="lightgrey">_Y_</font>][<font color="lightgrey">_Y_</font>]"""
            new_field.answer = [Paragraph(date_str, styles.normal)]

        elif validation == "time":
            # Add a time placeholder
            time_str = "_" * 18
            new_field.answer = [Paragraph(time_str, styles.normal)]

        elif validation == "number":
            number_str = "_" * 18
            new_field.answer = [Paragraph(number_str, styles.normal)]
        else:
            # Open-ended questions
            new_field.answer = [Paragraph(self.line_placeholder, styles.normal)]
        return new_field

    def _create_field(self, row: pd.Series) -> Field | None:
        variable_name = row["Variable / Field Name"]

        branching_logic = row["Branching Logic (Show field only if...)"]
        dependency_list = []

        if isinstance(branching_logic, str):
            dependency_list = self._parse_branching_logic(branching_logic)

        # Create a new field with question and placeholder answer
        new_field = Field(
            name=variable_name,
            dependencies=dependency_list,
            data=[row],
            question=Paragraph(row["Field Label"], styles.normal),
            answer=[],
        )

        # If country, make it a short line
        if variable_name == "demog_country":
            new_field.answer = [Paragraph("_" * 18, styles.normal)]
            return new_field

        if row["Field Type"] in [
            "radio",
            "dropdown",
            "checkbox",
            "list",
            "user_list",
            "multi_list",
        ]:
            new_field = self._format_multi_choice_field(row, new_field)
            return new_field

        elif row["Field Type"] == "text":
            new_field = self._format_text_field(row, new_field)
            return new_field

        return None

    def _add_field_to_section(
        self, row: pd.Series, section: List[Field]
    ) -> List[Field]:
        variable_name = row["Variable / Field Name"]

        if row["Field Type"] == "descriptive":
            new_field = Field(
                name=variable_name,
                dependencies=[],
                data=[row],
                question=Paragraph(row["Field Label"]),
                answer=[Paragraph("")],
                is_descriptive=True,
            )
            if isinstance(new_field, Field):
                section.append(new_field)
            return section

        ### ! Handle special cases (add to last question) ###

        if "demog_country_other" in variable_name:
            return section

        if variable_name.endswith(
            (
                "lesion_torsoo",
                "lesion_armso",
                "lesion_legso",
                "lesion_palmo",
                "lesion_soleo",
                "lesion_genito",
                "lesion_perio",
                "lesion_ocularo",
                "lesion_heado",
            )
        ):
            section[-1].answer.append(Paragraph("_" * 18, styles.normal))
            section[-1].data.append(row)

        # if other, oth, otherl3: add "Specify Other" to last field's answer
        elif variable_name.endswith(("_oth", "_otherl3")):
            section[-1].answer.append(Paragraph("_" * 18, styles.normal))
            section[-1].data.append(row)

        # if otherl2: ignore (Because these are long lists)
        elif variable_name.endswith("_otherl2"):
            return section

        # if units, add units to last field's answer
        elif variable_name.endswith("_units"):
            formatted_choices = self.format_choices(
                row["Choices, Calculations, OR Slider Labels"],
                row["Field Type"],
                200,
                True,
            )

            if isinstance(formatted_choices, str):
                section[-1].answer.append(Paragraph(formatted_choices, styles.normal))
            else:
                section[-1].answer.append(
                    Paragraph("Units:" + "_" * (18 - len("Units:")), styles.normal)
                )

            section[-1].data.append(row)

        ### ! If not a special case, add new field to section ###
        else:
            new_field = self._create_field(row)
            if isinstance(new_field, Field):
                section.append(new_field)

        return section

    def _get_sections(self, group: pd.Series) -> List[Section]:
        """Return section after appending new field to it, or modifying old one."""

        section_fields = []
        current_section_name = None

        for index, row in group.iterrows():
            if ">" in row["Field Label"][0:2]:
                continue
            if ("_unlisted_" in row["Variable / Field Name"]) and not (
                "_unlisted_0item" in row["Variable / Field Name"]
                or "_unlisted_type" in row["Variable / Field Name"]
            ):
                continue
            if row["Variable / Field Name"].endswith("addi"):
                continue
            # If row part of new section, add Section Header field
            if row["Section Header"] != current_section_name and pd.notna(
                row["Section Header"]
            ):
                section_fields.append([])
                current_section_name = row["Section Header"]
                current_section_index = len(section_fields) - 1
                section_fields[current_section_index].append(
                    Field(
                        name=row["Variable / Field Name"],
                        data=[row],
                        is_heading=True,
                        title=Paragraph(current_section_name, styles.section_header),
                    )
                )

            # If form_sections isn't yet started, add
            if len(section_fields) == 0:
                section_fields.append([])

            current_section_index = len(section_fields) - 1

            field_to_add = row
            if (
                "_unlisted_0item" in row["Variable / Field Name"]
                or "_unlisted_type" in row["Variable / Field Name"]
            ):
                field_to_add["Field Label"] = ""

            section_fields[current_section_index] = self._add_field_to_section(
                field_to_add, section_fields[current_section_index]
            )

        section_list = []
        for fields_list in section_fields:
            section_type = SectionType.STANDARD
            if fields_list[0].name.startswith("medi_"):
                section_type = SectionType.MEDICATION
            elif fields_list[0].name.startswith("test_"):
                section_type = SectionType.TESTING
            section_list.append(Section(fields=fields_list, section_type=section_type))

        return section_list

    def generate_form(
        self, df_datadicc: pd.DataFrame, element_list: list, locate_phrase: Callable
    ) -> List:
        """
        Generates the array of elements for a PDF of several forms from the data_dictionary
        Function returns array of sections. Each section is an array of Fields
        """

        for form_name in df_datadicc["Form Name"].drop_duplicates():
            group = df_datadicc[df_datadicc["Form Name"] == form_name]
            fixed_name = form_name.replace("_", " ").upper()

            # Add form name as a title for each table
            element_list.append(PageBreak())
            element_list.append(Paragraph(str(fixed_name), styles.form_header))

            # Form Sections are a way of splitting up the data into lists of Fields
            # where each field represents a heading or Question Answer pair.
            sections = self._get_sections(group)

            # For each section, divide into subsections
            for section in sections:
                if section.type == SectionType.MEDICATION:
                    medication_form = construct_medication_form(section.fields)
                    for table in medication_form:
                        element_list.append(table)

                elif section.type == SectionType.TESTING:
                    medication_form = construct_testing_form(
                        section.fields, locate_phrase
                    )
                    for table in medication_form:
                        element_list.append(table)

                else:
                    subsections = section.divide_into_subsections()
                    # For each subsection, divide into rows
                    for subsection in subsections:
                        subsubsections = subsection.divide_into_subsubsections(
                            bool(subsection.style != SubsectionStyle.QA_BLACK),
                            locate_phrase,
                        )

                        for subsub_index, subsubsection in enumerate(subsubsections):
                            rows = subsubsection.divide_into_rows()
                            if not rows:
                                continue

                            for row_index, row in enumerate(rows):
                                # For each row, setup to get columns and widths
                                # Then, style it and add it to elements
                                if row is None:
                                    continue

                                row.setup_row()

                                # Scale column widths to fit page width
                                row_table = construct_standard_row(
                                    row,
                                    row_index,
                                    len(rows),
                                    subsubsection,
                                    subsub_index,
                                    len(subsubsections),
                                    subsection.style,
                                )

                                element_list.append(row_table)

                # Add space between form sections
                element_list.append(Spacer(1, 12))

        return element_list
