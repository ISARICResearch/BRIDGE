import dash_bootstrap_components as dbc
import dash_treeview_antd
from dash import dcc, html

from bridge.layout.grid import Grid
from bridge.layout.modals import Modals


class MainContent:
    def __init__(self, tree_items_data):
        self.tree_items_data = tree_items_data

        self.tree_items = html.Div(
            dash_treeview_antd.TreeView(
                id="input",
                multiple=False,
                checkable=True,
                checked=[],
                data=self.tree_items_data,
            ),
            id="tree_items_container",
            className="tree-item",
        )

        self.main_content = dbc.Container(
            [
                dbc.Row(
                    [
                        dbc.Col(
                            [
                                html.Div(
                                    id="output-expanded", style={"display": "none"}
                                ),
                                dbc.Fade(
                                    self.tree_items,
                                    id="tree-column",
                                    is_in=True,  # Initially show
                                    style={
                                        "position": "fixed",
                                        "left": "4rem",
                                        "width": "35%",
                                        "height": "95%",
                                    },
                                ),
                            ],
                            width=5,
                        ),
                        dbc.Col(
                            [
                                dbc.Row(html.Div(), style={"height": "1rem"}),
                                dbc.Row(Grid().grid),
                                html.Br(),
                                dbc.Row(
                                    [
                                        dbc.Col(
                                            dbc.Input(
                                                placeholder="CRF Name",
                                                type="text",
                                                id="crf_name",
                                            ),
                                        ),
                                        dbc.Col(
                                            dbc.Button(
                                                "Generate",
                                                color="primary",
                                                id="crf_generate",
                                            ),
                                            width="auto",
                                        ),
                                        dbc.Col(
                                            dbc.Button(
                                                "Save Template",
                                                color="primary",
                                                id="crf_save",
                                            ),
                                            width="auto",
                                        ),
                                        dbc.Col(
                                            dcc.Upload(
                                                dbc.Button(
                                                    "Upload Template",
                                                    color="primary",
                                                ),
                                                id="upload-crf",
                                            ),
                                            width="auto",
                                        ),
                                    ],
                                ),
                                dbc.Row(html.Div(), style={"height": "1rem"}),
                                dbc.Row(
                                    dbc.Col(
                                        [
                                            "BRIDGE is being developed by ISARIC. For inquiries, support, or collaboration, please write to: ",
                                            html.A(
                                                "data@isaric.org",
                                                href="mailto:data@isaric.org",
                                            ),
                                            ". ",
                                            "Licensed under a ",
                                            html.A(
                                                "Creative Commons Attribution-ShareAlike 4.0 ",
                                                href="https://creativecommons.org/licenses/by-sa/4.0/",
                                                target="_blank",
                                            ),
                                            "International License by ",
                                            html.A(
                                                "ISARIC",
                                                href="https://isaric.org/",
                                                target="_blank",
                                            ),
                                            " on behalf of Oxford University.",
                                        ],
                                    )
                                ),
                            ],
                            width=7,
                        ),
                    ],
                ),
            ],
            fluid=True,
            style={
                "width": "98vw",
            },
        )

    @staticmethod
    def define_app_layout(
        arc_json,
        ulist_variable_json,
        multilist_variable_json,
        grouped_presets_json,
        arc_language_list,
    ):
        app_layout = html.Div(
            [
                dcc.Store(id="current_datadicc-store", data=arc_json),
                dcc.Store(id="ulist_variable_choices-store", data=ulist_variable_json),
                dcc.Store(
                    id="multilist_variable_choices-store", data=multilist_variable_json
                ),
                dcc.Store(id="grouped_presets-store", data=grouped_presets_json),
                dcc.Store(id="tree_items_data-store", data=grouped_presets_json),
                dcc.Store(id="templates_checks_ready", data=False),
                dcc.Location(id="url", refresh=False),
                html.Div(id="page-content"),
                dcc.Download(id="download-dataframe-csv"),
                dcc.Download(id="download-compGuide-pdf"),
                dcc.Download(id="download-projectxml-pdf"),
                dcc.Download(id="download-paperlike-pdf"),
                dcc.Download(id="download-paperlike-docx"),
                dcc.Download(id="save-crf"),
                Modals.variable_information_modal(),
                dcc.Loading(
                    id="loading-generate",
                    type="default",
                    children=html.Div(id="loading-output-generate"),
                ),
                dcc.Loading(
                    id="loading-save",
                    type="default",
                    children=html.Div(id="loading-output-save"),
                ),
                dcc.Store(id="commit-store"),
                dcc.Store(id="selected_data-store"),
                dcc.Store(id="language-list-store", data=arc_language_list),
                dcc.Store(id="upload-version-store"),
                dcc.Store(id="upload-language-store"),
                dcc.Store(id="upload-crf-ready", data=False),
                dcc.Store(id="browser-info-store"),
                dcc.Interval(
                    id="interval-browser", interval=500, n_intervals=0, max_intervals=1
                ),
                dcc.Store(id="focused-cell-index"),
                dcc.Store(id="focused-cell-run-callback", data=False),
            ]
        )
        return app_layout
