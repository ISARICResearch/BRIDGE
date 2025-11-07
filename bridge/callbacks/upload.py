import base64
import io
import json
import re
from typing import Tuple

import dash
import dash_treeview_antd
import pandas as pd
from dash import html, Input, Output, State

from bridge.arc import arc_translations, arc_tree
from bridge.callbacks.language import Language
from bridge.logging.logger import setup_logger

logger = setup_logger(__name__)

pd.options.mode.copy_on_write = True


@dash.callback(
    [
        Output('upload-version-store', 'data', allow_duplicate=True),
        Output('upload-language-store', 'data', allow_duplicate=True),
    ],
    [
        Input('upload-crf', 'filename'),
        Input('upload-crf', 'contents'),
    ],
    prevent_initial_call=True
)
def on_upload_crf(filename: str,
                  contents: str):
    if filename:
        try:
            upload_version = re.search(r'v\d_\d_\d', filename).group(0)
            upload_language = filename.split(f'{upload_version}_')[1].split('_')[0]
        except AttributeError as e:
            logger.error(e)
            raise AttributeError(f'Failed to determine ARC version and/or language from file {filename}')
        return (
            {'upload_version': upload_version.replace('_', '.')},
            {'upload_language': upload_language},
        )

    return dash.no_update, dash.no_update


@dash.callback(
    [
        Output('selected-version-store', 'data', allow_duplicate=True),
        Output('selected-language-store', 'data', allow_duplicate=True),
        Output('commit-store', 'data', allow_duplicate=True),
        Output('preset-accordion', 'children', allow_duplicate=True),
        Output('grouped_presets-store', 'data', allow_duplicate=True),
        Output('current_datadicc-store', 'data', allow_duplicate=True),
        Output('upload-crf-ready', 'data'),
        Output('crf_name', 'value', allow_duplicate=True),
        Output('ulist_variable_choices-store', 'data', allow_duplicate=True),
        Output('multilist_variable_choices-store', 'data', allow_duplicate=True),
    ],
    [
        Input('upload-version-store', 'data'),
        Input('upload-language-store', 'data'),
    ],
    [
        State('selected-version-store', 'data'),
        State('selected-language-store', 'data'),
    ],
    prevent_initial_call=True
)
def load_upload_arc_version_language(upload_version_data: dict,
                                     upload_language_data: dict,
                                     selected_version_data: dict,
                                     selected_language_data: dict):
    ctx = dash.callback_context

    if not ctx.triggered:
        return (dash.no_update,
                dash.no_update,
                dash.no_update,
                dash.no_update,
                dash.no_update,
                dash.no_update,
                False,
                None,
                dash.no_update,
                dash.no_update)

    upload_version = upload_version_data.get('upload_version')
    upload_language = upload_language_data.get('upload_language')

    if ((selected_version_data
         and upload_version == selected_version_data.get('selected_version', None))
            and (selected_language_data
                 and upload_language == selected_language_data.get('selected_language', None))):
        return (dash.no_update,
                dash.no_update,
                dash.no_update,
                dash.no_update,
                dash.no_update,
                dash.no_update,
                True,
                None,
                dash.no_update,
                dash.no_update)

    try:
        (df_upload_version,
         version_commit,
         version_grouped_presets,
         version_accordion_items,
         version_ulist_variable_choices,
         version_multilist_variable_choices) = Language(upload_version,
                                                        upload_language).get_version_language_related_data()
        logger.info(f'upload_version: {upload_version}')
        logger.info(f'upload_language: {upload_language}')
        return (
            {'selected_version': upload_version},
            {'selected_language': upload_language},
            {'commit': version_commit},
            version_accordion_items,
            version_grouped_presets,
            df_upload_version.to_json(date_format='iso', orient='split'),
            True,
            None,
            version_ulist_variable_choices,
            version_multilist_variable_choices,
        )
    except json.JSONDecodeError:
        return (dash.no_update,
                dash.no_update,
                dash.no_update,
                dash.no_update,
                dash.no_update,
                dash.no_update,
                False,
                None,
                dash.no_update,
                dash.no_update)


