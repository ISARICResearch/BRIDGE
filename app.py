import json

import dash
import dash_bootstrap_components as dbc
from dash import dcc, html, Input, Output

from bridge.arc import arc
from bridge.arc.arc_api import ArcApiClient
from bridge.layout.generate import Generate
from bridge.layout.save import Save
from bridge.layout.upload import Upload
from bridge.layout.app_layout import MainContent
from bridge.layout.grid import Grid
from bridge.layout.index import Index
from bridge.layout.modals import Modals
from bridge.layout.navbar import NavBar
from bridge.layout.settings import Settings
from bridge.layout.sidebar import SideBar
from bridge.layout.tree import Tree
from bridge.logging.logger import setup_logger

logger = setup_logger(__name__)

app = dash.Dash(__name__,
                external_stylesheets=[dbc.themes.BOOTSTRAP, 'https://use.fontawesome.com/releases/v5.8.1/css/all.css'],
                suppress_callback_exceptions=True)
app.title = 'BRIDGE'
server = app.server

logger.info('Starting BRIDGE application')

# Get initial data from ARC
ARC_VERSION_LIST, ARC_VERSION_LATEST = arc.get_arc_versions()
ARC_LANGUAGE_LIST = ArcApiClient().get_arc_language_list_version(ARC_VERSION_LATEST)
ARC_LANGUAGE_DEFAULT = 'English'

DF_ARC, PRESETS, _COMMIT = arc.get_arc(ARC_VERSION_LATEST)
DF_ARC = arc.add_required_datadicc_columns(DF_ARC)

TREE_ITEMS_DATA = arc.get_tree_items(DF_ARC, ARC_VERSION_LATEST)

# List content Transformation
DF_LISTS, LIST_VARIABLE_LIST = arc.get_list_content(DF_ARC, ARC_VERSION_LATEST, ARC_LANGUAGE_DEFAULT)
DF_ARC = arc.add_transformed_rows(DF_ARC, DF_LISTS, arc.get_variable_order(DF_ARC))

# User List content Transformation
DF_ULIST, ULIST_VARIABLE_LIST = arc.get_user_list_content(DF_ARC, ARC_VERSION_LATEST, ARC_LANGUAGE_DEFAULT)
DF_ARC = arc.add_transformed_rows(DF_ARC, DF_ULIST, arc.get_variable_order(DF_ARC))

# Multi List content Transformation
DF_MULTILIST, MULTILIST_VARIABLE_LIST = arc.get_multi_list_content(DF_ARC, ARC_VERSION_LATEST, ARC_LANGUAGE_DEFAULT)
DF_ARC = arc.add_transformed_rows(DF_ARC, DF_MULTILIST, arc.get_variable_order(DF_ARC))

ARC_JSON = DF_ARC.to_json(date_format='iso', orient='split')
ULIST_VARIABLE_JSON = json.dumps(ULIST_VARIABLE_LIST)
MULTILIST_VARIABLE_JSON = json.dumps(MULTILIST_VARIABLE_LIST)

# Grouping presets by the first column
GROUPED_PRESETS = {}
for key, value in PRESETS:
    GROUPED_PRESETS.setdefault(key, []).append(value)
GROUPED_PRESETS_JSON = json.dumps(GROUPED_PRESETS)

app.layout = MainContent().define_app_layout(ARC_JSON, ULIST_VARIABLE_JSON, MULTILIST_VARIABLE_JSON,
                                                   GROUPED_PRESETS_JSON, ARC_LANGUAGE_LIST)

app = Generate().register_callbacks(app)
app = Grid().register_callbacks(app)
app = Modals.register_callbacks(app)
app = Save.register_callbacks(app)
app = Settings.register_callbacks(app)
app = SideBar().register_callbacks(app)
app = Tree.register_callbacks(app)
app = Upload.register_callbacks(app)

app.clientside_callback(
    """
    function(n_intervals) {
        return navigator.userAgent;
    }
    """,
    Output("browser-info-store", "data"),
    Input("interval-browser", "n_intervals"),
    prevent_initial_call=True
)


@app.callback(Output('page-content', 'children'),
              Input('url', 'pathname'))
def display_page(pathname):
    if pathname == '/':
        return Index().home_page()
    else:
        return main_app()


@app.callback(Output('url', 'pathname'),
              Input('start-button', 'n_clicks'))
def start_app(n_clicks):
    if n_clicks is None:
        return '/'
    else:
        return '/main'


def main_app():
    return html.Div([
        NavBar().navbar,
        SideBar().sidebar,
        dcc.Loading(
            id="loading-overlay",
            type="circle",
            fullscreen=True,
            children=[
                Settings(ARC_VERSION_LIST, ARC_LANGUAGE_LIST, ARC_VERSION_LATEST, ARC_LANGUAGE_DEFAULT).settings_column,
                SideBar().preset_column,
                Tree(TREE_ITEMS_DATA).tree_column,
                MainContent().main_content,
            ],
            delay_show=1200,
        ),
    ])


if __name__ == "__main__":
    app.run_server(debug=True, use_reloader=False)
    # app.run_server(debug=True, host='0.0.0.0', port='8080')#change for deploy
