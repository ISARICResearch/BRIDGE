import io
import json

import dash
import dash_treeview_antd
import pandas as pd
from dash import html, Input, Output, State

from bridge.arc import arc_translations, arc_tree
from bridge.arc.arc_api import ArcApiClient
from bridge.logging.logger import setup_logger

pd.options.mode.copy_on_write = True

logger = setup_logger(__name__)


@dash.callback(
    [
        Output('tree_items_container', 'children'),
        Output('current_datadicc-store', 'data', allow_duplicate=True),
        Output('ulist_variable_choices-store', 'data', allow_duplicate=True),
        Output('multilist_variable_choices-store', 'data', allow_duplicate=True)
    ],
    [
        Input({'type': 'template_check', 'index': dash.ALL}, 'value'),
        Input('upload-crf-ready', 'data'),
    ],
    [
        State('current_datadicc-store', 'data'),
        State('grouped_presets-store', 'data'),
        State('selected-version-store', 'data'),
        State('selected-language-store', "data")
    ],
    prevent_initial_call=True
)
def update_tree_items_and_stores(checked_variables: list,
                                 upload_crf_ready: bool,
                                 current_datadicc_saved: str,
                                 grouped_presets_dict: dict,
                                 selected_version_data: dict,
                                 selected_language_data: dict):
    if upload_crf_ready:
        return (dash.no_update,
                dash.no_update,
                dash.no_update,
                dash.no_update)

    ctx = dash.callback_context
    df_current_datadicc = pd.read_json(io.StringIO(current_datadicc_saved), orient='split')

    current_version = selected_version_data.get('selected_version')
    current_language = selected_language_data.get('selected_language')

    tree_items_data = arc_tree.get_tree_items(df_current_datadicc, current_version)

    if (not ctx.triggered) | (all(not sublist for sublist in checked_variables)):
        tree_items = html.Div(
            dash_treeview_antd.TreeView(
                id='input',
                multiple=False,
                checkable=True,
                checked=[],
                expanded=[],
                data=tree_items_data),
            id='tree_items_container',
            className='tree-item',
        )
        return (tree_items,
                dash.no_update,
                dash.no_update,
                dash.no_update)

    logger.info(f'checked_variables: {checked_variables}')
    logger.info(f'grouped_presets: {grouped_presets_dict}')
    checked_template_list = get_checked_template_list(grouped_presets_dict, checked_variables)

    checked = []
    ulist_variable_choices = []
    multilist_variable_choices = []

    if len(checked_template_list) > 0:
        for ps in checked_template_list:
            checked_key = 'preset_' + ps[0] + '_' + ps[1]
            if checked_key in df_current_datadicc:
                checked = checked + list(
                    df_current_datadicc['Variable'].loc[df_current_datadicc[checked_key].notnull()])

            df_current_datadicc, ulist_variable_choices, multilist_variable_choices = update_for_template_options(
                current_version, current_language, df_current_datadicc, ulist_variable_choices,
                multilist_variable_choices,
                checked_key=checked_key)

    else:
        df_current_datadicc, ulist_variable_choices, multilist_variable_choices = update_for_template_options(
            current_version, current_language, df_current_datadicc, ulist_variable_choices,
            multilist_variable_choices)

    tree_items = html.Div(
        dash_treeview_antd.TreeView(
            id='input',
            multiple=False,
            checkable=True,
            checked=checked,
            expanded=checked,
            data=tree_items_data),
        id='tree_items_container',
        className='tree-item',
    )

    return (
        tree_items,
        df_current_datadicc.to_json(date_format='iso', orient='split'),
        json.dumps(ulist_variable_choices),
        json.dumps(multilist_variable_choices)
    )


def get_checked_template_list(grouped_presets_dict: dict,
                              checked_values_list: list) -> list:
    output = []
    for section, item_checked_list in zip(grouped_presets_dict.keys(), checked_values_list):
        if item_checked_list:
            for item_checked in item_checked_list:
                output.append([section, item_checked.replace(' ', '_')])
    return output


def update_for_template_options(version: str,
                                language: str,
                                df_current_datadicc: pd.DataFrame,
                                ulist_variable_choices: list,
                                multilist_variable_choices: list,
                                checked_key: str = None):
    translations_for_language = arc_translations.get_translations(language)
    other_text = translations_for_language['other']

    df_datadicc_u_multilists = df_current_datadicc.loc[df_current_datadicc['Type'].isin(['user_list', 'multi_list'])]

    for list_data_index, list_data in df_datadicc_u_multilists.iterrows():
        ulist_options = []
        multilist_options = []
        list_name = list_data['List']
        df_list_data = ArcApiClient().get_dataframe_arc_list_version_language(version, language,
                                                                              list_name.replace('_', '/'))

        select_answer_options = ''
        not_select_answer_options = ''

        list_index = 1
        for index, row in df_list_data.iterrows():
            if list_index == 88:
                list_index = 89
            elif list_index == 99:
                list_index = 100

            if checked_key and checked_key in df_list_data.columns:
                selected_column = checked_key
            else:
                selected_column = 'Selected'

            selected_value = row[selected_column]
            if isinstance(selected_value, str):
                selected_value = float(1) if selected_value.replace(' ', '') == '1' else None

            if pd.notnull(selected_value) and int(selected_value) == 1:
                if list_data['Type'] == 'user_list':
                    ulist_options.append([str(list_index), str(row[df_list_data.columns[0]]), 1])
                elif list_data['Type'] == 'multi_list':
                    multilist_options.append([str(list_index), str(row[df_list_data.columns[0]]), 1])
                select_answer_options += f'{str(list_index)}, {str(row[df_list_data.columns[0]])} | '
            else:
                if list_data['Type'] == 'user_list':
                    ulist_options.append([str(list_index), str(row[df_list_data.columns[0]]), 0])
                elif list_data['Type'] == 'multi_list':
                    multilist_options.append([str(list_index), str(row[df_list_data.columns[0]]), 0])
                not_select_answer_options += f'{str(list_index)}, {str(row[df_list_data.columns[0]])} | '
            list_index += 1

        df_current_datadicc.loc[df_current_datadicc['Variable'] == list_data[
            'Variable'], 'Answer Options'] = f'{select_answer_options} 88, {other_text}'

        if list_data['Variable'] + '_otherl2' in list(df_current_datadicc['Variable']):
            df_current_datadicc.loc[df_current_datadicc['Variable'] == list_data[
                'Variable'] + '_otherl2', 'Answer Options'] = f'{not_select_answer_options} 88, {other_text}'

        if list_data['Type'] == 'user_list':
            ulist_variable_choices.append([list_data['Variable'], ulist_options])

        elif list_data['Type'] == 'multi_list':
            multilist_variable_choices.append([list_data['Variable'], multilist_options])

    return df_current_datadicc, ulist_variable_choices, multilist_variable_choices


@dash.callback(
    Output('output-expanded', 'children'),
    Input('input', 'expanded')
)
def display_expanded_tree_items(expanded: str) -> str:
    return 'You have expanded {}'.format(expanded)
