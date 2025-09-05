import base64
import io
import json
import re

import dash
import dash_treeview_antd
import pandas as pd
from dash import html, Input, Output, State

from bridge.arc import arc
from bridge.layout.language import Language
from bridge.logging.logger import setup_logger

logger = setup_logger(__name__)

pd.options.mode.copy_on_write = True


class Upload:

    @staticmethod
    def register_callbacks(app):

        @app.callback(
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
        def on_upload_crf(filename, contents):

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

        @app.callback(
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
        def load_upload_arc_version_language(upload_version_data, upload_language_data, selected_version_data,
                                             selected_language_data):
            ctx = dash.callback_context

            if not ctx.triggered:
                return (dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update,
                        False, None, dash.no_update, dash.no_update)

            upload_version = upload_version_data.get('upload_version', None)
            upload_language = upload_language_data.get('upload_language', None)

            if ((selected_version_data and upload_version == selected_version_data.get('selected_version', None)) and (
                    selected_language_data and upload_language == selected_language_data.get('selected_language',
                                                                                             None))):
                return (dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update,
                        True, None, dash.no_update, dash.no_update)

            try:
                (df_upload_version, version_commit, version_grouped_presets, version_accordion_items,
                 version_ulist_variable_choices, version_multilist_variable_choices) = Language(upload_version,
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
                return (dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update,
                        False, None, dash.no_update, dash.no_update)

        def update_for_upload_list_selected(df_datadicc, df_list_upload, list_variable_choices, list_type, language):
            translations_for_language = arc.get_translations(language)
            other_text = translations_for_language['other']

            selected_column = f'{list_type} Selected'
            # Use a dataframe to make replacing values easier
            df_list_all = pd.DataFrame(json.loads(list_variable_choices), columns=['Variable', selected_column])
            df_list_upload = df_list_upload[df_list_upload[selected_column].notnull()]

            for index, row in df_list_upload.iterrows():
                list_name = row['Variable']
                boxes_checked = row[selected_column]
                if pd.notnull(boxes_checked):
                    boxes_checked_list = boxes_checked.split('|')
                    list_index = df_list_all[df_list_all['Variable'] == list_name].index
                    list_values = df_list_all.loc[list_index, selected_column].values[0]
                    list_values_updated = []

                    datadicc_index = df_datadicc.loc[df_datadicc['Variable'] == list_name].index
                    datadicc_values_updated = []

                    for list_value in list_values:
                        list_value_name = list_value[1]
                        if list_value_name not in boxes_checked_list:
                            list_values_updated.append(list_value)
                        else:
                            list_value_number = list_value[0]
                            list_values_updated.append([list_value_number, list_value_name, 1])
                            datadicc_values_updated.append(f'{list_value_number}, {list_value_name}')

                    list_values_updated.append(f'88, {other_text}')
                    datadicc_values_updated.append(f'88, {other_text}')

                    df_list_all.loc[list_index, selected_column] = pd.Series([list_values_updated])
                    df_datadicc.loc[datadicc_index, 'Answer Options'] = ' | '.join(datadicc_values_updated)

            list_variable_choices_updated = df_list_all.values.tolist()

            return df_datadicc, list_variable_choices_updated

        @app.callback(
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
        def update_output_upload_crf(upload_crf_ready, upload_version_data, upload_language_data, upload_crf_contents,
                                     upload_version_lang_datadicc_saved, upload_version_lang_ulist_saved,
                                     upload_version_lang_multilist_saved):
            ctx = dash.callback_context

            if not ctx.triggered:
                return dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update

            upload_version = upload_version_data.get('upload_version', None)
            upload_language = upload_language_data.get('upload_language', None)
            upload_type, upload_string = upload_crf_contents.split(',')
            upload_decoded = base64.b64decode(upload_string)
            df_upload_csv = pd.read_csv(io.StringIO(upload_decoded.decode('utf-8')))
            checked = list(df_upload_csv['Variable'])

            df_version_lang_datadicc = pd.read_json(io.StringIO(upload_version_lang_datadicc_saved), orient='split')
            tree_items_current_datadicc = arc.get_tree_items(df_version_lang_datadicc, upload_version)

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

            df_datadicc_selected, ulist_variables_selected = update_for_upload_list_selected(df_version_lang_datadicc,
                                                                                             df_upload_ulist,
                                                                                             upload_version_lang_ulist_saved,
                                                                                             'Ulist',
                                                                                             upload_language)
            df_datadicc_selected, multilist_variables_selected = update_for_upload_list_selected(df_datadicc_selected,
                                                                                                 df_upload_multilist,
                                                                                                 upload_version_lang_multilist_saved,
                                                                                                 'Multilist',
                                                                                                 upload_language)

            return (
                tree_items,
                df_datadicc_selected.to_json(date_format='iso', orient='split'),
                json.dumps(ulist_variables_selected),
                json.dumps(multilist_variables_selected),
                None,
            )

        return app