def update_list_variables_checked_upload(df_datadicc: pd.DataFrame,
                                         df_list_upload: pd.DataFrame,
                                         variable_choices: str,
                                         list_type: str,
                                         language: str) -> Tuple[pd.DataFrame, str]:
    translations_for_language = arc_translations.get_translations(language)
    other_text = translations_for_language['other']

    selected_column = f'{list_type} Selected'
    df_list_saved = pd.DataFrame(json.loads(variable_choices), columns=['Variable', selected_column])
    df_list_upload = df_list_upload[df_list_upload[selected_column].notnull()]

    list_variable_choices_updated = []

    for _, row in df_list_saved.iterrows():
        list_items_updated = []
        select_answer_options = ''
        not_select_answer_options = ''
        variable_name = row['Variable']
        variable_name_not_selected = f'{variable_name}_otherl2'

        df_upload_variable = df_list_upload.loc[df_list_upload['Variable'] == variable_name]

        list_items_saved = df_list_saved.loc[df_list_saved['Variable'] == variable_name, selected_column].values[0]

        for list_item in list_items_saved:
            list_item_name = list_item[1]
            list_item_number = list_item[0]

            if not df_upload_variable.empty:
                variables_checked = df_upload_variable[selected_column].values[0]
                checked_list = variables_checked.split('|')
                if list_item_name in checked_list:
                    list_items_updated.append([list_item_number, str(list_item_name), 1])
                    select_answer_options += f'{list_item_number}, {str(list_item_name)} | '
                else:
                    list_items_updated.append([list_item_number, str(list_item_name), 0])
                    not_select_answer_options += f'{list_item_number}, {str(list_item_name)} | '
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
    [
        Output('tree_items_container', 'children', allow_duplicate=True),
        Output('current_datadicc-store', 'data', allow_duplicate=True),
        Output('ulist_variable_choices-store', 'data', allow_duplicate=True),
        Output('multilist_variable_choices-store', 'data', allow_duplicate=True),
        Output('upload-crf', 'contents'),
    ],
    [
        Input('upload-crf-ready', 'data'),
    ],
    [
        State('upload-version-store', 'data'),
        State('upload-language-store', 'data'),
        State('upload-crf', 'contents'),
        State('current_datadicc-store', 'data'),
        State('ulist_variable_choices-store', 'data'),
        State('multilist_variable_choices-store', 'data'),
    ],
    prevent_initial_call=True
)
def update_output_upload_crf(upload_crf_ready: bool,
                             upload_version_data: dict,
                             upload_language_data: dict,
                             upload_crf_contents: str,
                             upload_version_lang_datadicc_saved: str,
                             upload_version_lang_ulist_saved: str,
                             upload_version_lang_multilist_saved: str):
    ctx = dash.callback_context

    if not ctx.triggered:
        return dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update

    upload_version = upload_version_data.get('upload_version')
    upload_language = upload_language_data.get('upload_language')
    upload_type, upload_string = upload_crf_contents.split(',')
    upload_decoded = base64.b64decode(upload_string)
    df_upload_csv = pd.read_csv(io.StringIO(upload_decoded.decode('utf-8')))
    checked = list(df_upload_csv['Variable'])

    df_version_lang_datadicc = pd.read_json(io.StringIO(upload_version_lang_datadicc_saved), orient='split')
    tree_items_current_datadicc = arc_tree.get_tree_items(df_version_lang_datadicc, upload_version)

    tree_items = html.Div(
        dash_treeview_antd.TreeView(
            id='input',
            multiple=False,
            checkable=True,
            checked=checked,
            expanded=checked,
            data=tree_items_current_datadicc),
        id='tree_items_container',
        className='tree-item',
    )

    df_upload_ulist = df_upload_csv[['Variable', 'Ulist Selected']]
    df_upload_multilist = df_upload_csv[['Variable', 'Multilist Selected']]

    (df_datadicc_selected,
     ulist_variable_choices) = update_list_variables_checked_upload(df_version_lang_datadicc,
                                                                    df_upload_ulist,
                                                                    upload_version_lang_ulist_saved,
                                                                    'Ulist',
                                                                    upload_language)
    (df_datadicc_selected,
     multilist_variable_choices) = update_list_variables_checked_upload(df_datadicc_selected,
                                                                        df_upload_multilist,
                                                                        upload_version_lang_multilist_saved,
                                                                        'Multilist',
                                                                        upload_language)

    return (
        tree_items,
        df_datadicc_selected.to_json(date_format='iso', orient='split'),
        ulist_variable_choices,
        multilist_variable_choices,
        None,
    )
