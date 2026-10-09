from urllib.parse import parse_qs, urlparse

from bridge.utils.logger import setup_logger

import dash
from dash import Input, Output, State


logger = setup_logger(__name__)


@dash.callback(
    [
        Output("crf_name", "value"),
        Output({"type": "template_check", "index": dash.ALL}, "value"),
    ],
    [
        Input("templates_checks_ready", "data"),
        Input("grouped_presets-store", "data"),
    ],
    [
        State("url", "href"),
    ],
    prevent_initial_call=True,
)
def update_output_based_on_url(
    template_check_flag: bool, grouped_presets: dict, href: str
) -> tuple(list[str], list[list[str]]) | dash._callback.NoUpdate:
    if not template_check_flag:
        return dash.no_update

    if "?param=" in href:
        logger.info(f"grouped_presets={grouped_presets}")
        logger.info(f"Parsing params from href={href}")
        parsed_url = urlparse(href)
        params = parse_qs(parsed_url.query)

        param_value = params.get("param", [""])[0]
        logger.info(
            f"parsed_url={parsed_url}, params={params}, param_value={param_value}"
        )
        mapping = {
            "Recommended%Outcomes_Dengue": "Recommended Outcomes_Dengue",
            "mpox-pregnancy-paediatric": "ARChetype Disease CRF_Mpox Pregnancy and Paediatric",
        }

        param_value = mapping.get(param_value, param_value.replace("-", " "))

        group, value = param_value.split("_") if "_" in param_value else (None, None)
        flattened_grouped_presets = [
            (k, v) for k, values in grouped_presets.items() for v in values
        ]

        checklist_values = [
            [template_name] if (template_id, template_name) == (group, value) else []
            for template_id, template_name in flattened_grouped_presets
        ]

        # Return the value for 'crf_name' and checklist values
        return [value], checklist_values
    else:
        return dash.no_update
