import io
from typing import Tuple

import dash
import pandas as pd
from dash import Input, Output, State

from bridge.arc import arc_core
from bridge.generate_pdf import form


@dash.callback(
    [
        Output('CRF_representation_grid', 'rowData', allow_duplicate=True),
        Output('selected_data-store', 'data'),
        Output('focused-cell-run-callback', 'data', allow_duplicate=True),
        Output('focused-cell-index', 'data'),
    ],
    [
        Input('input', 'checked'),
    ],
    [
        State('current_datadicc-store', 'data'),
        State('focused-cell-index', 'data'),
    ],
    prevent_initial_call=True)
def display_checked_in_grid(checked: list,
                            current_datadicc_saved: str,
                            focused_cell_index: int) -> Tuple[list, str, bool, int]:
    df_current_datadicc = pd.read_json(io.StringIO(current_datadicc_saved), orient='split')

    row_data = []

    df_selected_variables = pd.DataFrame()
    if checked:
        selected_dependency_lists = df_current_datadicc['Dependencies'].loc[
            df_current_datadicc['Variable'].isin(checked)].tolist()
        flat_selected_dependency = set()
        for sublist in selected_dependency_lists:
            flat_selected_dependency.update(sublist)
        all_selected = set(checked).union(flat_selected_dependency)
        df_selected_variables = df_current_datadicc.loc[df_current_datadicc['Variable'].isin(all_selected)]

        ## REDCAP Pipeline
        df_selected_variables = arc_core.get_include_not_show(df_selected_variables['Variable'], df_current_datadicc)

        # Select Units Transformation
        (arc_var_units_selected,
         delete_this_variables_with_units) = arc_core.get_select_units(df_selected_variables['Variable'],
                                                                       df_current_datadicc)
        if arc_var_units_selected is not None:
            df_selected_variables = arc_core.add_transformed_rows(df_selected_variables, arc_var_units_selected,
                                                                  arc_core.get_variable_order(df_current_datadicc))
            if len(delete_this_variables_with_units) > 0:
                # This remove all the unit variables that were included in a select unit type question
                df_selected_variables = df_selected_variables.loc[
                    ~df_selected_variables['Variable'].isin(delete_this_variables_with_units)]

        last_form, last_section = None, None
        new_rows = []
        df_selected_variables = df_selected_variables.fillna('')
        for index, row in df_selected_variables.iterrows():
            # Add form separator
            if row['Form'] != last_form:
                new_rows.append(
                    {'Question': f"{row['Form'].upper()}", 'Answer Options': '', 'IsSeparator': True,
                     'SeparatorType': 'form'})
                last_form = str(row['Form'])

            # Add section separator
            if row['Section'] != last_section and row['Section'] != '':
                new_rows.append(
                    {'Question': f"{row['Section'].upper()}", 'Answer Options': '', 'IsSeparator': True,
                     'SeparatorType': 'section'})
                last_section = str(row['Section'])

            if row['Type'] == 'descriptive':
                new_row = row.to_dict()
                new_row['IsDescriptive'] = True

                new_row['Answer Options'] = ''
                new_row['IsSeparator'] = False
                new_rows.append(new_row)
                continue

                # Process the actual row
            if row['Type'] in ['radio', 'dropdown', 'checkbox', 'list', 'user_list', 'multi_list']:
                formatted_choices = form.format_choices(row['Answer Options'], row['Type'])
                row['Answer Options'] = formatted_choices

            elif row['Validation'] == 'date_dmy':
                date_str = "[_D_][_D_]/[_M_][_M_]/[_2_][_0_][_Y_][_Y_]"
                row['Answer Options'] = date_str

            else:
                row['Answer Options'] = form.LINE_PLACEHOLDER

            # Add the processed row to new_rows
            new_row = row.to_dict()
            new_row['IsSeparator'] = False
            new_rows.append(new_row)

        # Update selected variables with new rows including separators
        selected_variables_for_table_visualization = pd.DataFrame(new_rows)
        selected_variables_for_table_visualization = selected_variables_for_table_visualization.loc[
            selected_variables_for_table_visualization['Type'] != 'group']
        # Convert to dictionary for row_data
        row_data = selected_variables_for_table_visualization.to_dict(orient='records')

    focused_cell_index = get_focused_cell_index(row_data,
                                                focused_cell_index,
                                                checked)

    focused_cell_run_callback = False
    if type(focused_cell_index) is int:
        focused_cell_run_callback = True

    return (row_data,
            df_selected_variables.to_json(date_format='iso', orient='split'),
            focused_cell_run_callback,
            focused_cell_index)


