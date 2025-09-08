import dash
from dash import Input, Output, State


class SideBar:

    def __init__(self):
        self.assets_dir = '../../assets'
        self.icons_dir = f'{self.assets_dir}/icons'
        self.settings_on = f"{self.icons_dir}/settings_on.png"
        self.settings_off = f"{self.icons_dir}/settings_off.png"
        self.preset_on = f"{self.icons_dir}/preset_on.png"
        self.preset_off = f"{self.icons_dir}/preset_off.png"

    def register_callbacks(self, app):

        @app.callback(
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
        def toggle_columns(_n_presets, _n_settings, is_in_presets, is_in_settings):
            ctx = dash.callback_context
            button_id = ctx.triggered[0]['prop_id'].split('.')[0]

            # Initialize the state of icons
            preset_icon_img = self.preset_off
            settings_icon_img = self.settings_off

            # Toggle logic
            if button_id == "toggle-settings-2":
                # If settings is open, close it and open presets
                if is_in_settings:
                    new_is_in_presets = True
                    new_is_in_settings = False
                else:
                    # Toggle the state of presets
                    new_is_in_presets = not is_in_presets
                    new_is_in_settings = False

                preset_icon_img = self.preset_on if new_is_in_presets else self.preset_off

            elif button_id == "toggle-settings-1":
                # If presets is open, close it and open settings
                if is_in_presets:
                    new_is_in_settings = True
                    new_is_in_presets = False
                else:
                    # Toggle the state of settings
                    new_is_in_settings = not is_in_settings
                    new_is_in_presets = False

                settings_icon_img = self.settings_on if new_is_in_settings else self.settings_off

            else:
                # Default state if no button is clicked
                new_is_in_presets = is_in_presets
                new_is_in_settings = is_in_settings

            # Determine tree-column visibility
            is_in_tree = not (new_is_in_presets or new_is_in_settings)

            return new_is_in_presets, new_is_in_settings, is_in_tree, settings_icon_img, preset_icon_img

        return app
