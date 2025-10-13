import io
import json
from typing import Tuple

import dash
import dash_bootstrap_components as dbc
import dash_treeview_antd
import pandas as pd
from dash import html, Input, Output, State

from bridge.arc import arc_translations, arc_tree
from bridge.utils.trigger_id import get_trigger_id


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
    [
        Input('input', 'selected'),
    ],
    [
        State('ulist_variable_choices-store', 'data'),
        State('multilist_variable_choices-store', 'data'),
        State('modal', 'is_open'),
        State('current_datadicc-store', 'data'),
    ])
def display_selected_in_modal(selected: list,
                              ulist_variable_choices_saved: str,
                              multilist_variable_choices_saved: str,
                              is_open: bool,
                              current_datadicc_saved: str) -> (
        Tuple)[bool, str, str, str, str, dict, dict, list, list, list]:
    if selected:
        ulist = json.loads(ulist_variable_choices_saved)
        multilist = json.loads(multilist_variable_choices_saved)
        ulist_multilist = ulist + multilist
        df_datadicc = pd.read_json(io.StringIO(current_datadicc_saved), orient='split')
        selected_variable = selected[0]
        if selected_variable in list(df_datadicc['Variable']):
            question = df_datadicc['Question'].loc[df_datadicc['Variable'] == selected[0]].iloc[0]
            definition = df_datadicc['Definition'].loc[df_datadicc['Variable'] == selected[0]].iloc[0]
            completion = \
                df_datadicc['Completion Guideline'].loc[df_datadicc['Variable'] == selected[0]].iloc[0]
            skip_logic = df_datadicc['Branch'].loc[df_datadicc['Variable'] == selected[0]].iloc[0]

            ulist_multilist_names = [item[0] for item in ulist_multilist]
            if selected_variable in ulist_multilist_names:
                for ulist_multilist_item in ulist_multilist:
                    ulist_multilist_name = ulist_multilist_item[0]
                    if ulist_multilist_name == selected_variable:
                        options = []
                        checked_items = []
                        for ulist_multilist_variable in ulist_multilist_item[1]:
                            options.append(
                                {"label": str(ulist_multilist_variable[0]) + ', ' + ulist_multilist_variable[1],
                                 "value": str(ulist_multilist_variable[0]) + '_' + ulist_multilist_variable[1]})
                            if ulist_multilist_variable[2] == 1:
                                checked_items.append(
                                    str(ulist_multilist_variable[0]) + '_' + ulist_multilist_variable[1])

                        return True, question + ' [' + selected_variable + ']', definition, completion, skip_logic, {
                            "padding": "20px", "maxHeight": "250px", "overflowY": "auto"}, {
                            "display": "none"}, options, checked_items, []
            else:
                options = []
                answer_options = \
                    df_datadicc['Answer Options'].loc[df_datadicc['Variable'] == selected_variable].iloc[0]
                if isinstance(answer_options, str):
                    for ulist_multilist_variable in answer_options.split('|'):
                        options.append(dbc.ListGroupItem(ulist_multilist_variable))
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
def on_modal_button_click(submit_n_clicks: int,
                          cancel_n_clicks: int,
                          current_datadicc_saved: str,
                          modal_title: str,
                          modal_options_checked: list,
                          checked: list,
                          ulist_variable_choices_saved: str,
                          multilist_variable_choices_saved: str,
                          selected_version_data: dict,
                          selected_language_data: dict):
    ctx = dash.callback_context

    if not ctx.triggered:
        return dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update

    trigger_id = get_trigger_id(ctx)

    if trigger_id == 'modal_submit':

        df_current_datadicc = pd.read_json(io.StringIO(current_datadicc_saved), orient='split')
        selected_version = selected_version_data.get('selected_version')
        selected_language = selected_language_data.get('selected_language')
        translations_for_language = arc_translations.get_translations(selected_language)
        other_text = translations_for_language['other']

        variable_submitted = modal_title.split('[')[1][:-1]

        ulist_variable_choices_dict = json.loads(ulist_variable_choices_saved)
        multilist_variable_choices_dict = json.loads(multilist_variable_choices_saved)

        ulist_variables = [i[0] for i in json.loads(ulist_variable_choices_saved)]
        multilist_variables = [i[0] for i in json.loads(multilist_variable_choices_saved)]

        if (variable_submitted in ulist_variables) | (variable_submitted in multilist_variables):
            list_options_checked = []
            for checked_option in modal_options_checked:
                list_options_checked.append(checked_option.split('_'))

            list_options_checked = pd.DataFrame(data=list_options_checked, columns=['cod', 'Option'])

            df_current_datadicc, ulist_variable_choices_submit = determine_list_variable_choices(
                ulist_variable_choices_dict,
                variable_submitted,
                list_options_checked,
                df_current_datadicc,
                other_text)

            df_current_datadicc, multilist_variable_choices_submit = determine_list_variable_choices(
                multilist_variable_choices_dict,
                variable_submitted,
                list_options_checked,
                df_current_datadicc,
                other_text)

            checked.append(variable_submitted)

            tree_items_data = arc_tree.get_tree_items(df_current_datadicc, selected_version)

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

    elif trigger_id == 'modal_cancel':
        # Just close the modal without doing anything else
        return False, dash.no_update, dash.no_update, dash.no_update, dash.no_update

    return dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update


def determine_list_variable_choices(variable_choices_list: list,
                                    variable_submitted: str,
                                    df_list_options_checked: pd.DataFrame,
                                    df_current_datadicc: pd.DataFrame,
                                    other_text: str) -> Tuple[pd.DataFrame, list]:
    new_submitted_options = []
    new_submitted_line = []
    position = 0
    for var_select in variable_choices_list:
        if var_select[0] == variable_submitted:
            select_answer_options = ''
            not_select_answer_options = ''
            for option_var_select in (var_select[1]):
                if option_var_select[1] in (list(df_list_options_checked['Option'])):
                    new_submitted_options.append([option_var_select[0], option_var_select[1], 1])
                    select_answer_options += str(option_var_select[0]) + ', ' + str(
                        option_var_select[1]) + ' | '
                else:
                    new_submitted_options.append([option_var_select[0], option_var_select[1], 0])
                    not_select_answer_options += str(option_var_select[0]) + ', ' + str(
                        option_var_select[1]) + ' | '
            new_submitted_line.append([var_select, new_submitted_options])
            variable_choices_list[position][1] = new_submitted_line[0][1]
            df_current_datadicc.loc[df_current_datadicc['Variable'] == variable_submitted, 'Answer Options'] = (
                    select_answer_options + '88, ' + other_text)
            if variable_submitted + '_otherl2' in list(df_current_datadicc['Variable']):
                df_current_datadicc.loc[
                    df_current_datadicc['Variable'] == variable_submitted + '_otherl2', 'Answer Options'] = (
                        not_select_answer_options + '88, ' + other_text)

        position += 1
    return df_current_datadicc, variable_choices_list
