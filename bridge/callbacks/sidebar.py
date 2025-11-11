from typing import Tuple

import dash
from dash import Input, Output, State

from bridge.utils.trigger_id import get_trigger_id


@dash.callback(
    [
        Output("presets-column", "is_in"),
        Output("settings-column", "is_in"),
        Output("tree-column", 'is_in'),
        Output("settings_icon", "src"),
        Output("preset_icon", "src")
    ],
    [
        Input("toggle-settings-2", "n_clicks"),
        Input("toggle-settings-1", "n_clicks")
    ],
    [
        State("presets-column", "is_in"),
        State("settings-column", "is_in")
    ],
    prevent_initial_call=True
)
def toggle_columns(_n_presets: int,
                   _n_settings: int,
                   is_in_presets: bool,
                   is_in_settings: bool) -> Tuple[bool, bool, bool, str, str]:
    ctx = dash.callback_context

    trigger_id = get_trigger_id(ctx)

    settings_on = dash.get_asset_url('settings_on.png')
    settings_off = dash.get_asset_url('settings_off.png')
    preset_on = dash.get_asset_url('preset_on.png')
    preset_off = dash.get_asset_url('preset_off.png')

    # Initialize the state of icons
    preset_icon_img = preset_off
    settings_icon_img = settings_off

    # Toggle logic
    if trigger_id == "toggle-settings-2":
        # If settings is open, close it and open presets
        if is_in_settings:
            new_is_in_presets = True
            new_is_in_settings = False
        else:
            # Toggle the state of presets
            new_is_in_presets = not is_in_presets
            new_is_in_settings = False

        preset_icon_img = preset_on if new_is_in_presets else preset_off

    elif trigger_id == "toggle-settings-1":
        # If presets is open, close it and open settings
        if is_in_presets:
            new_is_in_settings = True
            new_is_in_presets = False
        else:
            # Toggle the state of settings
            new_is_in_settings = not is_in_settings
            new_is_in_presets = False

        settings_icon_img = settings_on if new_is_in_settings else settings_off

    else:
        # Default state if no button is clicked
        new_is_in_presets = is_in_presets
        new_is_in_settings = is_in_settings

    # Determine tree-column visibility
    is_in_tree = not (new_is_in_presets or new_is_in_settings)

    return (new_is_in_presets,
            new_is_in_settings,
            is_in_tree,
            settings_icon_img,
            preset_icon_img)
