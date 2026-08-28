import dash_bootstrap_components as dbc
from dash import html, dcc


class Modals:
    @staticmethod
    def variable_information_modal():
        return dbc.Modal(
            [
                dbc.ModalHeader(dbc.ModalTitle("Row Details", id="modal_title")),
                dbc.ModalBody(
                    [
                        html.H5("Definition:"),
                        html.P("Your definition text here", id="definition-text"),
                        html.H5("Options:"),
                        dbc.Checklist(
                            options=[
                                {"label": "Option 1", "value": 1},
                                {"label": "Option 2", "value": 2},
                            ],
                            id="options-checklist",
                            value=[1],
                        ),
                        dbc.ListGroup(
                            [
                                dbc.ListGroupItem("Item 1"),
                                dbc.ListGroupItem("Item 2"),
                            ],
                            id="options-list-group",
                            style={"display": "none"},
                        ),
                        html.Br(),
                        html.H5("Completion Guide:"),
                        html.P(
                            "Completion guide text here", id="completion-guide-text"
                        ),
                        html.H5("Skip logic:"),
                        html.P("Skip logic here", id="skip-logic-text"),
                    ]
                ),
                dbc.ModalFooter(
                    html.Div(
                        [
                            dbc.Button(
                                "Submit",
                                id="modal_submit",
                                className="me-1",
                                n_clicks=0,
                            ),
                            dbc.Button(
                                "Cancel",
                                id="modal_cancel",
                                className="me-1",
                                n_clicks=0,
                            ),
                        ]
                    )
                ),
            ],
            id="modal",
            is_open=False,
            size="xl",
        )

    @staticmethod
    def crf_metadata_modal():
        """Modal for displaying CRF template metadata."""
        return dbc.Modal(
            [
                dbc.ModalHeader(
                    dbc.ModalTitle("CRF Metadata", id="crf_metadata_modal_title")
                ),
                dbc.ModalBody(
                    [
                        html.Div(
                            [
                                html.H1(""),
                                dcc.Tabs(
                                    id="crf-metadata-modal-tabbed-body",
                                    value="project-overview-tab",
                                    children=[
                                        dcc.Tab(
                                            label="Project Overview",
                                            value="project-overview-tab",
                                        ),
                                        dcc.Tab(
                                            label="Scientific Scope",
                                            value="scientific-scope-tab",
                                        ),
                                        dcc.Tab(
                                            label="Governance & Contributors",
                                            value="governance-and-contributors-tab",
                                        ),
                                        dcc.Tab(
                                            label="Documentation & Discoverability",
                                            value="documentation-and-discoverability-tab",
                                        ),
                                    ],
                                ),
                                html.Div(
                                    id="crf-metadata-modal-body-tab-content",
                                    style={
                                        "width": "800px",
                                        "height": "250px",
                                        "overflow-x": "hidden",
                                        "white-space": "normal",
                                    },
                                ),
                            ],
                            id="crf_metadata_modal_body",
                        )
                    ],
                ),
                dbc.ModalFooter(
                    dbc.Button(
                        "Close",
                        id="crf_metadata_modal_close",
                        className="ms-auto",
                        n_clicks=0,
                    )
                ),
            ],
            id="crf_metadata_modal",
            is_open=False,
            size="lg",
            scrollable=True,
        )
