from typing import Tuple

import dash
from dash import Input, Output, State

from bridge.utils.trigger_id import get_trigger_id

ASSETS_DIR = '../../assets'
ICONS_DIR = f'{ASSETS_DIR}/icons'
SETTINGS_ON = f"{ICONS_DIR}/settings_on.png"
SETTINGS_OFF = f"{ICONS_DIR}/settings_off.png"
PRESET_ON = f"{ICONS_DIR}/preset_on.png"
PRESET_OFF = f"{ICONS_DIR}/preset_off.png"


@dash.callback(
    [
        Output("presets-column", "is_in"),
        Output("settings-column", "is_in"),
        Output("tree-column", 'is_in'),
        Output("settings_icon", "bridge"),
        Output("preset_icon", "bridge")
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

    # Initialize the state of icons
    preset_icon_img = PRESET_OFF
    settings_icon_img = SETTINGS_OFF

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

        preset_icon_img = PRESET_ON if new_is_in_presets else PRESET_OFF

    elif trigger_id == "toggle-settings-1":
        # If presets is open, close it and open settings
        if is_in_presets:
            new_is_in_settings = True
            new_is_in_presets = False
        else:
            # Toggle the state of settings
            new_is_in_settings = not is_in_settings
            new_is_in_presets = False

        settings_icon_img = SETTINGS_ON if new_is_in_settings else SETTINGS_OFF

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
