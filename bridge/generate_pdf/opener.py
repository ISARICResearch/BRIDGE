from copy import deepcopy
from os import getenv
from typing import Tuple

import numpy as np
import pandas as pd
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, PropertySet, StyleSheet1
from reportlab.lib.units import inch
from reportlab.platypus import Spacer
from reportlab.platypus import Table, TableStyle, Paragraph

REGISTERED_FONT = 'DejaVuSans'
REGISTERED_FONT_BOLD = 'DejaVuSans-Bold'

TEXT_FIELD = 'Text'
PAPER_LIKE_FIELD = 'Paper-like section'


class ElementList:

    def __init__(self,
                 df_details: pd.DataFrame,
                 db_name: str,
                 text_field: str,
                 paper_like_field: str,
                 sample_style_sheet: StyleSheet1,
                 normal_style: PropertySet,
                 center_style: PropertySet,
                 header_style: PropertySet,
                 title_style: PropertySet):
        self.df_details = df_details
        self.db_name = db_name
        self.text_field = text_field
        self.paper_like_field = paper_like_field
        self.sample_style_sheet = sample_style_sheet
        self.normal_style = normal_style
        self.center_style = center_style
        self.header_style = header_style
        self.title_style = title_style

        self.df_details[TEXT_FIELD] = df_details[TEXT_FIELD].replace(np.nan, '')

    def add_title_design_and_description(self, element_list: list) -> list:
        title_text = self.df_details[self.df_details[PAPER_LIKE_FIELD] == 'Title'][self.text_field].values[0]
        title_text = title_text.replace('CORE', self.db_name).upper()
        element_list.append(Paragraph(title_text, self.title_style))
        element_list.append(Paragraph("<br/><br/>"))
        return element_list

    def add_design_description(self, element_list: list) -> list:
        match_text = 'DESIGN OF THIS CASE REPORT FORM (CRF)'
        design_text = self.df_details.loc[ \
            self.df_details[PAPER_LIKE_FIELD] == match_text, self.text_field].values[0].replace('[PROJECT_NAME]',
                                                                                                self.db_name)
        section_name = \
            self.df_details.loc[self.df_details[PAPER_LIKE_FIELD] == match_text, self.paper_like_field].values[0]
        element_list.append(Paragraph(section_name, self.header_style))
        element_list.append(Paragraph(design_text, self.normal_style))
        element_list.append(Paragraph("<br/><br/>"))
        return element_list

    def add_presentation_paragraphs(self, element_list: list) -> list:
        # Filtering out rows that are not related to form details
        df_form_details = self.df_details[
            ~self.df_details[TEXT_FIELD].str.startswith("Timing /Events:") &
            self.df_details[PAPER_LIKE_FIELD].isin(['PRESENTATION FORM', 'DAILY FORM', 'OUTCOME FORM','PREGNANCY FORM','NEONATE FORM'])].copy()

        # Build the paragraphs with the desired format
        form_names_added = set()
        presentation_paragraphs = []

        for _, row in df_form_details.iterrows():
            form_name = row[self.paper_like_field]
            text = row[self.text_field]

            # Check if the form name has been added before
            if form_name not in form_names_added:
                presentation_paragraphs.append(f'<b>{form_name}:</b> {text}')
                form_names_added.add(form_name)
            else:
                presentation_paragraphs.append(f'{form_name}: {text}')

        # Joining the constructed paragraphs with line breaks and add to the elements list
        element_list.append(Paragraph('<br/>'.join(presentation_paragraphs), self.normal_style))
        return element_list

    def add_follow_up_details(self, element_list: list) -> list:
        # Filtering out rows that are not related to form details
        follow_up_text = \
            self.df_details.loc[self.df_details[PAPER_LIKE_FIELD] == 'Follow-up details', self.text_field].iloc[0]
        element_list.append(Paragraph(follow_up_text, self.normal_style))
        element_list.append(Paragraph("<br/>"))
        element_list.append(Spacer(1, 10))
        return element_list

    def get_timing_events_dataframe(self) -> pd.DataFrame:
        df_details_event = self.df_details[(self.df_details[TEXT_FIELD].str.startswith('Timing /Events:')) | (
                self.df_details[PAPER_LIKE_FIELD] == 'Timing /Events')].copy()

        event_columns = ['Forms'] + self.df_details[self.text_field].loc[
            self.df_details[PAPER_LIKE_FIELD] == 'Timing /Events'].iloc[0].split(' | ')
        df_transformed = pd.DataFrame(columns=event_columns)

        df_transformed['Forms'] = df_details_event[self.paper_like_field]

        for event_column in event_columns[1:]:
            if event_column in [event for event in event_columns if '(' in event]:
                df_transformed[event_column] = df_details_event[self.text_field].apply(
                    lambda x: '(COMPLETE)' if event_column in x else '')
            else:
                df_transformed[event_column] = df_details_event[self.text_field].apply(
                    lambda x: 'COMPLETE' if event_column in x else '')

        timing_text = \
            self.df_details.loc[self.df_details[PAPER_LIKE_FIELD] == 'Timing /Events', self.paper_like_field].iloc[0]
        df_transformed = df_transformed.loc[df_transformed['Forms'] != timing_text]
        return df_transformed

    def add_table_data(self,
                       df_transformed: pd.DataFrame,
                       element_list: list) -> list:
        # Convert DataFrame data into a list of lists with Paragraphs for wrapping
        table_data_list = [[Paragraph(str(item), self.center_style) for item in row] for row in
                           df_transformed.values.tolist()]
        header_list = [Paragraph(str(header), self.center_style) for header in df_transformed.columns.tolist()]
        table_data_list.insert(0, header_list)

        # Calculate the available width for the table
        page_width = 8.5 * inch
        margin_width = .4 * inch  # Assuming a 1-inch margin on both sides
        table_width = page_width - 2 * margin_width  # subtracting both left and right margins
        num_columns = len(df_transformed.columns)
        col_width = table_width / num_columns

        table = Table(table_data_list, colWidths=[col_width for _ in range(num_columns)])

        style = TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.hsl2rgb(0, 0, .7)),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('FONTNAME', (0, 0), (-1, 0), REGISTERED_FONT),
            ('FONTSIZE', (0, 0), (-1, -1), 8),  # Adjust the font size for all cells here
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ])

        table.setStyle(style)

        element_list.append(table)
        element_list.append(Spacer(1, 30))
        return element_list

    def add_general_guidance(self,
                             element_list: list) -> list:
        guidance_text = \
            self.df_details.loc[self.df_details[PAPER_LIKE_FIELD] == 'GENERAL GUIDANCE', self.paper_like_field].values[
                0]
        element_list.append(Paragraph(guidance_text, self.header_style))
        element_list.append(Spacer(1, 12))

        for entry in self.df_details.loc[
            self.df_details[PAPER_LIKE_FIELD] == 'GENERAL GUIDANCE', self.text_field].values:
            bullet_point = Paragraph(
                "• " + entry.replace('circles ()', 'circles (○)').replace('square boxes ()', 'square boxes (□)'),
                self.sample_style_sheet['Normal'])
            element_list.append(bullet_point)

        return element_list


