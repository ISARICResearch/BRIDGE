import dash_bootstrap_components as dbc
from dash import html


class SideBar:

    def __init__(self):
        self.assets_dir = '../../assets'
        self.icons_dir = f'{self.assets_dir}/icons'
        self.settings_off = f"{self.icons_dir}/settings_off.png"
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
