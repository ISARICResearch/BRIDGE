import io
import json

import dash
import dash_bootstrap_components as dbc
import dash_treeview_antd
import pandas as pd
from dash import html, Input, Output, State

from bridge.arc import arc


@dash.callback(
    [
        Output('modal', 'is_open'),
        Output('modal_title', 'children'),
        Output('definition-text', 'children'),
        Output('completion-guide-text', 'children'),
        Output('skip-logic-text', 'children'),
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
            question = df_datadicc['Question'].loc[df_datadicc['Variable'] == selected[0]].iloc[0]
            definition = df_datadicc['Definition'].loc[df_datadicc['Variable'] == selected[0]].iloc[0]
            completion = \
                df_datadicc['Completion Guideline'].loc[df_datadicc['Variable'] == selected[0]].iloc[0]
            skip_logic = df_datadicc['Branch'].loc[df_datadicc['Variable'] == selected[0]].iloc[0]

            ulist_variables = [i[0] for i in dict_lists]
            if selected_variable in ulist_variables:
                for item in dict_lists:
                    if item[0] == selected_variable:
                        options = []
                        checked_items = []
                        for i in item[1]:
                            options.append({"label": str(i[0]) + ', ' + i[1], "value": str(i[0]) + '_' + i[1]})
                            if i[2] == 1:
                                checked_items.append(str(i[0]) + '_' + i[1])

                return True, question + ' [' + selected_variable + ']', definition, completion, skip_logic, {
                    "padding": "20px", "maxHeight": "250px", "overflowY": "auto"}, {
                    "display": "none"}, options, checked_items, []
            else:
                options = []
                answ_options = \
                    df_datadicc['Answer Options'].loc[df_datadicc['Variable'] == selected_variable].iloc[0]
                if isinstance(answ_options, str):
                    for i in answ_options.split('|'):
                        options.append(dbc.ListGroupItem(i))
                else:
                    options = []
                return True, question + ' [' + selected_variable + ']', definition, completion, skip_logic, {
                    "display": "none"}, {"maxHeight": "250px", "overflowY": "auto"}, [], [], options

    return False, '', '', '', '', {"display": "none"}, {"display": "none"}, [], [], []


@dash.callback(
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
                          checked_options, checked, ulist_variable_choices_saved,
                          multilist_variable_choices_saved, selected_version_data, selected_language_data):
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
            for checked_option in checked_options:
                list_options_checked.append(checked_option.split('_'))

            list_options_checked = pd.DataFrame(data=list_options_checked, columns=['cod', 'Option'])

            ulist_variable_choices_submit = determine_list_variable_choices(ulist_variable_choices_dict,
                                                                            variable_submitted,
                                                                            list_options_checked,
                                                                            df_current_datadicc, other_text)

            multilist_variable_choices_submit = determine_list_variable_choices(multilist_variable_choices_dict,
                                                                                variable_submitted,
                                                                                list_options_checked,
                                                                                df_current_datadicc, other_text)

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
                ulist_variable_choices_submit), json.dumps(multilist_variable_choices_submit), tree_items
        else:
            return False, dash.no_update, dash.no_update, dash.no_update, dash.no_update

    elif button_id == 'modal_cancel':
        # Just close the modal without doing anything else
        return False, dash.no_update, dash.no_update, dash.no_update, dash.no_update

    return dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update


def determine_list_variable_choices(variable_choices_dict, variable_submitted, list_options_checked,
                                    df_current_datadicc, other_text):
    new_submitted_options = []
    new_submitted_line = []
    position = 0
    for var_select in variable_choices_dict:
        if var_select[0] == variable_submitted:
            select_answer_options = ''
            not_select_answer_options = ''
            for option_var_select in (var_select[1]):
                if option_var_select[1] in (list(list_options_checked['Option'])):
                    new_submitted_options.append([option_var_select[0], option_var_select[1], 1])
                    select_answer_options += str(option_var_select[0]) + ', ' + str(
                        option_var_select[1]) + ' | '
                else:
                    new_submitted_options.append([option_var_select[0], option_var_select[1], 0])
                    not_select_answer_options += str(option_var_select[0]) + ', ' + str(
                        option_var_select[1]) + ' | '
            new_submitted_line.append([var_select, new_submitted_options])
            variable_choices_dict[position][1] = new_submitted_line[0][1]
            df_current_datadicc.loc[df_current_datadicc[
                                        'Variable'] == variable_submitted, 'Answer Options'] = select_answer_options + '88, ' + other_text
            if variable_submitted + '_otherl2' in list(df_current_datadicc['Variable']):
                df_current_datadicc.loc[df_current_datadicc[
                                            'Variable'] == variable_submitted + '_otherl2', 'Answer Options'] = not_select_answer_options + '88, ' + other_text

        position += 1
    return variable_choices_dict
