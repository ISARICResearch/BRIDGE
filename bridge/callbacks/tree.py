import io
import json
from typing import Tuple

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
        State('selected-language-store', 'data'),
        State('ulist_variable_choices-store', 'data'),
        State('multilist_variable_choices-store', 'data'),
    ],
    prevent_initial_call=True
)
def update_tree_items_and_stores(checked_templates: list,
                                 upload_crf_ready: bool,
                                 current_datadicc_saved: str,
                                 grouped_presets_dict: dict,
                                 selected_version_data: dict,
                                 selected_language_data: dict,
                                 version_lang_ulist_saved: str,
                                 version_lang_multilist_saved: str):
    if upload_crf_ready:
        return (dash.no_update,
                dash.no_update,
                dash.no_update,
                dash.no_update)

    ctx = dash.callback_context
    df_datadicc = pd.read_json(io.StringIO(current_datadicc_saved), orient='split')

    version = selected_version_data.get('selected_version')
    language = selected_language_data.get('selected_language')

    tree_items_data = arc_tree.get_tree_items(df_datadicc, version)

    if (not ctx.triggered) | (all(not sublist for sublist in checked_templates)):
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

    logger.info(f'checked_variables: {checked_templates}')
    logger.info(f'grouped_presets: {grouped_presets_dict}')
    checked_template_list = get_checked_template_list(grouped_presets_dict, checked_templates)

    checked = []
    ulist_variable_choices = []
    multilist_variable_choices = []

    if len(checked_template_list) > 0:
        for ps in checked_template_list:
            checked_key = 'preset_' + ps[0] + '_' + ps[1]
            if checked_key in df_datadicc.columns:
                checked = checked + list(
                    df_datadicc['Variable'].loc[df_datadicc[checked_key].notnull()])

            (df_datadicc,
             ulist_variable_choices) = update_list_items(df_datadicc,
                                                         version_lang_ulist_saved,
                                                         'user_list',
                                                         version,
                                                         language,
                                                         checked_key=checked_key)

            (df_datadicc,
             multilist_variable_choices) = update_list_items(df_datadicc,
                                                             version_lang_multilist_saved,
                                                             'multi_list',
                                                             version,
                                                             language,
                                                             checked_key=checked_key)

    else:
        (df_datadicc,
         ulist_variable_choices) = update_list_items(df_datadicc,
                                                     version_lang_ulist_saved,
                                                     'user_list',
                                                     version,
                                                     language)

        (df_datadicc,
         multilist_variable_choices) = update_list_items(df_datadicc,
                                                         version_lang_ulist_saved,
                                                         'multi_list',
                                                         version,
                                                         language)

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
        df_datadicc.to_json(date_format='iso', orient='split'),
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


def update_list_items(df_datadicc: pd.DataFrame,
                      list_saved: str,
                      list_type: str,
                      version: str,
                      language: str,
                      checked_key: str = None) -> Tuple[pd.DataFrame, str]:
    translations_for_language = arc_translations.get_translations(language)
    other_text = translations_for_language['other']

    df_datadicc_list = df_datadicc.loc[df_datadicc['Type'] == list_type]

    list_variable_choices_updated = []

    for _, datadicc_list_variable_row in df_datadicc_list.iterrows():
        # Iterate over the variables in this df as it has the list name
        list_items_updated = []
        select_answer_options = ''
        not_select_answer_options = ''

        list_name = str(datadicc_list_variable_row['List'])
        variable_name = datadicc_list_variable_row['Variable']
        variable_name_not_selected = f'{variable_name}_otherl2'

        df_template_list_data = ArcApiClient().get_dataframe_arc_list_version_language(version,
                                                                                       language,
                                                                                       list_name.replace('_', '/'))

        if checked_key and checked_key in df_template_list_data.columns:
            selected_column = checked_key
        else:
            selected_column = 'Selected'

        df_list_saved = pd.DataFrame(json.loads(list_saved), columns=['Variable', selected_column])
        list_items_saved = df_list_saved.loc[df_list_saved['Variable'] == variable_name, selected_column].values[0]

        for list_item in list_items_saved:
            # Update the list items saved with the settings in the template
            list_item_name = list_item[1]
            list_item_number = list_item[0]

            df_template_list_data[selected_column] = df_template_list_data[selected_column].apply(
                lambda x: float(1) if type(x) == str and x.replace(' ', '') == '1' else x)
            df_template_checked = df_template_list_data[df_template_list_data[selected_column] == float(1)]

            checked_list = list(df_template_checked.iloc[:, 0].values)

            if list_item_name in checked_list:
                list_items_updated.append([list_item_number, str(list_item_name), 1])
                select_answer_options += f'{list_item_number}, {str(list_item_name)} | '
            else:
                list_items_updated.append([list_item_number, str(list_item_name), 0])
                not_select_answer_options += f'{list_item_number}, {str(list_item_name)} | '

        df_datadicc.loc[df_datadicc['Variable'] == variable_name, 'Answer Options'] \
            = f'{select_answer_options}88, {other_text}'

        if variable_name_not_selected in list(df_datadicc['Variable']):
            df_datadicc.loc[df_datadicc['Variable'] == variable_name_not_selected, 'Answer Options'] \
                = f'{not_select_answer_options}88, {other_text}'

        list_variable_choices_updated.append([variable_name, list_items_updated])

    return (
        df_datadicc,
        json.dumps(list_variable_choices_updated),
    )


@dash.callback(
    Output('output-expanded', 'children'),
    Input('input', 'expanded')
)
def display_expanded_tree_items(expanded: str) -> str:
    return 'You have expanded {}'.format(expanded)
