import json

import dash
import dash_bootstrap_components as dbc
from dash import Input, Output, State

from bridge.arc import arc
from bridge.arc.arc_api import ArcApiClient
from bridge.callbacks.language import Language
from bridge.logging.logger import setup_logger

logger = setup_logger(__name__)


@dash.callback(
    Output("dropdown-ARC_version_input", "value"),
    Input('selected-version-store', 'data'),
)
def update_input_version(data):
    if data is None:
        return dash.no_update
    return data.get('selected_version')


@dash.callback(
    Output("dropdown-ARC_language_input", "value"),
    Input('selected-language-store', 'data'),
)
def update_input_language(data):
    if data is None:
        return dash.no_update
    return data.get('selected_language')


@dash.callback(
    [
        Output("dropdown-ARC-language-menu", "children"),
        Output("language-list-store", "data"),
    ],
    Input('selected-version-store', 'data'),
)
def update_language_available_for_version(selected_version_data):
    if not selected_version_data:
        return dash.no_update, dash.no_update

    current_version = selected_version_data.get('selected_version', None)
    arc_languages = ArcApiClient().get_arc_language_list_version(current_version)
    arc_language_items = [dbc.DropdownMenuItem(language, id={"type": "dynamic-language", "index": i}) for
                          i, language in enumerate(arc_languages)]
    return arc_language_items, arc_languages


@dash.callback(
    Output("output-files-store", "data"),
    Input("output-files-checkboxes", "value")
)
def update_output_files_store(checked_values):
    return checked_values


@dash.callback(
    [
        Output('selected-version-store', 'data', allow_duplicate=True),
        Output('selected-language-store', 'data', allow_duplicate=True),
        Output('commit-store', 'data', allow_duplicate=True),
        Output('preset-accordion', 'children', allow_duplicate=True),
        Output('grouped_presets-store', 'data'),
        Output('current_datadicc-store', 'data', allow_duplicate=True),
        Output('templates_checks_ready', 'data'),
        Output('ulist_variable_choices-store', 'data', allow_duplicate=True),
        Output('multilist_variable_choices-store', 'data', allow_duplicate=True),
    ],
    [
        Input({'type': 'dynamic-version', 'index': dash.ALL}, 'n_clicks'),
        Input({'type': 'dynamic-language', 'index': dash.ALL}, 'n_clicks'),
        Input('upload-crf-ready', 'data'),
    ],
    [
        State('selected-version-store', 'data'),
        State('selected-language-store', 'data'),
        State('language-list-store', 'data'),
    ],
    prevent_initial_call=True
)
def store_data_for_selected_version_language(n_clicks_version, n_clicks_language, upload_crf_ready,
                                             selected_version_data, selected_language_data, language_list_data):
    if upload_crf_ready:
        return (dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update,
                dash.no_update, dash.no_update, dash.no_update)

    ctx = dash.callback_context

    if not ctx.triggered:
        return (dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update,
                False, dash.no_update, dash.no_update)

    button_id = ctx.triggered[0]['prop_id'].split(".")[0]
    button_index = json.loads(button_id)["index"]
    button_type = json.loads(button_id)["type"]

    selected_version = None
    selected_language = None

    if button_type == 'dynamic-version':
        arc_version_list, _arc_version_latest = arc.get_arc_versions()
        selected_version = arc_version_list[button_index]
        if selected_version_data and selected_version == selected_version_data.get('selected_version', None):
            return (dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update,
                    dash.no_update,
                    False, dash.no_update, dash.no_update)
        # Reset to English to ensure the data is present
        selected_language = 'English'

    elif button_type == 'dynamic-language':
        if not upload_crf_ready:
            selected_language = language_list_data[button_index]
        else:
            # We don't have the button_index if loading from file
            selected_language = selected_language_data.get('selected_language', None)
        selected_version = selected_version_data.get('selected_version')

    try:
        (
            df_version,
            version_commit,
            version_presets,
            version_accordion_items,
            version_ulist_variable_choices,
            version_multilist_variable_choices
        ) = Language(selected_version, selected_language).get_version_language_related_data()
        logger.info(f'selected_version: {selected_version}')
        logger.info(f'selected_language: {selected_language}')
        logger.info(f'version_presets: {version_presets}')

        return (
            {'selected_version': selected_version},
            {'selected_language': selected_language},
            {'commit': version_commit},
            version_accordion_items,
            version_presets,
            df_version.to_json(date_format='iso', orient='split'),
            True,
            version_ulist_variable_choices,
            version_multilist_variable_choices
        )
    except json.JSONDecodeError:
        return (dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update,
                False, dash.no_update, dash.no_update)
