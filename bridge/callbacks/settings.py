import json

import dash
import dash_bootstrap_components as dbc
import pandas as pd
from dash import Input, Output, State

from bridge.arc import arc_core
from bridge.arc.arc_api import ArcApiClient
from bridge.callbacks.language import Language
from bridge.logging.logger import setup_logger
from bridge.utils.trigger_id import get_trigger_id

logger = setup_logger(__name__)


@dash.callback(
    Output("dropdown-ARC_version_input", "value"),
    Input('selected-version-store', 'data'),
)
def update_input_version(data: dict) -> str | None:
    if data is None:
        return dash.no_update
    return data.get('selected_version', None)


@dash.callback(
    Output("dropdown-ARC_language_input", "value"),
    Input('selected-language-store', 'data'),
)
def update_input_language(data: dict) -> str | None:
    if data is None:
        return dash.no_update
    return data.get('selected_language', None)


@dash.callback(
    [
        Output("dropdown-ARC-language-menu", "children"),
        Output("language-list-store", "data"),
    ],
    [
        Input('selected-version-store', 'data'),
    ],
)
def update_language_available_for_version(selected_version_data: dict):
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
def update_output_files_store(checked_values: list) -> list:
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
        State('language-list-store', 'data'),
    ],
    prevent_initial_call=True
)
def store_data_for_selected_version_language(n_clicks_version: list,
                                             n_clicks_language: list,
                                             upload_crf_ready: bool,
                                             selected_version_data: dict,
                                             language_list_data: list):
    if upload_crf_ready:
        # CRF upload updates in a different callback
        return (dash.no_update,
                dash.no_update,
                dash.no_update,
                dash.no_update,
                dash.no_update,
                dash.no_update,
                dash.no_update,
                dash.no_update,
                dash.no_update)

    ctx = dash.callback_context

    if not ctx.triggered:
        return (dash.no_update,
                dash.no_update,
                dash.no_update,
                dash.no_update,
                dash.no_update,
                dash.no_update,
                False,
                dash.no_update,
                dash.no_update)

    trigger_id = get_trigger_id(ctx)
    button_index = json.loads(trigger_id)["index"]
    button_type = json.loads(trigger_id)["type"]

    initial_load = determine_initial_load_boolean(n_clicks_version,
                                                  n_clicks_language)

    selected_version = None
    selected_language = None

    if button_type == 'dynamic-version':
        arc_version_list, _arc_version_latest = arc_core.get_arc_versions()
        selected_version = arc_version_list[button_index]
        if selected_version_data and selected_version == selected_version_data.get('selected_version', None):
            return (dash.no_update,
                    dash.no_update,
                    dash.no_update,
                    dash.no_update,
                    dash.no_update,
                    dash.no_update,
                    False,
                    dash.no_update,
                    dash.no_update)
        # Reset to English to ensure the data is present
        selected_language = 'English'

    elif button_type == 'dynamic-language':
        selected_language = language_list_data[button_index]
        selected_version = selected_version_data.get('selected_version', None)

    try:
        (
            df_version,
            version_commit,
            version_presets,
            version_accordion_items,
            version_ulist_variable_choices,
            version_multilist_variable_choices
        ) = Language(selected_version,
                     selected_language,
                     initial_load).get_version_language_related_data()
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
        return (dash.no_update,
                dash.no_update,
                dash.no_update,
                dash.no_update,
                dash.no_update,
                dash.no_update,
                False,
                dash.no_update,
                dash.no_update)


def determine_initial_load_boolean(n_clicks_version,
                                   n_clicks_language):
    initial_load = False
    n_clicks_version_unique_values = [click for click in n_clicks_version if pd.notnull(click)]
    n_clicks_language_unique_values = [click for click in n_clicks_language if pd.notnull(click)]
    if not n_clicks_version_unique_values and not n_clicks_language_unique_values:
        initial_load = True
    return initial_load
