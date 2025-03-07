import dash
import dash_ag_grid as dag
import dash_bootstrap_components as dbc
import pandas as pd
from dash import html, Input, Output, State

pd.options.mode.copy_on_write = True

assets_dir = '../assets'
icons_dir = f'{assets_dir}/icons'
logos_dir = f'{assets_dir}/logos'
screenshots_dir = f'{assets_dir}/screenshots'


class MainContent:
    column_defs = [{'headerName': "Question", 'field': "Question", 'wrapText': True},
                   {'headerName': "Answer Options", 'field': "Answer Options", 'wrapText': True}]

    row_data = [{'question': "", 'options': ""},
                {'question': "", 'options': ""}]

    grid = html.Div(
        dag.AgGrid(
            id='CRF_representation_grid',
            columnDefs=column_defs,
            rowData=row_data,
            defaultColDef={"sortable": True, "filter": True, 'resizable': True},
            columnSize="sizeToFit",
            dashGridOptions={
                "rowDragManaged": True,
                "rowDragEntireRow": True,
                "rowDragMultiRow": True, "rowSelection": "multiple",
                "suppressMoveWhenRowDragging": True,
                "autoHeight": True
            },
            rowClassRules={
                "form-separator-row ": 'params.data.SeparatorType == "form"',
                'section-separator-row': 'params.data.SeparatorType == "section"',
            },
            style={
                'overflow-y': 'auto',  # Vertical scrollbar when needed
                'height': '99%',  # Fixed height
                'width': '100%',  # Fixed width, or you can specify a value in px
                'white-space': 'normal',  # Allow text to wrap
                'overflow-x': 'hidden',  # Hide overflowed content

            }

        ),
        style={
            'overflow-y': 'auto',  # Vertical scrollbar when needed
            'height': '75vh',  # Fixed height
            'width': '100%',  # Fixed width, or you can specify a value in px
            'white-space': 'normal',  # Allow text to wrap
            'overflow-x': 'hidden',  # Hide overflowed content
            'text-overflow': 'ellipsis'  # Indicate more content with an ellipsis

        }
    )

    main_content = dbc.Container(
        [
            dbc.Row(
                [
                    dbc.Col([html.Div(),

                             # tree_items,

                             html.Div(id='output-expanded', style={'display': 'none'})
                             ]

                            , width=5),  # 45% width
                    dbc.Col(
                        [
                            dbc.Row([html.Div(),
                                     grid]),  # 90% height
                            dbc.Row(
                                [
                                    dbc.Col(dbc.Input(placeholder="CRF Name", type="text", id='crf_name')),
                                    dbc.Col(dbc.Button("Generate", color="primary", id='crf_generate'))
                                ],
                                style={"height": "10%"}  # Remaining height for input and button
                            ),
                            dbc.Row(html.Div([
                                "BRIDGE is being developed by ISARIC. For inquiries, support, or collaboration, please write to: ",
                                html.A("data@isaric.org", href="mailto:data@isaric.org"), ". ",
                                "Licensed under a ",
                                html.A("Creative Commons Attribution-ShareAlike 4.0 ",
                                       href="https://creativecommons.org/licenses/by-sa/4.0/",
                                       target="_blank"),
                                "International License by ",
                                html.A("ISARIC", href="https://isaric.org/", target="_blank"),
                                " on behalf of Oxford University."]))
                        ],
                        width=7  # 55% width
                    )
                ]
            )
        ],
        fluid=True,
        style={"margin-top": "4rem", "margin-left": "4rem", "z-index": 1, "width": "90vw"}
        # Adjust margin to accommodate navbar and sidebar
    )


class NavBar:
    navbar = dbc.Navbar(
        dbc.Container(
            [
                html.A(
                    # Use row and col to control vertical alignment of logo / brand
                    dbc.Row(
                        [
                            dbc.Col(html.Img(src=f"{logos_dir}/ISARIC_logo_wh.png", height="60px")),
                            dbc.Col(
                                dbc.NavbarBrand("BRIDGE - BioResearch Integrated Data tool GEnerator",
                                                className="ms-2")),
                        ],
                        align="center",
                        className="g-0",
                    ),
                    href="https://isaric.org/",
                    style={"textDecoration": "none"},
                ),
                dbc.NavbarToggler(id="navbar-toggler", n_clicks=0),
            ]
        ),
        color="#BA0225",
        dark=True,
    )


class SideBar:
    # Sidebar with icons
    sidebar = html.Div(
        [
            dbc.NavLink(html.Img(src=f"{icons_dir}/Settings_off.png", style={'width': '40px'}, id='settings_icon'),
                        id="toggle-settings-1", n_clicks=0),
            dbc.NavLink(html.Img(src=f"{icons_dir}/preset_off.png", style={'width': '40px'}, id='preset_icon'),
                        id="toggle-settings-2", n_clicks=0),

        ],
        style={
            "position": "fixed",
            "top": "5rem",  # Height of the navbar
            "left": 0,
            "bottom": 0,
            "width": "4rem",
            "padding": "2rem 1rem",
            "background-color": "#dddddd",
            "display": "flex",
            "flexDirection": "column",
            "alignItems": "center",
            # "z-index": 2000
        }
    )

    @staticmethod
    def add_sidebar(app):
        @app.callback(
            [Output("presets-column", "is_in"),
             Output("settings-column", "is_in"),
             Output("tree-column", 'is_in'),
             Output("settings_icon", "src"),
             Output("preset_icon", "src")],
            [Input("toggle-settings-2", "n_clicks"),
             Input("toggle-settings-1", "n_clicks")],
            [State("presets-column", "is_in"),
             State("settings-column", "is_in")],
            prevent_initial_call=True
        )
        def toggle_columns(n_presets, n_settings, is_in_presets, is_in_settings):
            ctx = dash.callback_context
            button_id = ctx.triggered[0]['prop_id'].split('.')[0]

            # Initialize the state of icons
            preset_icon_img = f"{icons_dir}/preset_off.png"
            settings_icon_img = f"{icons_dir}/Settings_off.png"

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

                preset_icon_img = f"{icons_dir}/preset_on.png" if new_is_in_presets else f"{icons_dir}/preset_off.png"

            elif button_id == "toggle-settings-1":
                # If presets is open, close it and open settings
                if is_in_presets:
                    new_is_in_settings = True
                    new_is_in_presets = False
                else:
                    # Toggle the state of settings
                    new_is_in_settings = not is_in_settings
                    new_is_in_presets = False

                settings_icon_img = f"{icons_dir}/Settings_on.png" if new_is_in_settings else f"{icons_dir}/Settings_off.png"

            else:
                # Default state if no button is clicked
                new_is_in_presets = is_in_presets
                new_is_in_settings = is_in_settings

            # Determine tree-column visibility
            is_in_tree = not (new_is_in_presets or new_is_in_settings)

            return new_is_in_presets, new_is_in_settings, is_in_tree, settings_icon_img, preset_icon_img

        return app
