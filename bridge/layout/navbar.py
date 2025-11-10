import dash
import dash_bootstrap_components as dbc
from dash import html


class NavBar:

    def __init__(self):
        self.isaric_logo = dash.get_asset_url('ISARIC_logo_wh.png')

        self.navbar = dbc.Navbar(
            dbc.Container(
                [
                    html.A(
                        dbc.Row(
                            [
                                dbc.Col(html.Img(src=self.isaric_logo, height="60px")),
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
                        href="https://bridge.isaric.org/",
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
