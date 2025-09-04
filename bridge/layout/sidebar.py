import dash
import dash_bootstrap_components as dbc
from dash import html, Input, Output, State


class SideBar:

    def __init__(self):
        self.assets_dir = '../../assets'
        self.icons_dir = f'{self.assets_dir}/icons'
        self.settings_on = f"{self.icons_dir}/settings_on.png"
        self.settings_off = f"{self.icons_dir}/settings_off.png"
        self.preset_on = f"{self.icons_dir}/preset_on.png"
        self.preset_off = f"{self.icons_dir}/preset_off.png"

        self.sidebar = html.Div(
            [
                dbc.NavLink(html.Img(src=self.settings_off, style={'width': '40px'}, id='settings_icon'),
                            id="toggle-settings-1", n_clicks=0),
                dbc.NavLink(html.Img(src=self.preset_off, style={'width': '40px'}, id='preset_icon'),
                            id="toggle-settings-2", n_clicks=0),

            ],
            style={
                "position": "fixed",
                "top": "4.75rem",  # Height of the navbar
                "left": 0,
                "bottom": 0,
                "width": "4rem",
                "padding": "2rem 1rem",
                "background-color": "#dddddd",
                "display": "flex",
                "flexDirection": "column",
                "alignItems": "center",
            }
        )

        self.preset_column = dbc.Fade(
            html.Div(
                [
                    html.H3("Templates", id="settings-text-1"),
                    dbc.Accordion(id='preset-accordion')  # ID to be updated dynamically
                ],
                style={"padding": "2rem"}
            ),
            id="presets-column",
            is_in=False,  # Initially hidden
            style={
                "position": "fixed",
                "top": "4.75rem",  # Height of the navbar
                "left": "4rem",
                "bottom": 0,
                "width": "20rem",
                "background-color": "#dddddd",
                "z-index": 2001
            }
        )

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
