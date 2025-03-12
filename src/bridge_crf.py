from urllib.parse import parse_qs, urlparse

import dash
import pandas as pd
from dash import Input, Output, State, ALL

pd.options.mode.copy_on_write = True


class BridgeCrf:
    def __init__(self, grouped_presets):
        self.grouped_presets = grouped_presets

    def add_callbacks(self, app):
        @app.callback(
            [Output('crf_name', 'value'), Output({'type': 'template_check', 'index': ALL}, 'value')],
            [Input('templates_checks_ready', 'data')],
            [State('url', 'href')],
            prevent_initial_call=True,
        )
        def update_output_based_on_url(template_check_flag, href):
            if not template_check_flag:
                return dash.no_update

            if href is None:
                return [''] + [[] for _ in self.grouped_presets.keys()]

            if '?param=' in href:
                # Parse the URL to extract the parameters
                parsed_url = urlparse(href)
                params = parse_qs(parsed_url.query)

                # Accessing the 'param' parameter
                param_value = params.get('param', [''])[0]  # Default to an empty string if the parameter is not present

                # Example: Split param_value by underscore
                group, value = param_value.split('_') if '_' in param_value else (None, None)

                # Prepare the outputs
                checklist_values = {key: [] for key in self.grouped_presets.keys()}

                if group in self.grouped_presets and value in self.grouped_presets[group]:
                    checklist_values[group] = [value]

                # Return the value for 'crf_name' and checklist values
                return [value], [checklist_values[key] for key in self.grouped_presets.keys()]
            else:
                return dash.no_update

        return app