def get_focused_cell_index(row_data: list,
                           focused_cell_index: int,
                           checked: list) -> int:
    if checked:
        df_row_data = pd.DataFrame(row_data)
        df_row_data['Question'] = df_row_data['Question'].str.split(':').str[0]

        latest_checked_variable = checked[-1]
        while (latest_checked_variable.isupper()
               or latest_checked_variable not in df_row_data['Variable'].values):
            # Exclude headers and fields not in data (e.g. units)
            checked.pop()
            latest_checked_variable = checked[-1]

        df_row_data_variable = df_row_data[df_row_data['Variable'] == latest_checked_variable]
        section_name = df_row_data_variable['Section'].values[0]
        df_row_data_section = df_row_data[df_row_data['Section'] == section_name]

        df_row_data_section = df_row_data_section[~df_row_data_section['Variable'].str.contains('_otherl')]

        uppercase_variable_list = []
        for item in checked:
            if item.isupper():
                uppercase_variable_list.append(item)

        type_list = df_row_data_section['Type'].values
        latest_type = type_list[-1]
        list_types = [variable_type for variable_type in type_list if variable_type in ['multi_list', 'user_list']]
        if latest_type not in ['multi_list', 'user_list']:
            # Not a list => pick latest variable
            focused_cell_index = df_row_data_section.index.tolist()[-1]

        elif len(list_types) > 1 or latest_type in ['multi_list', 'user_list']:
            # Multiple lists checked => pick latest list
            df_lists = df_row_data_section[df_row_data_section['Type'].isin(list_types)]
            focused_cell_index = df_lists.index.tolist()[-1]

        elif len(df_row_data_section) == 1:
            # Section checked, then a variable in a different section => highlight the variable
            focused_cell_index = df_row_data_variable.index.tolist()[0]

        elif uppercase_variable_list:
            # One or more section headers have been checked
            if 'ARC' in uppercase_variable_list:
                # Everything checked => pick first
                uppercase_variable_list.remove('ARC')
                section_header = uppercase_variable_list[0]
                section_question_list = [question for question in df_row_data['Question'].values if
                                         question.isupper()]
                if section_header not in section_question_list:
                    # Subsection, then all
                    section_header = uppercase_variable_list[1]

            else:
                first_header = uppercase_variable_list[0]
                section_list = [item for item in uppercase_variable_list if '-' not in item]

                if all([item.startswith(first_header) for item in uppercase_variable_list]) and section_list:
                    # All sections checked => pick first
                    section_header = first_header

                elif section_list:
                    # No subsections checked => pick last selected section
                    section_header = section_list[-1]

                else:
                    # Multiple subsections checked => pick last one
                    section_subsection_list = [item for item in uppercase_variable_list if '-' in item]
                    subsection_list = []

                    for item in section_subsection_list:
                        subsection_list = subsection_list + item.split('-')
                    section_header = subsection_list[-1]

                    section_question_list = [question for question in df_row_data['Question'].values if
                                             question.isupper()]
                    if section_header not in section_question_list:
                        # Subsection contains a "-"
                        section_header = '-'.join([subsection_list[-2], subsection_list[-1]])

            df_row_data_section_start = df_row_data[df_row_data['Question'] == section_header]
            focused_cell_index = df_row_data_section_start.index.tolist()[0]

        else:
            # Single variable ticked
            # Group checked => pick last item in group
            focused_cell_index = df_row_data_variable.index.tolist()[0]

    return focused_cell_index
