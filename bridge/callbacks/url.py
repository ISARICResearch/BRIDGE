from urllib.parse import parse_qs, urlparse

import dash
from dash import Input, Output, State


@dash.callback(
    [
        Output('crf_name', 'value'),
        Output({'type': 'template_check', 'index': dash.ALL}, 'value'),
    ],
    [
        Input('templates_checks_ready', 'data'),
        Input('grouped_presets-store', 'data'),
    ],
    [
        State('url', 'href'),
    ],
    prevent_initial_call=True,
)
def update_output_based_on_url(template_check_flag: bool,
                               grouped_presets: dict,
                               href: str):
    if not template_check_flag:
        return dash.no_update

    if '?param=' in href:
        parsed_url = urlparse(href)
        params = parse_qs(parsed_url.query)

        param_value = params.get('param', [''])[0]
        
        mapping = {
                "Recommended%Outcomes_Dengue": "Recommended Outcomes_Dengue",
                "mpox-pregnancy-paediatric": "ARChetype Disease CRF_Mpox Pregnancy and Paediatrics",
            }

        param_value = mapping.get(
            param_value,
            param_value.replace("-", " ")
        )

             
        group, value = param_value.split('_') if '_' in param_value else (None, None)

        checklist_values = {key: [] for key in grouped_presets.keys()}

        if group in grouped_presets and value in grouped_presets[group]:
            checklist_values[group] = [value]

        # Return the value for 'crf_name' and checklist values
        return [value], [checklist_values[key] for key in grouped_presets.keys()]
    else:
        return dash.no_update
