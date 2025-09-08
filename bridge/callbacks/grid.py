import io

import pandas as pd
from dash import Input, Output, State

from bridge.arc import arc
from bridge.generate_pdf import form


class Grid:

    @staticmethod
    def register_callbacks(app):

        @app.callback(
            [
                Output('CRF_representation_grid', 'columnDefs'),
                Output('CRF_representation_grid', 'rowData'),
                Output('selected_data-store', 'data')
            ],
            Input('input', 'checked'),
            State('current_datadicc-store', 'data'),
            prevent_initial_call=True)
        def display_checked(checked, current_datadicc_saved):
            current_datadicc = pd.read_json(io.StringIO(current_datadicc_saved), orient='split')

            column_defs = [{'headerName': "Question", 'field': "Question", 'wrapText': True},
                           {'headerName': "Answer Options", 'field': "Answer Options", 'wrapText': True}]

            row_data = [{'question': "", 'options': ""},
                        {'question': "", 'options': ""}]

            selected_variables = pd.DataFrame()
            if checked and len(checked) > 0:
                # global selected_variables
                selected_dependency_lists = current_datadicc['Dependencies'].loc[
                    current_datadicc['Variable'].isin(checked)].tolist()
                flat_selected_dependency = set()
                for sublist in selected_dependency_lists:
                    flat_selected_dependency.update(sublist)
                all_selected = set(checked).union(flat_selected_dependency)
                selected_variables = current_datadicc.loc[current_datadicc['Variable'].isin(all_selected)]

                #############################################################
                #############################################################
                ## REDCAP Pipeline
                selected_variables = arc.get_include_not_show(selected_variables['Variable'], current_datadicc)

                # Select Units Transformation
                arc_var_units_selected, delete_this_variables_with_units = arc.get_select_units(
                    selected_variables['Variable'],
                    current_datadicc)
                if arc_var_units_selected is not None:
                    selected_variables = arc.add_transformed_rows(selected_variables, arc_var_units_selected,
                                                                  arc.get_variable_order(current_datadicc))
                    if len(delete_this_variables_with_units) > 0:  # This remove all the unit variables that were included in a select unit type question
                        selected_variables = selected_variables.loc[
                            ~selected_variables['Variable'].isin(delete_this_variables_with_units)]

                selected_variables = arc.generate_daily_data_type(selected_variables)

                #############################################################
                #############################################################

                last_form, last_section = None, None
                new_rows = []
                selected_variables = selected_variables.fillna('')
                for index, row in selected_variables.iterrows():
                    # Add form separator
                    if row['Form'] != last_form:
                        new_rows.append(
                            {'Question': f"{row['Form'].upper()}", 'Answer Options': '', 'IsSeparator': True,
                             'SeparatorType': 'form'})
                        last_form = row['Form']

                    # Add section separator
                    if row['Section'] != last_section and row['Section'] != '':
                        new_rows.append(
                            {'Question': f"{row['Section'].upper()}", 'Answer Options': '', 'IsSeparator': True,
                             'SeparatorType': 'section'})
                        last_section = row['Section']

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

                # Update selected_variables with new rows including separators
                selected_variables_for_table_visualization = pd.DataFrame(new_rows)
                selected_variables_for_table_visualization = selected_variables_for_table_visualization.loc[
                    selected_variables_for_table_visualization['Type'] != 'group']
                # Convert to dictionary for row_data
                row_data = selected_variables_for_table_visualization.to_dict(orient='records')

                column_defs = [{'headerName': "Question", 'field': "Question", 'wrapText': True},
                               {'headerName': "Answer Options", 'field': "Answer Options", 'wrapText': True}]

            return column_defs, row_data, selected_variables.to_json(date_format='iso', orient='split')

        return app
