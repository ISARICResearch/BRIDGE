import dash_bootstrap_components as dbc
from dash import html

ASSETS_DIR = '../assets'
LOGOS_DIR = f'{ASSETS_DIR}/logos'
SCREENSHOTS_DIR = f'{ASSETS_DIR}/screenshots'

navbar_big = dbc.Navbar(
    dbc.Container(
        [
            html.A(
                # Use row and col to control vertical alignment of logo / brand
                dbc.Row(
                    [
                        dbc.Col(html.Img(src=f"{LOGOS_DIR}/ISARIC_logo_wh.png", height="100px")),
                        dbc.Col(
                            dbc.NavbarBrand("BRIDGE - BioResearch Integrated Data tool GEnerator", className="ms-2")),
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


def home_page():
    return html.Div([
        navbar_big,
        # First Section: Big Slogan and Button
        html.Section([
            dbc.Row([
                dbc.Col([
                    html.Div([
                        html.H1("BRIDGE: Tailoring Case Reports for Every Outbreak", className="display-4",
                                style={'font-weight': 'bold', 'color': 'white'}),
                        html.P(
                            "ISARIC BRIDGE streamlines the CRF creation process, generating data dictionaries and XML for REDCap, along with paper-like CRFs and completion guides.",
                            style={'color': 'white'}),
                        dbc.Button("Create a CRF", className="home-button", id='start-button'),
                        html.A("Visit GitHub", target="_blank", href="https://github.com/ISARICResearch",
                               style={'display': 'block', 'margin-top': '10px', 'color': 'white'})
                    ], style={'padding': '2rem'})
                ], md=6, style={'display': 'flex', 'align-items': 'center', 'background-color': '#475160'}),
                dbc.Col([
                    html.Img(src=f"{SCREENSHOTS_DIR}/home_main.png", style={'width': '100%'})
                ], md=6)
            ])
        ], style={'padding': '0', 'margin': '0', 'background-color': '#475160'}),

        html.Section([
            dbc.Row([
                dbc.Col([
                    html.H4("Accelerating Outbreak Research Response", className="mb-3"),
                    html.P(
                        "BRIDGE automates the creation of Case Report Forms (CRFs) for specific diseases and research contexts. It generates the necessary data dictionary and XML to create a REDCap database for data capture in the ARC structure. Learn more in our ",
                        style={"font-size": "20px", "display": "inline"}),
                    html.A("guide for getting started.",
                           href="https://ISARICResearch.github.io/Training/bridge_starting.html", target="_blank",
                           style={"font-size": "20px", "display": "inline"})
                ], md=9)
            ], className="my-5"),

        ], className="container"),

        html.Section([
            dbc.Row([
                dbc.Col([
                    dbc.Card([

                        dbc.CardBody([
                            html.H4("Choose", className="card-title"),
                            html.P([
                                "BRIDGE uses the machine-readable library ",
                                html.A("ARC", href="https://example.com", target="_blank"),
                                " and allows the user to choose the questions they want to include in the CRF. ",
                                "BRIDGE presents ARC as a tree structure with different levels: ARC version, forms, sections, and questions. Users navigate through this tree and select the questions they want to include in the CRF.",
                                html.Br(),
                                html.Br(),
                                "Additionally, users can start with one of our Presets, which are pre-selected groups of questions. They can click on the Pre-sets tab and select those they want to include in the CRF. All selected questions can be customized."
                            ], className="card-text")
                        ], className="card-body-fixed"),
                        dbc.CardImg(src=f"{SCREENSHOTS_DIR}/card1.png", bottom=True, className="card-img-small"),
                    ], className="mb-3")
                ], md=4),
                dbc.Col([
                    dbc.Card([

                        dbc.CardBody([
                            html.H4("Customize", className="card-title"),
                            html.P([
                                "BRIDGE allows customization of CRFs from chosen questions, as well as selection of measurement units and answer options where pertinent. ",
                                "Users click the relevant question, and a checkable list appears with options for the site or disease being researched.",
                                html.Br(),
                                html.Br(),
                                "This feature ensures that the CRF is tailored to specific needs, enhancing the precision and relevance of the data collected."
                            ], className="card-text")
                        ], className="card-body-fixed"),
                        dbc.CardImg(src=f"{SCREENSHOTS_DIR}/card2.png", bottom=True, className="card-img-small"),
                    ], className="mb-3")
                ], md=4),
                dbc.Col([
                    dbc.Card([

                        dbc.CardBody([
                            html.H4("Capture", className="card-title"),
                            html.P([
                                "BRIDGE generates files for creating databases within REDCap, including the data dictionary and XML needed to create a REDCap database for capturing data in the ARC structure. ",
                                "It also produces paper-like versions of the CRFs and completion guides. ",
                                html.Br(),
                                html.Br(),
                                "Once users are satisfied with their selections, they can name the CRF and click on generate to finalize the process, ensuring a seamless transition to data collection."
                            ], className="card-text")
                        ], className="card-body-fixed"),
                        dbc.CardImg(src=f"{SCREENSHOTS_DIR}/card3.png", bottom=True, className="card-img-small"),
                    ], className="mb-3")
                ], md=4),

            ], className="my-5")
        ], className="container"),
        html.Section([
            html.Div([
                html.Br(),
                html.H3("In partnership with:", className="text-center my-4"),
                # First Row
                dbc.Row([
                    dbc.Col([
                        html.Div([
                            html.Img(src=f"{LOGOS_DIR}/FIOCRUZ_logo.png", className="img-fluid",
                                     style={"height": "100px"})
                        ], className="d-flex justify-content-center")
                    ], width="auto"),
                    dbc.Col([
                        html.Div([
                            html.Img(src=f"{LOGOS_DIR}/global_health.png", className="img-fluid",
                                     style={"height": "100px"})
                        ], className="d-flex justify-content-center")
                    ], width="auto"),
                    dbc.Col([
                        html.Div([
                            html.Img(src=f"{LOGOS_DIR}/puc_rio.png", className="img-fluid",
                                     style={"height": "100px"})
                        ], className="d-flex justify-content-center")
                    ], width="auto"),

                ], className="justify-content-center"),

                # Second Row
                html.Br(),
                dbc.Row([
                    dbc.Col([
                        html.Div([
                            html.Img(src=f"{LOGOS_DIR}/CONTAGIO_Logo.jpg", className="img-fluid",
                                     style={"height": "100px"})
                        ], className="d-flex justify-content-center")
                    ], width="auto"),
                    dbc.Col([
                        html.Div([
                            html.Img(src=f"{LOGOS_DIR}/LONG_CCCC.png", className="img-fluid",
                                     style={"height": "100px"})
                        ], className="d-flex justify-content-center")
                    ], width="auto"),
                    dbc.Col([
                        html.Div([
                            html.Img(src=f"{LOGOS_DIR}/penta_col.jpg", className="img-fluid",
                                     style={"height": "100px"})
                        ], className="d-flex justify-content-center")
                    ], width="auto"),
                    dbc.Col([
                        html.Div([
                            html.Img(src=f"{LOGOS_DIR}/VERDI_Logo.jpg", className="img-fluid",
                                     style={"height": "100px"})
                        ], className="d-flex justify-content-center")
                    ], width="auto")
                ], className="justify-content-center")

            ])
        ]),

        html.Section([
            html.Div([
                html.Br(),
                html.H3("With funding from:", className="text-center my-4"),
                dbc.Row([
                    dbc.Col([
                        html.Div([
                            html.Img(src=f"{LOGOS_DIR}/wellcome-logo.png", className="img-fluid",
                                     style={"height": "100px"})
                        ], className="d-flex justify-content-center")
                    ], width="auto"),
                    dbc.Col([
                        html.Div([
                            html.Img(src=f"{LOGOS_DIR}/billmelinda-logo.png", className="img-fluid",
                                     style={"height": "100px"})
                        ], className="d-flex justify-content-center")
                    ], width="auto"),
                    dbc.Col([
                        html.Div([
                            html.Img(src=f"{LOGOS_DIR}/uk-international-logo.png", className="img-fluid",
                                     style={"height": "100px"})
                        ], className="d-flex justify-content-center")
                    ], width="auto"),
                    dbc.Col([
                        html.Div([
                            html.Img(src=f"{LOGOS_DIR}/FundedbytheEU.png", className="img-fluid",
                                     style={"height": "100px"})
                        ], className="d-flex justify-content-center")
                    ], width="auto")
                ], className="justify-content-center")
            ])
        ]),

        # Fourth Section: Other Tools
        # Section showcasing other tools
        html.Section([
            html.Div([
                html.H3("Take a Look at Our Other Tools", className="text-center my-4"),
                dbc.Row([
                    dbc.Col([
                        dbc.Card([
                            dbc.CardImg(src=f"{LOGOS_DIR}/arc_logo.png", top=True),
                            dbc.CardBody([
                                html.H4("Analysis and ReseARC Compendium (ARC)", className="card-title"),
                                html.P([
                                    "ARC is a comprehensive machine-readable document in CSV format, designed for use in Clinical Report Forms (CRFs) during disease outbreaks. ",
                                    "It includes a library of questions covering demographics, comorbidities, symptoms, medications, and outcomes. ",
                                    "Each question is based on a standardized schema, has specific definitions mapped to controlled terminologies, and has built-in quality control. ",
                                    "ARC is openly accessible, with version control via GitHub ensuring document integrity and collaboration."
                                ], className="card-text"),
                                html.A("Find Out More", target="_blank", href="https://github.com/ISARICResearch/ARC",
                                       style={'display': 'block', 'margin-top': '10px', 'color': '#BA0225'})
                            ], className="card-tools-fixed")
                        ])
                    ], md=3),
                    dbc.Col([
                        dbc.Card([
                            dbc.CardImg(src=f"{LOGOS_DIR}/fhirflat_logo.png", top=True),
                            dbc.CardBody([
                                html.H4("FHIRflat", className="card-title"),
                                html.P([
                                    "FHIRflat is a versatile library designed to transform FHIR resources in NDJSON or native Python dictionaries into a flat structure, which can be easily written to a Parquet file. ",
                                    "This facilitates reproducible analytical pipelines (RAP) by converting raw data into the FHIR R5 standard with ISARIC-specific extensions. ",
                                    "Typically, FHIR resources are stored in databases served by specialized FHIR servers. However, for RAP development, which demands reproducibility and data snapshots, a flat file format is more practical. ",

                                ], className="card-text")
                                ,
                                html.A("Find Out More", target="_blank",
                                       href="https://fhirflat.readthedocs.io/en/latest/",
                                       style={'display': 'block', 'margin-top': '10px', 'color': '#BA0225'})
                            ], className="card-tools-fixed")
                        ])
                    ], md=3),

                    dbc.Col([
                        dbc.Card([
                            dbc.CardImg(src=f"{LOGOS_DIR}/polyflame_logo.png", top=True),
                            dbc.CardBody([
                                html.H4("Polymorphic FLexible Analytics and Modelling Engine (PolyFLAME)",
                                        className="card-title"),
                                html.P([
                                    "PolyFLAME processes and transforms data using the FHIRflat library. ",
                                    "Once input data is brought into FHIRflat, it is represented as a (optionally zipped) folder of FHIR resources, with a parquet file corresponding to each resource: patient.parquet, encounter.parquet, and so on. ",
                                    "PolyFLAME is an easy-to-use library that can be utilized in Jupyter notebooks and other downstream code to query answers to common research questions in a reproducible analytical pipeline (RAP). "
                                ], className="card-text"),
                                html.A("Find Out More", target="_blank",
                                       href="https://polyflame.readthedocs.io/en/latest/index.html",
                                       style={'display': 'block', 'margin-top': '10px', 'color': '#BA0225'})
                            ], className="card-tools-fixed"),

                        ])
                    ], md=3),
                    dbc.Col([
                        dbc.Card([
                            dbc.CardImg(src=f"{LOGOS_DIR}/vertex_logo.png", top=True),
                            dbc.CardBody([
                                html.H4("Visual Evidence & Research Tool for Exploration (VERTEX)",
                                        className="card-title"),
                                html.P([
                                    "VERTEX is a web-based application designed to present graphs and tables based on relevant research questions that need quick answers during an outbreak. ",
                                    "VERTEX uses reproducible analytical pipelines, currently focusing on identifying the spectrum of clinical features in a disease and determining risk factors for patient outcomes. ",
                                    "New questions will be added by the ISARIC team and the wider scientific community, enabling the creation and sharing of new pipelines. ",
                                    "Users can download the code for ARC-structured data visualization through VERTEX."
                                ], className="card-text"),
                                html.A("Find Out More", target="_blank",
                                       href="https://github.com/ISARICResearch/VERTEX",
                                       style={'display': 'block', 'margin-top': '10px', 'color': '#BA0225'})
                            ], className="card-tools-fixed")
                        ])
                    ], md=3)
                ], className="my-5")
            ], className="container")
        ], className="py-5"),

        html.Footer([
            html.Div([
                html.P([
                    "Licensed under a ",
                    html.A("Creative Commons Attribution-ShareAlike 4.0",
                           href="https://creativecommons.org/licenses/by-sa/4.0/", target="_blank"),
                    " International License by ",
                    html.A("ISARIC", href="https://isaric.org/", target="_blank"),
                    " on behalf of Oxford University."
                ], className="text-center my-3")
            ], className="footer")
        ])
    ]),
