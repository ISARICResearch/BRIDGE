import json

import dash
import dash_ag_grid as dag
import dash_bootstrap_components as dbc
import dash_treeview_antd
import pandas as pd
from dash import dcc, html, Input, Output, State

from bridge.arc import arc
from bridge.arc.arc_api import ArcApiClient
from bridge.layout.modals import Modals

pd.options.mode.copy_on_write = True

ASSETS_DIR = '../../assets'
ICONS_DIR = f'{ASSETS_DIR}/icons'
LOGOS_DIR = f'{ASSETS_DIR}/logos'

# TODO: Should these be global vars?
# Global variables
ARC_VERSION_LIST, ARC_VERSION_LATEST = arc.get_arc_versions()
ARC_LANGUAGE_LIST_INITIAL = ArcApiClient().get_arc_language_list_version(ARC_VERSION_LATEST)
ARC_LANGUAGE_INITIAL = 'English'

CURRENT_DATADICC, PRESETS, COMMIT = arc.get_arc(ARC_VERSION_LATEST)
CURRENT_DATADICC = arc.add_required_datadicc_columns(CURRENT_DATADICC)

TREE_ITEMS_DATA = arc.get_tree_items(CURRENT_DATADICC, ARC_VERSION_LATEST)

# List content Transformation
ARC_LISTS, LIST_VARIABLE_CHOICES = arc.get_list_content(CURRENT_DATADICC, ARC_VERSION_LATEST, ARC_LANGUAGE_INITIAL)
CURRENT_DATADICC = arc.add_transformed_rows(CURRENT_DATADICC, ARC_LISTS, arc.get_variable_order(CURRENT_DATADICC))

# User List content Transformation
ARC_ULIST, ULIST_VARIABLE_CHOICES = arc.get_user_list_content(CURRENT_DATADICC, ARC_VERSION_LATEST,
                                                              ARC_LANGUAGE_INITIAL)
CURRENT_DATADICC = arc.add_transformed_rows(CURRENT_DATADICC, ARC_ULIST, arc.get_variable_order(CURRENT_DATADICC))

ARC_MULTILIST, MULTILIST_VARIABLE_CHOICES = arc.get_multu_list_content(CURRENT_DATADICC, ARC_VERSION_LATEST,
                                                                       ARC_LANGUAGE_INITIAL)
CURRENT_DATADICC = arc.add_transformed_rows(CURRENT_DATADICC, ARC_MULTILIST,
                                            arc.get_variable_order(CURRENT_DATADICC))

INITIAL_CURRENT_DATADICC = CURRENT_DATADICC.to_json(date_format='iso', orient='split')
INITIAL_ULIST_VARIABLE_CHOICES = json.dumps(ULIST_VARIABLE_CHOICES)
INITIAL_MULTILIST_VARIABLE_CHOICES = json.dumps(MULTILIST_VARIABLE_CHOICES)

# Grouping presets by the first column
GROUPED_PRESETS = {}

for key, value in PRESETS:
    GROUPED_PRESETS.setdefault(key, []).append(value)

INITIAL_GROUPED_PRESETS = json.dumps(GROUPED_PRESETS)


def define_app_layout():
    app_layout = html.Div(
        [
            dcc.Store(id='current_datadicc-store', data=INITIAL_CURRENT_DATADICC),
            dcc.Store(id='ulist_variable_choices-store', data=INITIAL_ULIST_VARIABLE_CHOICES),
            dcc.Store(id='multilist_variable_choices-store', data=INITIAL_MULTILIST_VARIABLE_CHOICES),
            dcc.Store(id='grouped_presets-store', data=INITIAL_GROUPED_PRESETS),
            dcc.Store(id='tree_items_data-store', data=INITIAL_GROUPED_PRESETS),

            dcc.Store(id='templates_checks_ready', data=False),

            dcc.Location(id='url', refresh=False),
            html.Div(id='page-content'),
            dcc.Download(id="download-dataframe-csv"),
            dcc.Download(id='download-compGuide-pdf'),
            dcc.Download(id='download-projectxml-pdf'),
            dcc.Download(id='download-paperlike-pdf'),
            dcc.Download(id='save-crf'),
            Modals.variable_information_modal(),
            Modals.research_questions_modal(),
            dcc.Loading(id="loading-generate",
                        type="default",
                        children=html.Div(id="loading-output-generate"),
                        ),
            dcc.Loading(id="loading-save",
                        type="default",
                        children=html.Div(id="loading-output-save"),
                        ),
            dcc.Store(id='commit-store'),
            dcc.Store(id='selected_data-store'),
            dcc.Store(id='language-list-store', data=ARC_LANGUAGE_LIST_INITIAL),
            dcc.Store(id='upload-version-store'),
            dcc.Store(id='upload-language-store'),
            dcc.Store(id='upload-crf-ready', data=False),
            dcc.Store(id="browser-info-store"),

            dcc.Interval(id="interval-browser", interval=500, n_intervals=0, max_intervals=1),
        ]
    )
    return app_layout


