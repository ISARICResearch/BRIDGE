import io
import json

import dash
import dash_bootstrap_components as dbc
import dash_treeview_antd
import pandas as pd
from dash import html, Input, Output, State

from bridge.arc import arc


class Modals:

    @staticmethod
    def variable_information_modal():
        return dbc.Modal(
            [
                dbc.ModalHeader(dbc.ModalTitle("Row Details", id='modal_title')),
                dbc.ModalBody(
                    [
                        html.H5("Definition:"),
                        html.P("Your definition text here", id='definition-text'),
                        html.H5("Options:"),
                        dbc.Checklist(
                            options=[
                                {"label": "Option 1", "value": 1},
                                {"label": "Option 2", "value": 2},
                            ],
                            id='options-checklist',
                            value=[1],
                        ),
                        dbc.ListGroup(
                            [
                                dbc.ListGroupItem("Item 1"),
                                dbc.ListGroupItem("Item 2"),
                            ],
                            id='options-list-group',
                            style={"display": "none"}
                        ),
                        html.Br(),
                        html.H5("Completion Guide:"),
                        html.P("Completion guide text here", id='completion-guide-text')
                    ]
                ),
                dbc.ModalFooter(
                    html.Div(
                        [dbc.Button("Submit", id='modal_submit', className="me-1", n_clicks=0),
                         dbc.Button("Cancel", id='modal_cancel', className="me-1", n_clicks=0)]
                    )
                ),
            ],
            id='modal',
            is_open=False,
            size="xl"
        )

    @staticmethod
    def register_callbacks(app):

        @app.callback(
            [
                Output('modal', 'is_open'),
                Output('modal_title', 'children'),
                Output('definition-text', 'children'),
                Output('completion-guide-text', 'children'),
                Output('options-checklist', 'style'),
                Output('options-list-group', 'style'),
                Output('options-checklist', 'options'),
                Output('options-checklist', 'value'),
                Output('options-list-group', 'children')
            ],
            Input('input', 'selected'),
            [
                State('ulist_variable_choices-store', 'data'),
                State('multilist_variable_choices-store', 'data'),
                State('modal', 'is_open'),
                State('current_datadicc-store', 'data'),
            ])
        def display_selected(selected, ulist_variable_choices_saved, multilist_variable_choices_saved, is_open,
                             current_datadicc_saved):
            dict_ulist = json.loads(ulist_variable_choices_saved)
            dict_multilist = json.loads(multilist_variable_choices_saved)
            dict_lists = dict_ulist + dict_multilist
            df_datadicc = pd.read_json(io.StringIO(current_datadicc_saved), orient='split')

            if selected:
                selected_variable = selected[0]
                if selected_variable in list(df_datadicc['Variable']):
                    question = df_datadicc['Question'].loc[df_datadicc['Variable'] == selected_variable].iloc[0]
                    definition = df_datadicc['Definition'].loc[df_datadicc['Variable'] == selected_variable].iloc[0]
                    completion = \
                        df_datadicc['Completion Guideline'].loc[df_datadicc['Variable'] == selected_variable].iloc[0]
                    ulist_variables = [i[0] for i in dict_lists]
                    if selected_variable in ulist_variables:
                        for item in dict_lists:
                            if item[0] == selected_variable:
                                options = []
                                checked_items = []
                                for i in item[1]:
                                    options.append({"number": int(i[0]), "label": str(i[0]) + ', ' + i[1],
                                                    "value": str(i[0]) + '_' + i[1]})
                                    if i[2] == 1:
                                        checked_items.append(str(i[0]) + '_' + i[1])

                        sorted_options = sorted(options, key=lambda x: x['number'])
                        for option in sorted_options:
                            del option['number']

                        return True, question + ' [' + selected_variable + ']', definition, completion, {
                            "maxHeight": "250px",
                            "overflowY": "auto"}, {
                            "display": "none"}, sorted_options, checked_items, []
                    else:
                        options = []
                        answ_options = \
                            df_datadicc['Answer Options'].loc[df_datadicc['Variable'] == selected_variable].iloc[0]
                        if isinstance(answ_options, str):
                            for i in answ_options.split('|'):
                                options.append(dbc.ListGroupItem(i))
                        else:
                            options = []
                        return True, question + ' [' + selected_variable + ']', definition, completion, {
                            "display": "none"}, {
                            "maxHeight": "250px", "overflowY": "auto"}, [], [], options

            return False, '', '', '', {"display": "none"}, {"display": "none"}, [], [], []

        @app.callback(
            [
                Output('modal', 'is_open', allow_duplicate=True),
                Output('current_datadicc-store', 'data'),
                Output('ulist_variable_choices-store', 'data'),
                Output('multilist_variable_choices-store', 'data'),
                Output('tree_items_container', 'children', allow_duplicate=True)
            ],
            [
                Input('modal_submit', 'n_clicks'),
                Input('modal_cancel', 'n_clicks'),
            ],
            [
                State('current_datadicc-store', 'data'),
                State('modal_title', 'children'),
                State('options-checklist', 'value'),
                State('input', 'checked'),
                State('ulist_variable_choices-store', 'data'),
                State('multilist_variable_choices-store', 'data'),
                State('selected-version-store', "data"),
                State('selected-language-store', "data"),
            ],
            prevent_initial_call=True
        )
        def on_modal_button_click(submit_n_clicks, cancel_n_clicks, current_datadicc_saved, modal_title,
                                  checked_options,
                                  checked, ulist_variable_choices_saved, multilist_variable_choices_saved,
                                  selected_version_data, selected_language_data):
            ctx = dash.callback_context

            if not ctx.triggered:
                return dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update

            df_current_datadicc = pd.read_json(io.StringIO(current_datadicc_saved), orient='split')
            button_id = ctx.triggered[0]['prop_id'].split('.')[0]

            if button_id == 'modal_submit':

                selected_version = selected_version_data.get('selected_version', None)
                selected_language = selected_language_data.get('selected_language', None)
                translations_for_language = arc.get_translations(selected_language)
                other_text = translations_for_language['other']

                variable_submitted = modal_title.split('[')[1][:-1]

                ulist_variable_choices_dict = json.loads(ulist_variable_choices_saved)
                multilist_variable_choices_dict = json.loads(multilist_variable_choices_saved)

                ulist_variables = [i[0] for i in json.loads(ulist_variable_choices_saved)]
                multilist_variables = [i[0] for i in json.loads(multilist_variable_choices_saved)]

                if (variable_submitted in ulist_variables) | (variable_submitted in multilist_variables):
                    list_options_checked = []
                    for lo in checked_options:
                        list_options_checked.append(lo.split('_'))

                    list_options_checked = pd.DataFrame(data=list_options_checked, columns=['cod', 'Option'])

                    new_submited_options = []
                    new_submited_line = []
                    position = 0
                    for var_select in ulist_variable_choices_dict:
                        if (var_select[0] == variable_submitted):
                            select_answer_options = ''
                            NOT_select_answer_options = ''
                            for option_var_select in (var_select[1]):
                                if (option_var_select[1] in (list(list_options_checked['Option']))):
                                    new_submited_options.append([option_var_select[0], option_var_select[1], 1])
                                    select_answer_options += str(option_var_select[0]) + ', ' + str(
                                        option_var_select[1]) + ' | '
                                else:
                                    new_submited_options.append([option_var_select[0], option_var_select[1], 0])
                                    NOT_select_answer_options += str(option_var_select[0]) + ', ' + str(
                                        option_var_select[1]) + ' | '
                            new_submited_line.append([var_select, new_submited_options])
                            ulist_variable_choices_dict[position][1] = new_submited_line[0][1]
                            df_current_datadicc.loc[df_current_datadicc[
                                                        'Variable'] == variable_submitted, 'Answer Options'] = select_answer_options + '88, ' + other_text
                            if variable_submitted + '_otherl2' in list(df_current_datadicc['Variable']):
                                df_current_datadicc.loc[df_current_datadicc[
                                                            'Variable'] == variable_submitted + '_otherl2', 'Answer Options'] = NOT_select_answer_options + '88, ' + other_text

                        position += 1
                    ulist_variable_choicesSubmit = ulist_variable_choices_dict

                    new_submited_options_multi_check = []
                    new_submited_line_multi_check = []
                    position_multi_check = 0
                    for var_select_multi_check in multilist_variable_choices_dict:
                        if (var_select_multi_check[0] == variable_submitted):
                            select_answer_options_multi_check = ''
                            NOT_select_answer_options_multi_check = ''
                            for option_var_select_multi_check in (var_select_multi_check[1]):
                                if (option_var_select_multi_check[1] in (list(list_options_checked['Option']))):
                                    new_submited_options_multi_check.append(
                                        [option_var_select_multi_check[0], option_var_select_multi_check[1], 1])
                                    select_answer_options_multi_check += str(
                                        option_var_select_multi_check[0]) + ', ' + str(
                                        option_var_select_multi_check[1]) + ' | '
                                else:
                                    new_submited_options_multi_check.append(
                                        [option_var_select_multi_check[0], option_var_select_multi_check[1], 0])
                                    NOT_select_answer_options_multi_check += str(
                                        option_var_select_multi_check[0]) + ', ' + str(
                                        option_var_select_multi_check[1]) + ' | '
                            new_submited_line_multi_check.append(
                                [var_select_multi_check, new_submited_options_multi_check])
                            multilist_variable_choices_dict[position_multi_check][1] = new_submited_line_multi_check[0][
                                1]
                            df_current_datadicc.loc[df_current_datadicc[
                                                        'Variable'] == variable_submitted, 'Answer Options'] = select_answer_options_multi_check + '88, ' + other_text
                            if variable_submitted + '_otherl2' in list(df_current_datadicc['Variable']):
                                df_current_datadicc.loc[df_current_datadicc[
                                                            'Variable'] == variable_submitted + '_otherl2', 'Answer Options'] = NOT_select_answer_options_multi_check + '88, ' + other_text
                        position_multi_check += 1
                    multilist_variable_choicesSubmit = multilist_variable_choices_dict

                    checked.append(variable_submitted)

                    tree_items_data = arc.get_tree_items(df_current_datadicc, selected_version)

                    tree_items = html.Div(
                        dash_treeview_antd.TreeView(
                            id='input',
                            multiple=False,
                            checkable=True,
                            checked=df_current_datadicc['Variable'].loc[df_current_datadicc['Variable'].isin(checked)],
                            expanded=df_current_datadicc['Variable'].loc[df_current_datadicc['Variable'].isin(checked)],
                            data=tree_items_data),
                        id='tree_items_container',
                        className='tree-item',
                    )
                    return False, df_current_datadicc.to_json(date_format='iso', orient='split'), json.dumps(
                        ulist_variable_choicesSubmit), json.dumps(multilist_variable_choicesSubmit), tree_items
                else:
                    return False, dash.no_update, dash.no_update, dash.no_update, dash.no_update

            elif button_id == 'modal_cancel':
                # Just close the modal without doing anything else
                return False, dash.no_update, dash.no_update, dash.no_update, dash.no_update

            return dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update

        return app
