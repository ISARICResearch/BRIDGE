import json

import dash
import dash_bootstrap_components as dbc
from dash import dcc, html, Input, Output, State

import bridge.callbacks  # noqa
from bridge.arc import arc_core, arc_tree
from bridge.arc.arc_api import ArcApiClient
from bridge.arc.arc_lists import ArcList
from bridge.layout.app_layout import MainContent
from bridge.layout.index import Index
from bridge.layout.navbar import NavBar
from bridge.layout.settings import Settings
from bridge.layout.sidebar import SideBar
from bridge.layout.tree import Tree
from bridge.logging.logger import setup_logger

logger = setup_logger(__name__)

app = dash.Dash(
    __name__,
    external_stylesheets=[
        dbc.themes.BOOTSTRAP,
        "https://use.fontawesome.com/releases/v5.8.1/css/all.css",
    ],
    suppress_callback_exceptions=True,
)
app.title = "BRIDGE"
server = app.server

logger.info("Starting BRIDGE application")

# Get initial data from ARC
ARC_VERSION_LIST, ARC_VERSION_LATEST = arc_core.get_arc_versions()
ARC_LANGUAGE_LIST = ArcApiClient().get_arc_language_list_version(ARC_VERSION_LATEST)
ARC_LANGUAGE_DEFAULT = "English"

DF_ARC, PRESETS, _COMMIT = arc_core.get_arc(ARC_VERSION_LATEST)
DF_ARC = arc_core.add_required_datadicc_columns(DF_ARC)

TREE_ITEMS_DATA = arc_tree.get_tree_items(DF_ARC, ARC_VERSION_LATEST)

# List content Transformation
DF_LISTS, LIST_VARIABLE_LIST = ArcList(
    ARC_VERSION_LATEST, ARC_LANGUAGE_DEFAULT
).get_list_content(DF_ARC)
DF_ARC = arc_core.add_transformed_rows(
    DF_ARC, DF_LISTS, arc_core.get_variable_order(DF_ARC)
)

# User List content Transformation
DF_ULIST, ULIST_VARIABLE_LIST = ArcList(
    ARC_VERSION_LATEST, ARC_LANGUAGE_DEFAULT
).get_user_list_content(DF_ARC)
DF_ARC = arc_core.add_transformed_rows(
    DF_ARC, DF_ULIST, arc_core.get_variable_order(DF_ARC)
)

# Multi List content Transformation
DF_MULTILIST, MULTILIST_VARIABLE_LIST = ArcList(
    ARC_VERSION_LATEST, ARC_LANGUAGE_DEFAULT
).get_multi_list_content(DF_ARC)
DF_ARC = arc_core.add_transformed_rows(
    DF_ARC, DF_MULTILIST, arc_core.get_variable_order(DF_ARC)
)

ARC_JSON = DF_ARC.to_json(date_format="iso", orient="split")
ULIST_VARIABLE_JSON = json.dumps(ULIST_VARIABLE_LIST)
MULTILIST_VARIABLE_JSON = json.dumps(MULTILIST_VARIABLE_LIST)

# Grouping presets by the first column
GROUPED_PRESETS = {}
for key, value in PRESETS:
    GROUPED_PRESETS.setdefault(key, []).append(value)
GROUPED_PRESETS_JSON = json.dumps(GROUPED_PRESETS)

app.layout = MainContent().define_app_layout(
    ARC_JSON,
    ULIST_VARIABLE_JSON,
    MULTILIST_VARIABLE_JSON,
    GROUPED_PRESETS_JSON,
    ARC_LANGUAGE_LIST,
)

app.clientside_callback(
    """
    function(n_intervals) {
        return navigator.userAgent;
    }
    """,
    Output("browser-info-store", "data"),
    Input("interval-browser", "n_intervals"),
    prevent_initial_call=True,
)

app.clientside_callback(
    """async  (runCallback, rowIndex) => {
        if (runCallback) {
            const gridApi =  await dash_ag_grid.getApiAsync("CRF_representation_grid")

            var firstCol = gridApi.getAllDisplayedColumns()[0];
            var rowsEmpty = gridApi.isRowDataEmpty();

            if (! rowsEmpty) {
                var rowNode = gridApi.getDisplayedRowAtIndex(rowIndex);
                gridApi.ensureNodeVisible(rowNode)
                gridApi.flashCells({ rowNodes: [rowNode] });
            }
        }
        return 0
    }""",
    Output("focused-cell-index", "data", allow_duplicate=True),
    [
        Input("focused-cell-run-callback", "data"),
    ],
    State("focused-cell-index", "data"),
    prevent_initial_call=True,
)


@app.callback(Output("page-content", "children"), Input("url", "pathname"))
def display_page(pathname):
    if pathname == "/":
        return Index().home_page()
    else:
        return main_app()


@app.callback(Output("url", "pathname"), Input("start-button", "n_clicks"))
def start_app(n_clicks):
    if n_clicks is None:
        return "/"
    else:
        return "/main"


def main_app():
    return html.Div(
        [
            NavBar().navbar,
            SideBar().sidebar,
            dcc.Loading(
                id="loading-overlay",
                type="circle",
                fullscreen=True,
                children=[
                    Settings(
                        ARC_VERSION_LIST,
                        ARC_LANGUAGE_LIST,
                        ARC_VERSION_LATEST,
                        ARC_LANGUAGE_DEFAULT,
                    ).settings_column,
                    SideBar().preset_column,
                    Tree(TREE_ITEMS_DATA).tree_column,
                    MainContent().main_content,
                ],
                delay_show=1500,
            ),
        ]
    )


if __name__ == "__main__":
    app.run_server(debug=True, use_reloader=False)
