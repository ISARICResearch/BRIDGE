import dash
import dash_bootstrap_components as dbc
from dash import html


FEATURE_CARDS = [
    {
        "title": "Choose",
        "image": "images/card1.png",
        "body": [
            "BRIDGE uses the machine-readable library ",
            html.A("ARC", href="https://example.com", target="_blank"),
            " and allows the user to choose the questions they want to include in the CRF. ",
            "BRIDGE presents ARC as a tree structure with different levels: ARC version, forms, sections, and questions. Users navigate through this tree and select the questions they want to include in the CRF.",
            html.Br(),
            html.Br(),
            "Additionally, users can start with one of our Presets, which are pre-selected groups of questions. They can click on the Pre-sets tab and select those they want to include in the CRF. All selected questions can be customized.",
        ],
    },
    {
        "title": "Customize",
        "image": "images/card2.png",
        "body": [
            "BRIDGE allows customization of CRFs from chosen questions, as well as selection of measurement units and answer options where pertinent. ",
            "Users click the relevant question, and a checkable list appears with options for the site or disease being researched.",
            html.Br(),
            html.Br(),
            "This feature ensures that the CRF is tailored to specific needs, enhancing the precision and relevance of the data collected.",
        ],
    },
    {
        "title": "Capture",
        "image": "images/card3.png",
        "body": [
            "BRIDGE generates files for creating databases within REDCap, including the data dictionary and XML needed to create a REDCap database for capturing data in the ARC structure. ",
            "It also produces paper-like versions of the CRFs and completion guides. ",
            html.Br(),
            html.Br(),
            "Once users are satisfied with their selections, they can name the CRF and click on generate to finalize the process, ensuring a seamless transition to data collection.",
        ],
    },
]

PARTNER_ROWS = [
    [
        "images/FIOCRUZ_logo.png",
        "images/global_health.png",
        "images/puc_rio.png",
    ],
    [
        "images/CONTAGIO_Logo.jpg",
        "images/LONG_CCCC.png",
        "images/penta_col.jpg",
        "images/VERDI_Logo.jpg",
        "images/UCL_logo.png",
    ],
]

FUNDING_LOGOS = [
    "images/wellcome-logo.png",
    "images/billmelinda-logo.png",
    "images/uk-international-logo.png",
    "images/FundedbytheEU.png",
]

TOOL_CARDS = [
    {
        "title": "Analysis and ReseARC Compendium (ARC)",
        "image": "images/arc_logo.png",
        "href": "https://github.com/ISARICResearch/ARC",
        "body": [
            "ARC is a comprehensive machine-readable document in CSV format, designed for use in Clinical Report Forms (CRFs) during disease outbreaks. ",
            "It includes a library of questions covering demographics, comorbidities, symptoms, medications, and outcomes. ",
            "Each question is based on a standardized schema, has specific definitions mapped to controlled terminologies, and has built-in quality control. ",
            "ARC is openly accessible, with version control via GitHub ensuring document integrity and collaboration.",
        ],
    },
    {
        "title": "FHIRflat",
        "image": "images/fhirflat_logo.png",
        "href": "https://fhirflat.readthedocs.io/en/latest/",
        "body": [
            "FHIRflat is a versatile library designed to transform FHIR resources in NDJSON or native Python dictionaries into a flat structure, which can be easily written to a Parquet file. ",
            "This facilitates reproducible analytical pipelines (RAP) by converting raw data into the FHIR R5 standard with ISARIC-specific extensions. ",
            "Typically, FHIR resources are stored in databases served by specialized FHIR servers. However, for RAP development, which demands reproducibility and data snapshots, a flat file format is more practical. ",
        ],
    },
    {
        "title": "Visual Evidence & Research Tool for Exploration (VERTEX)",
        "image": "images/vertex_logo.png",
        "href": "https://github.com/ISARICResearch/VERTEX",
        "body": [
            "VERTEX is a web-based application designed to present graphs and tables based on relevant research questions that need quick answers during an outbreak. ",
            "VERTEX uses reproducible analytical pipelines, currently focusing on identifying the spectrum of clinical features in a disease and determining risk factors for patient outcomes. ",
            "New questions will be added by the ISARIC team and the wider scientific community, enabling the creation and sharing of new pipelines. ",
            "Users can download the code for ARC-structured data visualization through VERTEX.",
        ],
    },
]


def about_page():
    return html.Div(
        [
            navbar(),
            hero_section(),
            intro_section(),
            feature_section(),
            logo_section("In partnership with:", PARTNER_ROWS),
            logo_section("With funding from:", [FUNDING_LOGOS]),
            tools_section(),
            footer(),
        ]
    )


