import dash
import dash_bootstrap_components as dbc
from dash import Input, Output

from bridge.arc.arc_api import ArcApiClient


class Dropdowns:

    @staticmethod
    def register_callbacks(app):

        @app.callback(
            Output("dropdown-ARC_version_input", "value"),
            [
                Input('selected-version-store', 'data')
            ]
        )
        def update_input_version(data):
            if data is None:
                return dash.no_update
            return data.get('selected_version')

        @app.callback(
            Output("dropdown-ARC_language_input", "value"),
            [
                Input('selected-language-store', 'data')
            ]
        )
        def update_input_language(data):
            if data is None:
                return dash.no_update
            return data.get('selected_language')

        @app.callback(
            Output("dropdown-ARC-language-menu", "children"),
            Output("language-list-store", "data"),
            [
                Input('selected-version-store', 'data'),
            ],
        )
        def update_language_dropdown(selected_version_data):
            if not selected_version_data:
                return dash.no_update, dash.no_update

            current_version = selected_version_data.get('selected_version', None)
            arc_languages = ArcApiClient().get_arc_language_list_version(current_version)
            arc_language_items = [dbc.DropdownMenuItem(language, id={"type": "dynamic-language", "index": i}) for
                                  i, language in enumerate(arc_languages)]
            return arc_language_items, arc_languages

        return app
