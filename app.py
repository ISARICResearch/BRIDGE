import dash
import dash_bootstrap_components as dbc
import pandas as pd
from dash import Input, Output

from bridge.buttons.generate import Generate
from bridge.buttons.save import Save
from bridge.buttons.upload import Upload
from bridge.layout import index
from bridge.layout.app_layout import define_app_layout, main_app, SideBar
from bridge.layout.grid import Grid
from bridge.layout.modals import Modals
from bridge.layout.settings import Settings
from bridge.layout.tree import Tree
from bridge.logging.logger import setup_logger

pd.options.mode.copy_on_write = True

logger = setup_logger(__name__)

app = dash.Dash(__name__,
                external_stylesheets=[dbc.themes.BOOTSTRAP, 'https://use.fontawesome.com/releases/v5.8.1/css/all.css'],
                suppress_callback_exceptions=True)
app.title = 'BRIDGE'
server = app.server

logger.info('Starting BRIDGE application')

app.layout = define_app_layout()
app = Generate().register_callbacks(app)
app = Grid.register_callbacks(app)
app = Modals.register_callbacks(app)
app = Save.register_callbacks(app)
app = Settings.register_callbacks(app)
app = SideBar.register_callbacks(app)
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
        return index.home_page()
    else:
        return main_app()


@app.callback(Output('url', 'pathname'),
              Input('start-button', 'n_clicks'))
def start_app(n_clicks):
    if n_clicks is None:
        return '/'
    else:
        return '/main'


if __name__ == "__main__":
    app.run_server(debug=True, use_reloader=False)
    # app.run_server(debug=True, host='0.0.0.0', port='8080')#change for deploy