def main_app():
    return html.Div([
        NavBar.navbar,
        SideBar.sidebar,
        dcc.Loading(
            id="loading-overlay",
            type="circle",  # Spinner style: 'default', 'circle', 'dot'
            fullscreen=True,  # Covers the full screen
            children=[
                Settings(ARC_VERSION_LIST, ARC_LANGUAGE_LIST_INITIAL, ARC_VERSION_LATEST,
                         ARC_LANGUAGE_INITIAL).settings_column,
                Presets.preset_column,
                TreeItems(TREE_ITEMS_DATA).tree_column,
                MainContent.main_content,
            ],
            delay_show=1200,
        ),
    ])


# TODO: Put these in different files?
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
            columnSize="responsiveSizeToFit",
            dashGridOptions={
                "rowDragManaged": True,
                "rowDragEntireRow": True,
                "rowDragMultiRow": True,
                "rowSelection": "multiple",
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
            'height': '67vh',  # Fixed height
            'width': '100%',  # Fixed width, or you can specify a value in px
            'white-space': 'normal',  # Allow text to wrap
            'overflow-x': 'hidden',  # Hide overflowed content
            'text-overflow': 'ellipsis',  # Indicate more content with an ellipsis
        }
    )

    main_content = dbc.Container(
        [
            dbc.Row(
                [
                    dbc.Col([html.Div(),
                             html.Div(id='output-expanded', style={'display': 'none'})], width=5),  # 45% width
                    dbc.Col(
                        [
                            dbc.Row([html.Div(),
                                     grid]),
                            html.Br(),
                            dbc.Row(
                                [
                                    dbc.Col(dbc.Input(placeholder="CRF Name", type="text", id='crf_name'), width=5),
                                    dbc.Col(dbc.Button("Generate", color="primary", id='crf_generate'), width=2),
                                    dbc.Col(dbc.Button("Save Template", color="primary", id='crf_save'), width=3),
                                ],
                                style={"height": "8%"},
                            ),
                            dbc.Row(
                                [
                                    dbc.Col(dbc.Button("Upload Template", color="secondary", disabled=True), width=2),
                                    dbc.Col(dcc.Upload(
                                        id='upload-crf',
                                        children=html.Div([
                                            'Drag and Drop or ',
                                            html.A('Select File')
                                        ]),
                                        style={
                                            'width': '100%',
                                            'height': '60px',
                                            'lineHeight': '60px',
                                            'borderWidth': '1px',
                                            'borderStyle': 'dashed',
                                            'borderRadius': '5px',
                                            'textAlign': 'center',
                                        },
                                    ), ),
                                ],
                                style={"height": "10%"}
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
        style={
            "margin-top": "1rem",
            "margin-bottom": "1rem",
            "margin-left": "1rem",
            "margin-right": "1rem",
            "width": "98vw",
        }
        # Adjust margin to accommodate navbar and sidebar
    )


class NavBar:
    navbar = dbc.Navbar(
        dbc.Container(
            [
                html.A(
                    dbc.Row(
                        [
                            dbc.Col(html.Img(src=f"{LOGOS_DIR}/ISARIC_logo_wh.png", height="60px")),
                        ],
                        align="center",
                        className="g-0 me-auto",
                    ),
                    href="https://isaric.org/",
                    style={"textDecoration": "none"},
                ),
                html.A(
                    dbc.NavbarBrand(
                        "BRIDGE - BioResearch Integrated Data tool GEnerator",
                        className="mx-auto"
                    ),
                    href="https://isaric-bridge.replit.app/",
                    style={"textDecoration": "none", "color": "white"},
                ),

                html.A(
                    dbc.NavbarBrand("Getting started with BRIDGE"),
                    href="https://isaricresearch.github.io/Training/bridge_starting.html",
                    style={"textDecoration": "none", "color": "white"},
                ),
                dbc.NavbarToggler(id="navbar-toggler", n_clicks=0),
            ],
            className="d-flex justify-content-between w-100"
        ),
        color="#BA0225",
        dark=True,
        className="px-3",
    )


class SideBar:
    sidebar = html.Div(
        [
            dbc.NavLink(html.Img(src=f"{ICONS_DIR}/Settings_off.png", style={'width': '40px'}, id='settings_icon'),
                        id="toggle-settings-1", n_clicks=0),
            dbc.NavLink(html.Img(src=f"{ICONS_DIR}/preset_off.png", style={'width': '40px'}, id='preset_icon'),
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
            # "z-index": 2000
        }
    )

    @staticmethod
    def register_callbacks(app):

        @app.callback(
            [Output("presets-column", "is_in"),
             Output("settings-column", "is_in"),
             Output("tree-column", 'is_in'),
             Output("settings_icon", "bridge"),
             Output("preset_icon", "bridge")],
            [Input("toggle-settings-2", "n_clicks"),
             Input("toggle-settings-1", "n_clicks")],
            [State("presets-column", "is_in"),
             State("settings-column", "is_in")],
            prevent_initial_call=True
        )
        def toggle_columns(_n_presets, _n_settings, is_in_presets, is_in_settings):
            ctx = dash.callback_context
            button_id = ctx.triggered[0]['prop_id'].split('.')[0]

            # Initialize the state of icons
            preset_icon_img = f"{ICONS_DIR}/preset_off.png"
            settings_icon_img = f"{ICONS_DIR}/Settings_off.png"

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

                preset_icon_img = f"{ICONS_DIR}/preset_on.png" if new_is_in_presets else f"{ICONS_DIR}/preset_off.png"

            elif button_id == "toggle-settings-1":
                # If presets is open, close it and open settings
                if is_in_presets:
                    new_is_in_settings = True
                    new_is_in_presets = False
                else:
                    # Toggle the state of settings
                    new_is_in_settings = not is_in_settings
                    new_is_in_presets = False

                settings_icon_img = f"{ICONS_DIR}/Settings_on.png" if new_is_in_settings else f"{ICONS_DIR}/Settings_off.png"

            else:
                # Default state if no button is clicked
                new_is_in_presets = is_in_presets
                new_is_in_settings = is_in_settings

            # Determine tree-column visibility
            is_in_tree = not (new_is_in_presets or new_is_in_settings)

            return new_is_in_presets, new_is_in_settings, is_in_tree, settings_icon_img, preset_icon_img

        return app


class Settings:
    def __init__(self, arc_versions, arc_languages, version, language):
        self.arc_versions = arc_versions
        self.arc_languages = arc_languages

        self.version = version
        self.language = language

        self.arc_versions_items = [dbc.DropdownMenuItem(version, id={"type": "dynamic-version", "index": i}) for
                                   i, version in enumerate(self.arc_versions)]
        self.arc_language_items = [dbc.DropdownMenuItem(language, id={"type": "dynamic-language", "index": i}) for
                                   i, language in enumerate(self.arc_languages)]

        self.settings_content = html.Div(
            [
                html.H3("Settings", id="settings-text-2"),

                html.Div([
                    dbc.InputGroup([
                        dbc.DropdownMenu(
                            label="ARC Version",
                            children=self.arc_versions_items,
                            id="dropdown-ARC-version-menu",
                        ),
                        dbc.Input(id="dropdown-ARC_version_input", value=self.version)
                    ]),
                    dcc.Store(id='selected-version-store'),
                    dcc.Store(id='selected_data-store'),
                ], style={'margin-bottom': '20px'}),

                html.Div([
                    dbc.InputGroup([
                        dbc.DropdownMenu(
                            label="Language",
                            children=self.arc_language_items,
                            id="dropdown-ARC-language-menu",
                        ),
                        dbc.Input(id="dropdown-ARC_language_input", value=self.language)
                    ]),
                    dcc.Store(id='selected-language-store'),
                ], style={'margin-bottom': '20px'}),

                html.Div([
                    html.Label("Output Files", htmlFor="output-files-checkboxes"),
                    dbc.Checklist(
                        id="output-files-checkboxes",
                        options=[
                            {'label': 'ISARIC Clinical Characterization XML', 'value': 'redcap_xml'},
                            {'label': 'REDCap Data Dictionary', 'value': 'redcap_csv'},
                            {'label': 'Paper-like CRF and Completion Guide', 'value': 'paper_like'},
                        ],
                        value=['redcap_xml', 'redcap_csv', 'paper_like'],
                        inline=True
                    )
                ], style={'margin-bottom': '20px'}),

                dcc.Store(id="output-files-store")
            ],
            style={"padding": "2rem"}
        )

        self.settings_column = dbc.Fade(
            self.settings_content,
            id="settings-column",
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


class Presets:
    preset_column = dbc.Fade(
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


class TreeItems:
    def __init__(self, tree_items_data):
        self.tree_items_data = tree_items_data

        self.tree_items = html.Div(
            dash_treeview_antd.TreeView(
                id='input',
                multiple=False,
                checkable=True,
                checked=[],
                data=self.tree_items_data),
            id='tree_items_container',
            className='tree-item',
        )

        self.tree_column = dbc.Fade(
            self.tree_items,
            id="tree-column",
            is_in=True,  # Initially show
            style={
                "position": "fixed",
                "left": "4rem",
                "width": "33rem",
                "height": "90%",
            }
        )