def navbar():
    return dbc.Navbar(
        dbc.Container(
            [
                html.A(
                    dbc.Row(
                        [
                            dbc.Col(
                                html.Img(
                                    src=dash.get_asset_url("images/ISARIC_logo_wh.png"),
                                    height="100px",
                                )
                            ),
                            dbc.Col(
                                dbc.NavbarBrand(
                                    "BRIDGE - BioResearch Integrated Data tool GEnerator",
                                    className="ms-2",
                                )
                            ),
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


def hero_section():
    return html.Section(
        [
            dbc.Row(
                [
                    dbc.Col(
                        [
                            html.Div(
                                [
                                    html.H1(
                                        "BRIDGE: Tailoring Case Report Forms for Every Outbreak",
                                        className="display-4",
                                        style={
                                            "font-weight": "bold",
                                            "color": "white",
                                        },
                                    ),
                                    html.P(
                                        "ISARIC BRIDGE streamlines the CRF creation process, generating data dictionaries and XML for REDCap, along with paper-like CRFs and completion guides.",
                                        style={"color": "white"},
                                    ),
                                    dbc.Button(
                                        "Create a CRF",
                                        className="home-button",
                                        id="start-button",
                                    ),
                                    html.A(
                                        "Visit GitHub",
                                        target="_blank",
                                        href="https://github.com/ISARICResearch",
                                        style={
                                            "display": "block",
                                            "margin-top": "10px",
                                            "color": "white",
                                        },
                                    ),
                                ],
                                style={"padding": "2rem"},
                            )
                        ],
                        md=6,
                        style={
                            "display": "flex",
                            "align-items": "center",
                            "background-color": "#475160",
                        },
                    ),
                    dbc.Col(
                        [
                            html.Img(
                                src=dash.get_asset_url("images/home_main.png"),
                                style={"width": "100%"},
                            )
                        ],
                        md=6,
                    ),
                ]
            )
        ],
        style={
            "padding": "0",
            "margin": "0",
            "background-color": "#475160",
        },
    )


def intro_section():
    return html.Section(
        [
            dbc.Row(
                [
                    dbc.Col(
                        [
                            html.H4(
                                "Accelerating Outbreak Research Response",
                                className="mb-3",
                            ),
                            html.P(
                                [
                                    "BRIDGE automates the creation of Case Report Forms (CRFs) tailored to specific diseases and research contexts. ",
                                    "You can build your CRF by selecting questions from the ARC library or using ready-made ",
                                    html.A(
                                        "ARChetype CRF templates",
                                        href="https://isaricresearch.github.io/CCP/ARChetype-CRF-Guidelines",
                                        target="_blank",
                                    ),
                                    ". BRIDGE then generates the required data dictionary and XML to set up a REDCap database, fully aligned with the ARC structure. ",
                                    "Learn more in our ",
                                    html.A(
                                        "guide for getting started.",
                                        href="https://ISARICResearch.github.io/Training/bridge_starting.html",
                                        target="_blank",
                                    ),
                                ],
                                style={
                                    "font-size": "20px",
                                    "textAlign": "justify",
                                },
                            ),
                        ],
                        md=9,
                    )
                ],
                className="my-5",
            ),
        ],
        className="container",
    )


def feature_section():
    return html.Section(
        [
            dbc.Row(
                [dbc.Col(feature_card(card), md=4) for card in FEATURE_CARDS],
                className="my-5",
            )
        ],
        className="container",
    )


def feature_card(card):
    return dbc.Card(
        [
            dbc.CardBody(
                [
                    html.H4(card["title"], className="card-title"),
                    html.P(card["body"], className="card-text"),
                ],
                className="card-body-fixed",
            ),
            dbc.CardImg(
                src=dash.get_asset_url(card["image"]),
                bottom=True,
                className="card-img-small",
            ),
        ],
        className="mb-3",
    )


def logo_section(heading, rows):
    return html.Section(
        [
            html.Div(
                [
                    html.Br(),
                    html.H3(heading, className="text-center my-4"),
                    *[
                        logo_row(images, add_top_spacing=index > 0)
                        for index, images in enumerate(rows)
                    ],
                ]
            )
        ]
    )


def logo_row(images, add_top_spacing=False):
    row_children = []
    if add_top_spacing:
        row_children.append(html.Br())
    row_children.append(
        dbc.Row(
            [dbc.Col(logo_image(image), width="auto") for image in images],
            className="justify-content-center",
        )
    )
    return html.Div(row_children)


def logo_image(image):
    return html.Div(
        [
            html.Img(
                src=dash.get_asset_url(image),
                className="img-fluid",
                style={"height": "100px"},
            )
        ],
        className="d-flex justify-content-center",
    )


def tools_section():
    return html.Section(
        [
            html.Div(
                [
                    html.H3(
                        "Take a Look at Our Other Tools",
                        className="text-center my-4",
                    ),
                    dbc.Row(
                        [dbc.Col(tool_card(card), md=3) for card in TOOL_CARDS],
                        className="my-5",
                        justify="center",
                    ),
                ],
                className="container",
            )
        ],
        className="py-5",
    )


def tool_card(card):
    return dbc.Card(
        [
            dbc.CardImg(src=dash.get_asset_url(card["image"]), top=True),
            dbc.CardBody(
                [
                    html.H4(card["title"], className="card-title"),
                    html.P(card["body"], className="card-text"),
                    html.A(
                        "Find Out More",
                        target="_blank",
                        href=card["href"],
                        style={
                            "display": "block",
                            "margin-top": "10px",
                            "color": "#BA0225",
                        },
                    ),
                ],
                className="card-tools-fixed",
            ),
        ]
    )


def footer():
    return html.Footer(
        [
            html.Div(
                [
                    html.P(
                        [
                            "Licensed under the ",
                            html.A(
                                "MIT License",
                                href="https://opensource.org/license/mit",
                                target="_blank",
                            ),
                            " by ",
                            html.A(
                                "ISARIC",
                                href="https://isaric.org/",
                                target="_blank",
                            ),
                            " on behalf of Oxford University.",
                        ],
                        className="text-center my-3",
                    )
                ],
                className="footer",
            )
        ]
    )
