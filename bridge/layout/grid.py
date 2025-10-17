import dash_ag_grid as dag
from dash import html


class Grid:

    def __init__(self):
        self.column_defs = [{'headerName': "Question", 'field': "Question", 'wrapText': True},
                            {'headerName': "Answer Options", 'field': "Answer Options", 'wrapText': True}]

        self.row_data = []

        self.grid = html.Div(
            dag.AgGrid(
                id='CRF_representation_grid',
                columnDefs=self.column_defs,
                rowData=self.row_data,
                defaultColDef={
                    "sortable": True,
                    "filter": True,
                    'resizable': True,
                    "enableCellChangeFlash": True,
                },
                columnSize="responsiveSizeToFit",
                dashGridOptions={
                    "rowDragManaged": True,
                    "rowDragEntireRow": True,
                    "rowDragMultiRow": True,
                    "rowSelection": "multiple",
                    "suppressMoveWhenRowDragging": True,
                    "autoHeight": True,
        },
                rowClassRules={
                    "form-separator-row ": 'params.data.SeparatorType == "form"',
                    'section-separator-row': 'params.data.SeparatorType == "section"',
                },
                style={
                    'overflow-y': 'auto',
                    'height': '99%',
                    'width': '100%',
                    'white-space': 'normal',
                    'overflow-x': 'hidden',
                },
            ),
            style={
                'overflow-y': 'auto',
                'height': '67vh',
                'width': '100%',
                'white-space': 'normal',
                'overflow-x': 'hidden',
                'text-overflow': 'ellipsis',
            },
        )
