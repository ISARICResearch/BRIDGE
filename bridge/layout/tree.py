import dash_bootstrap_components as dbc
import dash_treeview_antd
import pandas as pd
from dash import html

from bridge.logging.logger import setup_logger

pd.options.mode.copy_on_write = True

logger = setup_logger(__name__)


class Tree:

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