def get_text_variables_for_env() -> Tuple[str, str]:
    if getenv('ENV') == 'development':
        text_field = TEXT_FIELD
        paper_like_field = PAPER_LIKE_FIELD
    else:
        # Only required in some places. Otherwise, use global variables
        text_field = 'Text_translation'
        paper_like_field = 'Paper-like section_translation'
    return (text_field,
            paper_like_field)


def set_styles() -> Tuple[StyleSheet1, PropertySet, PropertySet, PropertySet, PropertySet]:
    sample_styles_sheet = getSampleStyleSheet()

    normal_style = sample_styles_sheet['Normal']
    normal_style.fontSize = 8
    normal_style.leading = 10
    normal_style.fontName = REGISTERED_FONT

    center_style = deepcopy(sample_styles_sheet['Normal'])
    center_style.fontSize = 8
    center_style.leading = 10
    center_style.fontName = REGISTERED_FONT
    center_style.alignment = 1  # Center alignment

    header_style = sample_styles_sheet['Heading1']
    header_style.fontSize = 12
    header_style.leading = 14
    header_style.fontName = REGISTERED_FONT_BOLD

    title_style = sample_styles_sheet['Title']
    title_style.fontSize = 16
    title_style.leading = 20
    title_style.fontName = REGISTERED_FONT_BOLD

    return (sample_styles_sheet,
            normal_style,
            center_style,
            header_style,
            title_style)


def generate_opener(element_list: list,
                    df_details: pd.DataFrame,
                    db_name: str) -> list:
    (text_field,
     paper_like_field) = get_text_variables_for_env()

    (sample_style_sheet,
     normal_style,
     center_style,
     header_style,
     title_style) = set_styles()

    element_instance = ElementList(df_details,
                                   db_name,
                                   text_field,
                                   paper_like_field,
                                   sample_style_sheet,
                                   normal_style,
                                   center_style,
                                   header_style,
                                   title_style)

    element_list = element_instance.add_title_design_and_description(element_list)
    element_list = element_instance.add_design_description(element_list)
    element_list = element_instance.add_presentation_paragraphs(element_list)
    element_list = element_instance.add_follow_up_details(element_list)

    df_transformed = element_instance.get_timing_events_dataframe()
    element_list = element_instance.add_table_data(df_transformed,
                                                   element_list)

    element_list = element_instance.add_general_guidance(element_list)

    return element_list
