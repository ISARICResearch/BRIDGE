import io
import json

import dash
import dash_bootstrap_components as dbc
import dash_treeview_antd
import pandas as pd
from dash import html, Input, Output, State
from dash.exceptions import PreventUpdate

from bridge.arc import arc
from bridge.arc.arc_api import ArcApiClient
from bridge.layout.language import Language
from bridge.logging.logger import setup_logger

pd.options.mode.copy_on_write = True

logger = setup_logger(__name__)


class Tree:

    def __init__(self, tree_items_data):
        self.tree_items_data = tree_items_data

        self.tree_items = html.Div(
            dash_treeview_antd.TreeView(
                id='input',
                multiple=False,
                checkable=True,
                checked=[],
                data=self.tree_items_data),
            id='tree_items_container',
            className='tree-item',
        )

        self.tree_column = dbc.Fade(
            self.tree_items,
            id="tree-column",
            is_in=True,  # Initially show
            style={
                "position": "fixed",
                "left": "4rem",
                "width": "33rem",
                "height": "90%",
            }
        )

    @staticmethod
    def register_callbacks(app):

        @app.callback(
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
        def update_tree_items_and_stores(checked_variables, upload_crf_ready, current_datadicc_saved, grouped_presets,
                                         selected_version_data, selected_lang_data):
            if  upload_crf_ready:
                return (dash.no_update,
                        dash.no_update,
                        dash.no_update,
                        dash.no_update)

            ctx = dash.callback_context
            df_current_datadicc = pd.read_json(io.StringIO(current_datadicc_saved), orient='split')

            current_version = selected_version_data.get('selected_version', None)
            current_language = selected_lang_data.get('selected_language', None)

            df_version, version_presets, version_commit = arc.get_arc(current_version)
            df_version = arc.add_required_datadicc_columns(df_version)
            df_version_language = Language(current_version, current_language).get_dataframe_arc_language(df_version)

            tree_items_data = arc.get_tree_items(df_version_language, current_version)

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

            if current_version is None or grouped_presets is None:
                raise PreventUpdate  # Prevent update if data is missing

            logger.info(f'checked_variables: {checked_variables}')
            logger.info(f'grouped_presets: {grouped_presets}')
            checked_template_list = get_checked_template_list(grouped_presets, checked_variables)

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

        def get_checked_template_list(grouped_presets_dict, checked_values_list):
            output = []
            for section, item_checked_list in zip(grouped_presets_dict.keys(), checked_values_list):
                if item_checked_list:
                    for item_checked in item_checked_list:
                        output.append([section, item_checked.replace(' ', '_')])
            return output

        def update_for_template_options(version, language, df_current_datadicc, ulist_variable_choices,
                                        multilist_variable_choices, checked_key=None):
            translations_for_language = arc.get_translations(language)
            other_text = translations_for_language['other']

            template_ulist_var = df_current_datadicc.loc[df_current_datadicc['Type'].isin(['user_list', 'multi_list'])]

            for index_tem_ul, row_tem_ul in template_ulist_var.iterrows():
                dict1_options = []
                dict2_options = []
                t_u_list = row_tem_ul['List']
                list_options = ArcApiClient().get_dataframe_arc_list_version_language(version, language,
                                                                                      t_u_list.replace('_', '/'))

                cont_lo = 1
                select_answer_options = ''

                not_select_answer_options = ''
                for index, row in list_options.iterrows():
                    if cont_lo == 88:
                        cont_lo = 89
                    elif cont_lo == 99:
                        cont_lo = 100

                    if checked_key and checked_key in list_options.columns:
                        selected_column = checked_key
                    else:
                        selected_column = 'Selected'

                    selected_value = row[selected_column]
                    if isinstance(selected_value, str):
                        selected_value = float(1) if selected_value.replace(' ', '') == '1' else None

                    if pd.notnull(selected_value) and int(selected_value) == 1:
                        if row_tem_ul['Type'] == 'user_list':
                            dict1_options.append([str(cont_lo), str(row[list_options.columns[0]]), 1])
                        elif row_tem_ul['Type'] == 'multi_list':
                            dict2_options.append([str(cont_lo), str(row[list_options.columns[0]]), 1])
                        select_answer_options += str(cont_lo) + ', ' + str(row[list_options.columns[0]]) + ' | '
                    else:
                        if row_tem_ul['Type'] == 'user_list':
                            dict1_options.append([str(cont_lo), str(row[list_options.columns[0]]), 0])
                        elif row_tem_ul['Type'] == 'multi_list':
                            dict2_options.append([str(cont_lo), str(row[list_options.columns[0]]), 0])
                        not_select_answer_options += str(cont_lo) + ', ' + str(row[list_options.columns[0]]) + ' | '
                    cont_lo += 1
                df_current_datadicc.loc[df_current_datadicc['Variable'] == row_tem_ul[
                    'Variable'], 'Answer Options'] = select_answer_options + '88, ' + other_text
                if row_tem_ul['Variable'] + '_otherl2' in list(df_current_datadicc['Variable']):
                    df_current_datadicc.loc[df_current_datadicc['Variable'] == row_tem_ul[
                        'Variable'] + '_otherl2', 'Answer Options'] = not_select_answer_options + '88, ' + other_text

                if row_tem_ul['Type'] == 'user_list':
                    ulist_variable_choices.append([row_tem_ul['Variable'], dict1_options])
                elif row_tem_ul['Type'] == 'multi_list':
                    multilist_variable_choices.append([row_tem_ul['Variable'], dict2_options])
            return df_current_datadicc, ulist_variable_choices, multilist_variable_choices

        @app.callback(
            Output('output-expanded', 'children'),
            Input('input', 'expanded')
        )
        def display_expanded_tree_items(expanded):
            return 'You have expanded {}'.format(expanded)

        return app
