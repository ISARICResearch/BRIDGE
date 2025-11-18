import dash_bootstrap_components as dbc
from dash import dcc, html

from bridge.logging.logger import setup_logger

logger = setup_logger(__name__)


class Settings:

    def __init__(self, arc_version_list, arc_language_list, version, language):
        self.arc_version_list = arc_version_list
        self.arc_language_list = arc_language_list

        self.version = version
        self.language = language

        self.arc_versions_items = [dbc.DropdownMenuItem(version, id={"type": "dynamic-version", "index": i}) for
                                   i, version in enumerate(self.arc_version_list)]
        self.arc_language_items = [dbc.DropdownMenuItem(language, id={"type": "dynamic-language", "index": i}) for
                                   i, language in enumerate(self.arc_language_list)]

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
                            {'label': 'Paper-like CRF (PDF + Guide)', 'value': 'paper_like'},
                            {'label': 'CRF Review Word Document', 'value': 'paper_word'},   
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
