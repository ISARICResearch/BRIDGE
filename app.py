import base64
import io
import json
import re
import zipfile
from datetime import datetime
from os.path import join, abspath, dirname

import dash
import dash_ag_grid as dag
import dash_bootstrap_components as dbc
import dash_treeview_antd
import pandas as pd
from dash import callback_context, dcc, html, Input, Output, State
from dash.exceptions import PreventUpdate
from unidecode import unidecode

import src.generate_pdf.form as form
from src import arc, bridge_modals, paper_crf, index
from src.arc_api import ArcApiClient
from src.bridge_main import MainContent, NavBar, SideBar, Settings, Presets, TreeItems
from src.logger import setup_logger

pd.options.mode.copy_on_write = True

logger = setup_logger(__name__)

app = dash.Dash(__name__,
                external_stylesheets=[dbc.themes.BOOTSTRAP, 'https://use.fontawesome.com/releases/v5.8.1/css/all.css'],
                suppress_callback_exceptions=True)
app.title = 'BRIDGE'
server = app.server

logger.info('Starting BRIDGE application')

# Global variables
CONFIG_DIR_FULL = join(dirname(abspath(__file__)), 'assets', 'config_files')

ARC_VERSION_LIST, ARC_VERSION_INITIAL = arc.getARCVersions()
ARC_LANGUAGE_LIST_INITIAL = ArcApiClient().get_arc_language_list_version(ARC_VERSION_INITIAL)
ARC_LANGUAGE_INITIAL = 'English'

CURRENT_DATADICC, PRESETS, COMMIT = arc.getARC(ARC_VERSION_INITIAL)
CURRENT_DATADICC = arc.add_required_datadicc_columns(CURRENT_DATADICC)

TREE_ITEMS_DATA = arc.getTreeItems(CURRENT_DATADICC, ARC_VERSION_INITIAL)

# List content Transformation
ARC_LISTS, LIST_VARIABLE_CHOICES = arc.getListContent(CURRENT_DATADICC, ARC_VERSION_INITIAL, ARC_LANGUAGE_INITIAL)
CURRENT_DATADICC = arc.addTransformedRows(CURRENT_DATADICC, ARC_LISTS, arc.getVariableOrder(CURRENT_DATADICC))

# User List content Transformation
ARC_ULIST, ULIST_VARIABLE_CHOICES = arc.getUserListContent(CURRENT_DATADICC, ARC_VERSION_INITIAL, ARC_LANGUAGE_INITIAL)
CURRENT_DATADICC = arc.addTransformedRows(CURRENT_DATADICC, ARC_ULIST, arc.getVariableOrder(CURRENT_DATADICC))

ARC_MULTILIST, MULTILIST_VARIABLE_CHOICES = arc.getMultuListContent(CURRENT_DATADICC, ARC_VERSION_INITIAL,
                                                                    ARC_LANGUAGE_INITIAL)
CURRENT_DATADICC = arc.addTransformedRows(CURRENT_DATADICC, ARC_MULTILIST, arc.getVariableOrder(CURRENT_DATADICC))

INITIAL_CURRENT_DATADICC = CURRENT_DATADICC.to_json(date_format='iso', orient='split')
INITIAL_ULIST_VARIABLE_CHOICES = json.dumps(ULIST_VARIABLE_CHOICES)
INITIAL_MULTILIST_VARIABLE_CHOICES = json.dumps(MULTILIST_VARIABLE_CHOICES)

MODIFIED_LIST = []

# Grouping presets by the first column
GROUPED_PRESETS = {}

for key, value in PRESETS:
    GROUPED_PRESETS.setdefault(key, []).append(value)

INITIAL_GROUPED_PRESETS = json.dumps(GROUPED_PRESETS)

app.layout = html.Div(
    [
        dcc.Store(id='current_datadicc-store', data=INITIAL_CURRENT_DATADICC),
        dcc.Store(id='ulist_variable_choices-store', data=INITIAL_ULIST_VARIABLE_CHOICES),
        dcc.Store(id='multilist_variable_choices-store', data=INITIAL_MULTILIST_VARIABLE_CHOICES),
        dcc.Store(id='grouped_presets-store', data=INITIAL_GROUPED_PRESETS),
        dcc.Store(id='tree_items_data-store', data=INITIAL_GROUPED_PRESETS),

        dcc.Store(id='templates_checks_ready', data=False),

        dcc.Location(id='url', refresh=False),
        html.Div(id='page-content'),
        dcc.Download(id="download-dataframe-csv"),
        dcc.Download(id='download-compGuide-pdf'),
        dcc.Download(id='download-projectxml-pdf'),
        dcc.Download(id='download-paperlike-pdf'),
        dcc.Download(id='save-crf'),
        bridge_modals.variableInformation_modal(),
        bridge_modals.researchQuestions_modal(),
        dcc.Loading(id="loading-generate",
                    type="default",
                    children=html.Div(id="loading-output-generate"),
                    ),
        dcc.Loading(id="loading-save",
                    type="default",
                    children=html.Div(id="loading-output-save"),
                    ),
        dcc.Store(id='commit-store'),
        dcc.Store(id='selected_data-store'),
        dcc.Store(id='language-list-store', data=ARC_LANGUAGE_LIST_INITIAL),
        dcc.Store(id='upload-version-store'),
        dcc.Store(id='upload-language-store'),
        dcc.Store(id='upload-crf-ready', data=False),
        dcc.Store(id="browser-info-store"),

        dcc.Interval(id="interval-browser", interval=500, n_intervals=0, max_intervals=1),
    ]
)

app = SideBar.add_sidebar_callbacks(app)

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


def main_app():
    return html.Div([
        NavBar.navbar,
        SideBar.sidebar,
        dcc.Loading(
            id="loading-overlay",
            type="circle",  # Spinner style: 'default', 'circle', 'dot'
            fullscreen=True,  # Covers the full screen
            children=[
                Settings(ARC_VERSION_LIST, ARC_LANGUAGE_LIST_INITIAL, ARC_VERSION_INITIAL,
                         ARC_LANGUAGE_INITIAL).settings_column,
                Presets.preset_column,
                TreeItems(TREE_ITEMS_DATA).tree_column,
                MainContent.main_content,
            ],
            delay_show=1000,
        ),
    ])


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


@app.callback(
    [
        Output('CRF_representation_grid', 'columnDefs'),
        Output('CRF_representation_grid', 'rowData'),
        Output('selected_data-store', 'data')
    ],
    [
        Input('input', 'checked')
    ],
    [
        State('current_datadicc-store', 'data')
    ],
    prevent_initial_call=True)
def display_checked(checked, current_datadicc_saved):
    current_datadicc = pd.read_json(io.StringIO(current_datadicc_saved), orient='split')

    column_defs = [{'headerName': "Question", 'field': "Question", 'wrapText': True},
                   {'headerName': "Answer Options", 'field': "Answer Options", 'wrapText': True}]

    row_data = [{'question': "", 'options': ""},
                {'question': "", 'options': ""}]

    selected_variables = pd.DataFrame()
    if checked and len(checked) > 0:
        # global selected_variables
        selected_dependency_lists = current_datadicc['Dependencies'].loc[
            current_datadicc['Variable'].isin(checked)].tolist()
        flat_selected_dependency = set()
        for sublist in selected_dependency_lists:
            flat_selected_dependency.update(sublist)
        all_selected = set(checked).union(flat_selected_dependency)
        selected_variables = current_datadicc.loc[current_datadicc['Variable'].isin(all_selected)]

        #############################################################
        #############################################################
        ## REDCAP Pipeline
        selected_variables = arc.getIncludeNotShow(selected_variables['Variable'], current_datadicc)

        # Select Units Transformation
        arc_var_units_selected, delete_this_variables_with_units = arc.getSelectUnits(selected_variables['Variable'],
                                                                                      current_datadicc)
        if arc_var_units_selected is not None:
            selected_variables = arc.addTransformedRows(selected_variables, arc_var_units_selected,
                                                        arc.getVariableOrder(current_datadicc))
            if len(delete_this_variables_with_units) > 0:  # This remove all the unit variables that were included in a select unit type question
                selected_variables = selected_variables.loc[
                    ~selected_variables['Variable'].isin(delete_this_variables_with_units)]

        selected_variables = arc.generateDailyDataType(selected_variables)

        #############################################################
        #############################################################

        last_form, last_section = None, None
        new_rows = []
        selected_variables = selected_variables.fillna('')
        for index, row in selected_variables.iterrows():
            # Add form separator
            if row['Form'] != last_form:
                new_rows.append({'Question': f"{row['Form'].upper()}", 'Answer Options': '', 'IsSeparator': True,
                                 'SeparatorType': 'form'})
                last_form = row['Form']

            # Add section separator
            if row['Section'] != last_section and row['Section'] != '':
                new_rows.append({'Question': f"{row['Section'].upper()}", 'Answer Options': '', 'IsSeparator': True,
                                 'SeparatorType': 'section'})
                last_section = row['Section']

            # Process the actual row
            if row['Type'] in ['radio', 'dropdown', 'checkbox', 'list', 'user_list', 'multi_list']:

                formatted_choices = form.format_choices(row['Answer Options'], row['Type'])
                row['Answer Options'] = formatted_choices
            elif row['Validation'] == 'date_dmy':
                date_str = "[_D_][_D_]/[_M_][_M_]/[_2_][_0_][_Y_][_Y_]"
                row['Answer Options'] = date_str
            else:
                row['Answer Options'] = form.LINE_PLACEHOLDER

            # Add the processed row to new_rows
            new_row = row.to_dict()
            new_row['IsSeparator'] = False
            new_rows.append(new_row)

        # Update selected_variables with new rows including separators
        selected_variables_for_TableVisualization = pd.DataFrame(new_rows)
        selected_variables_for_TableVisualization = selected_variables_for_TableVisualization.loc[
            selected_variables_for_TableVisualization['Type'] != 'group']
        # Convert to dictionary for row_data
        row_data = selected_variables_for_TableVisualization.to_dict(orient='records')

        column_defs = [{'headerName': "Question", 'field': "Question", 'wrapText': True},
                       {'headerName': "Answer Options", 'field': "Answer Options", 'wrapText': True}]

    return column_defs, row_data, selected_variables.to_json(date_format='iso', orient='split')


@app.callback(Output('rq_modal', 'is_open'),
              [Input("toggle-question", "n_clicks")],
              prevent_initial_call=True)
def research_question(n_question):
    return True


@app.callback([
    Output('modal', 'is_open'),
    Output('modal_title', 'children'),
    Output('definition-text', 'children'),
    Output('completion-guide-text', 'children'),
    Output('skip-logic-text', 'children'),
    Output('options-checklist', 'style'),
    Output('options-list-group', 'style'),
    Output('options-checklist', 'options'),
    Output('options-checklist', 'value'),
    Output('options-list-group', 'children')],
    [
        Input('input', 'selected'),
    ],
    [
        State('ulist_variable_choices-store', 'data'),
        State('multilist_variable_choices-store', 'data'),
        State('modal', 'is_open'),
        State('current_datadicc-store', 'data'),
    ])
def display_selected(selected, ulist_variable_choices_saved, multilist_variable_choices_saved, is_open,
                     current_datadicc_saved):
    dict1 = json.loads(ulist_variable_choices_saved)
    dict2 = json.loads(multilist_variable_choices_saved)
    datatatata = dict1 + dict2
    current_datadicc = pd.read_json(io.StringIO(current_datadicc_saved), orient='split')
    if selected is not None:
        if len(selected) > 0:
            if selected[0] in list(current_datadicc['Variable']):
                question = current_datadicc['Question'].loc[current_datadicc['Variable'] == selected[0]].iloc[0]
                definition = current_datadicc['Definition'].loc[current_datadicc['Variable'] == selected[0]].iloc[0]
                completion = \
                    current_datadicc['Completion Guideline'].loc[current_datadicc['Variable'] == selected[0]].iloc[0]
                skip_logic = current_datadicc['Branch'].loc[current_datadicc['Variable'] == selected[0]].iloc[0]

                branch = skip_logic

                ulist_variables = [i[0] for i in datatatata]
                if selected[0] in ulist_variables:
                    for item in datatatata:
                        if item[0] == selected[0]:
                            options = []
                            checked_items = []
                            for i in item[1]:
                                options.append({"label": str(i[0]) + ', ' + i[1], "value": str(i[0]) + '_' + i[1]})
                                if i[2] == 1:
                                    checked_items.append(str(i[0]) + '_' + i[1])

                    return True, question + ' [' + selected[0] + ']', definition, completion, branch, {
                        "padding": "20px", "maxHeight": "250px", "overflowY": "auto"}, {
                        "display": "none"}, options, checked_items, []
                else:
                    options = []
                    answ_options = \
                        current_datadicc['Answer Options'].loc[current_datadicc['Variable'] == selected[0]].iloc[0]
                    if isinstance(answ_options, str):
                        for i in answ_options.split('|'):
                            options.append(dbc.ListGroupItem(i))
                    else:
                        options = []
                    return True, question + ' [' + selected[0] + ']', definition, completion, branch, {
                        "display": "none"}, {"maxHeight": "250px", "overflowY": "auto"}, [], [], options

    return False, '', '', '', '', {"display": "none"}, {"display": "none"}, [], [], []


def get_dataframe_arc_language(df_version, selected_version, selected_language):
    if selected_language != 'English':
        df_version_language = arc.getARCTranslation(
            selected_language,
            selected_version,
            df_version
        )
    else:
        df_version_language = df_version.copy()
    return df_version_language


def get_version_language_related_data(selected_version, selected_language):
    df_version, version_presets, version_commit = arc.getARC(selected_version)
    df_version = arc.add_required_datadicc_columns(df_version)
    df_version_language = get_dataframe_arc_language(df_version, selected_version, selected_language)

    version_arc_lists, version_list_variable_choices = arc.getListContent(df_version_language, selected_version,
                                                                          selected_language)
    df_version_language = arc.addTransformedRows(df_version_language, version_arc_lists,
                                                 arc.getVariableOrder(df_version_language))

    version_arc_ulist, version_ulist_variable_choices = arc.getUserListContent(df_version_language, selected_version,
                                                                               selected_language)

    df_version_language = arc.addTransformedRows(df_version_language, version_arc_ulist,
                                                 arc.getVariableOrder(df_version_language))

    version_arc_multilist, version_multilist_variable_choices = arc.getMultuListContent(df_version_language,
                                                                                        selected_version,
                                                                                        selected_language)

    df_version_language = arc.addTransformedRows(df_version_language, version_arc_multilist,
                                                 arc.getVariableOrder(df_version_language))

    version_grouped_presets = {}
    for section, preset_name in version_presets:
        version_grouped_presets.setdefault(section, []).append(preset_name)

    accordion_items = [
        dbc.AccordionItem(
            title=section,
            children=dbc.Checklist(
                options=[{"label": preset_name, "value": preset_name} for preset_name in preset_names],
                value=[],
                id={'type': 'template_check', 'index': section},
                switch=True,
            )
        )
        for section, preset_names in version_grouped_presets.items()
    ]
    return df_version_language, version_commit, version_grouped_presets, accordion_items


@app.callback(
    [
        Output('selected-version-store', 'data', allow_duplicate=True),
        Output('selected-language-store', 'data', allow_duplicate=True),
        Output('commit-store', 'data', allow_duplicate=True),
        Output('preset-accordion', 'children', allow_duplicate=True),
        Output('grouped_presets-store', 'data'),
        Output('current_datadicc-store', 'data', allow_duplicate=True),
        Output('templates_checks_ready', 'data')
    ],
    [
        Input({'type': 'dynamic-version', 'index': dash.ALL}, 'n_clicks'),
        Input({'type': 'dynamic-language', 'index': dash.ALL}, 'n_clicks'),
    ],
    [
        State('selected-version-store', 'data'),
        State('selected-language-store', 'data'),
        State('language-list-store', 'data'),
    ],
    prevent_initial_call=True  # Evita que se dispare al inicio
)
def store_clicked_item(n_clicks_version, n_clicks_language, selected_version_data, selected_language_data, language_list_data):
    ctx = dash.callback_context

    # Si no hay cambios (es decir, no hay un input activado), no se hace nada
    if not ctx.triggered:
        return dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, False

    button_id = ctx.triggered[0]['prop_id'].split(".")[0]
    button_index = json.loads(button_id)["index"]
    button_type = json.loads(button_id)["type"]

    selected_version = None
    selected_language = None

    if button_type == 'dynamic-version':
        selected_version = ARC_VERSION_LIST[button_index]
        if selected_version_data and selected_version == selected_version_data.get('selected_version', None):
            return dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, False
        if selected_language_data:
            selected_language = selected_language_data.get('selected_language')
        else:
            selected_language = 'English'

    elif button_type == 'dynamic-language':
        selected_language = language_list_data[button_index]
        if selected_language_data and selected_language == selected_language_data.get('selected_language', None):
            return dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, False
        selected_version = selected_version_data.get('selected_version')

    try:
        df_version, version_commit, version_presets, version_accordion_items = get_version_language_related_data(
            selected_version, selected_language)
        logger.info(f'selected_version: {selected_version}')
        logger.info(f'selected_language: {selected_language}')
        logger.info(f'version_presets: {version_presets}')

        return (
            {'selected_version': selected_version},
            {'selected_language': selected_language},
            {'commit': version_commit},
            version_accordion_items,
            version_presets,
            df_version.to_json(date_format='iso', orient='split'),
            True
        )
    except json.JSONDecodeError:
        return dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, False


@app.callback(
    Output("dropdown-ARC_version_input", "value"),
    [
        Input('selected-version-store', 'data')
    ]
)
def update_input_version(data):
    if data is None:
        return dash.no_update
    return data.get('selected_version')


@app.callback(
    Output("dropdown-ARC_language_input", "value"),
    [
        Input('selected-language-store', 'data')
    ]
)
def update_input_language(data):
    if data is None:
        return dash.no_update
    return data.get('selected_language')


@app.callback(
    Output("dropdown-ARC-language-menu", "children"),
    Output("language-list-store", "data"),
    [
        Input('selected-version-store', 'data'),
    ],
)
def update_language_dropdown(selected_version_data):
    if not selected_version_data:
        return dash.no_update, dash.no_update

    current_version = selected_version_data.get('selected_version', None)
    arc_languages = ArcApiClient().get_arc_language_list_version(current_version)
    arc_language_items = [dbc.DropdownMenuItem(language, id={"type": "dynamic-language", "index": i}) for
                          i, language in enumerate(arc_languages)]
    return arc_language_items, arc_languages


def update_for_template_options(version, language, df_current_datadicc, answer_opt_dict1, answer_opt_dict2,
                                checked_key=None):
    translations_for_language = arc.get_translations(language)
    other_text = translations_for_language['other']

    template_ulist_var = df_current_datadicc.loc[df_current_datadicc['Type'].isin(['user_list', 'multi_list'])]

    for index_tem_ul, row_tem_ul in template_ulist_var.iterrows():
        dict1_options = []
        dict2_options = []
        t_u_list = row_tem_ul['List']
        list_options = ArcApiClient().get_dataframe_arc_list_version_language(version, language,
                                                                              t_u_list.replace('_', '/'))

        cont_lo = 1
        select_answer_options = ''

        NOT_select_answer_options = ''
        for index, row in list_options.iterrows():
            if cont_lo == 88:
                cont_lo = 89
            elif cont_lo == 99:
                cont_lo = 100

            if checked_key and checked_key in list_options.columns:
                selected_column = checked_key
            else:
                selected_column = 'Selected'

            selected_value = row[selected_column]
            if isinstance(selected_value, str):
                selected_value = float(1) if selected_value.replace(' ', '') == '1' else None

            if pd.notnull(selected_value) and int(selected_value) == 1:
                if row_tem_ul['Type'] == 'user_list':
                    dict1_options.append([str(cont_lo), str(row[list_options.columns[0]]), 1])
                elif row_tem_ul['Type'] == 'multi_list':
                    dict2_options.append([str(cont_lo), str(row[list_options.columns[0]]), 1])
                select_answer_options += str(cont_lo) + ', ' + str(row[list_options.columns[0]]) + ' | '
            else:
                if row_tem_ul['Type'] == 'user_list':
                    dict1_options.append([str(cont_lo), str(row[list_options.columns[0]]), 0])
                elif row_tem_ul['Type'] == 'multi_list':
                    dict2_options.append([str(cont_lo), str(row[list_options.columns[0]]), 0])
                NOT_select_answer_options += str(cont_lo) + ', ' + str(row[list_options.columns[0]]) + ' | '
            cont_lo += 1
        df_current_datadicc.loc[df_current_datadicc['Variable'] == row_tem_ul[
            'Variable'], 'Answer Options'] = select_answer_options + '88, ' + other_text
        if row_tem_ul['Variable'] + '_otherl2' in list(df_current_datadicc['Variable']):
            df_current_datadicc.loc[df_current_datadicc['Variable'] == row_tem_ul[
                'Variable'] + '_otherl2', 'Answer Options'] = NOT_select_answer_options + '88, ' + other_text

        if row_tem_ul['Type'] == 'user_list':
            answer_opt_dict1.append([row_tem_ul['Variable'], dict1_options])
        elif row_tem_ul['Type'] == 'multi_list':
            answer_opt_dict2.append([row_tem_ul['Variable'], dict2_options])
    return df_current_datadicc, answer_opt_dict1, answer_opt_dict2


def get_checked_template_list(grouped_presets_dict, checked_values_list):
    output = []
    for section, item_checked_list in zip(grouped_presets_dict.keys(), checked_values_list):
        if item_checked_list:
            for item_checked in item_checked_list:
                output.append([section, item_checked.replace(' ', '_')])
    return output


@app.callback(
    [
        Output('tree_items_container', 'children'),
        Output('current_datadicc-store', 'data', allow_duplicate=True),
        Output('ulist_variable_choices-store', 'data', allow_duplicate=True),
        Output('multilist_variable_choices-store', 'data', allow_duplicate=True)
    ],
    [
        Input({'type': 'template_check', 'index': dash.ALL}, 'value'),
    ],
    [
        State('current_datadicc-store', 'data'),
        State('grouped_presets-store', 'data'),
        State('selected-version-store', 'data'),
        State('selected-language-store', "data")
    ],
    prevent_initial_call=True  # Ensure callback doesn't fire on initialization
)
def update_output(checked_variables, current_datadicc_saved, grouped_presets, selected_version_data,
                  selected_lang_data):
    ctx = dash.callback_context
    df_current_datadicc = pd.read_json(io.StringIO(current_datadicc_saved), orient='split')

    current_version = selected_version_data.get('selected_version', None)
    current_language = selected_lang_data.get('selected_language', None)

    df_version, version_presets, version_commit = arc.getARC(current_version)
    df_version = arc.add_required_datadicc_columns(df_version)
    df_version_language = get_dataframe_arc_language(df_version, current_version, current_language)

    tree_items_data = arc.getTreeItems(df_version_language, current_version)

    if (not ctx.triggered) | (all(not sublist for sublist in checked_variables)):
        tree_items = html.Div(
            dash_treeview_antd.TreeView(
                id='input',
                multiple=False,
                checkable=True,
                checked=[],
                expanded=[],
                data=tree_items_data),
            id='tree_items_container',
            className='tree-item',
        )
        return (tree_items,
                dash.no_update,
                dash.no_update,
                dash.no_update)

    if current_version is None or grouped_presets is None:
        raise PreventUpdate  # Prevent update if data is missing

    logger.info(f'checked_variables: {checked_variables}')
    logger.info(f'grouped_presets: {grouped_presets}')
    checked_template_list = get_checked_template_list(grouped_presets, checked_variables)

    checked = []
    templa_answer_opt_dict1 = []
    templa_answer_opt_dict2 = []

    if len(checked_template_list) > 0:
        for ps in checked_template_list:
            checked_key = 'preset_' + ps[0] + '_' + ps[1]
            if checked_key in df_current_datadicc:
                checked = checked + list(
                    df_current_datadicc['Variable'].loc[df_current_datadicc[checked_key].notnull()])

            df_current_datadicc, templa_answer_opt_dict1, templa_answer_opt_dict2 = update_for_template_options(
                current_version, current_language, df_current_datadicc, templa_answer_opt_dict1,
                templa_answer_opt_dict2,
                checked_key=checked_key)

    else:
        df_current_datadicc, templa_answer_opt_dict1, templa_answer_opt_dict2 = update_for_template_options(
            current_version, current_language, df_current_datadicc, templa_answer_opt_dict1, templa_answer_opt_dict2)

    tree_items = html.Div(
        dash_treeview_antd.TreeView(
            id='input',
            multiple=False,
            checkable=True,
            checked=checked,
            expanded=checked,
            data=tree_items_data),
        id='tree_items_container',
        className='tree-item',
    )

    return (
        tree_items,
        df_current_datadicc.to_json(date_format='iso', orient='split'),
        json.dumps(templa_answer_opt_dict1),
        json.dumps(templa_answer_opt_dict2)
    )


@app.callback(
    [
        Output('modal', 'is_open', allow_duplicate=True),
        Output('current_datadicc-store', 'data'),
        Output('ulist_variable_choices-store', 'data'),
        Output('multilist_variable_choices-store', 'data'),
        Output('tree_items_container', 'children', allow_duplicate=True)
    ],
    [
        Input('modal_submit', 'n_clicks'),
        Input('modal_cancel', 'n_clicks'),
    ],
    [
        State('current_datadicc-store', 'data'),
        State('modal_title', 'children'),
        State('options-checklist', 'value'),
        State('input', 'checked'),
        State('ulist_variable_choices-store', 'data'),
        State('multilist_variable_choices-store', 'data')
    ],
    prevent_initial_call=True
)
def on_modal_button_click(submit_n_clicks, cancel_n_clicks, current_datadicc_saved, question, checked_options, checked,
                          ulist_variable_choices_saved, multilist_variable_choices_saved):
    dict1 = json.loads(ulist_variable_choices_saved)
    dict2 = json.loads(multilist_variable_choices_saved)

    ctx = callback_context
    current_datadicc = pd.read_json(io.StringIO(current_datadicc_saved), orient='split')

    if not ctx.triggered:
        return dash.no_update

    button_id = ctx.triggered[0]['prop_id'].split('.')[0]

    if button_id == 'modal_submit':

        variable_submited = question.split('[')[1][:-1]
        MODIFIED_LIST.append(variable_submited)
        ulist_variables = [i[0] for i in ULIST_VARIABLE_CHOICES]
        multilist_variables = [i[0] for i in MULTILIST_VARIABLE_CHOICES]
        if (variable_submited in ulist_variables) | (variable_submited in multilist_variables):
            list_options_checked = []
            for lo in checked_options:
                list_options_checked.append(lo.split('_'))

            list_options_checked = pd.DataFrame(data=list_options_checked, columns=['cod', 'Option'])

            new_submited_options = []
            new_submited_line = []
            position = 0
            for var_select in dict1:
                if (var_select[0] == variable_submited):
                    select_answer_options = ''
                    NOT_select_answer_options = ''
                    for option_var_select in (var_select[1]):
                        if (option_var_select[1] in (list(list_options_checked['Option']))):
                            new_submited_options.append([option_var_select[0], option_var_select[1], 1])
                            select_answer_options += str(option_var_select[0]) + ', ' + str(
                                option_var_select[1]) + ' | '
                        else:
                            new_submited_options.append([option_var_select[0], option_var_select[1], 0])
                            NOT_select_answer_options += str(option_var_select[0]) + ', ' + str(
                                option_var_select[1]) + ' | '
                    new_submited_line.append([var_select, new_submited_options])
                    dict1[position][1] = new_submited_line[0][1]
                    current_datadicc.loc[current_datadicc[
                                             'Variable'] == variable_submited, 'Answer Options'] = select_answer_options + '88, Other'
                    if variable_submited + '_otherl2' in list(current_datadicc['Variable']):
                        current_datadicc.loc[current_datadicc[
                                                 'Variable'] == variable_submited + '_otherl2', 'Answer Options'] = NOT_select_answer_options + '88, Other'

                position += 1
            ulist_variable_choicesSubmit = dict1

            new_submited_options_multi_check = []
            new_submited_line_multi_check = []
            position_multi_check = 0
            for var_select_multi_check in dict2:
                if (var_select_multi_check[0] == variable_submited):
                    select_answer_options_multi_check = ''
                    NOT_select_answer_options_multi_check = ''
                    for option_var_select_multi_check in (var_select_multi_check[1]):
                        if (option_var_select_multi_check[1] in (list(list_options_checked['Option']))):
                            new_submited_options_multi_check.append(
                                [option_var_select_multi_check[0], option_var_select_multi_check[1], 1])
                            select_answer_options_multi_check += str(option_var_select_multi_check[0]) + ', ' + str(
                                option_var_select_multi_check[1]) + ' | '
                        else:
                            new_submited_options_multi_check.append(
                                [option_var_select_multi_check[0], option_var_select_multi_check[1], 0])
                            NOT_select_answer_options_multi_check += str(option_var_select_multi_check[0]) + ', ' + str(
                                option_var_select_multi_check[1]) + ' | '
                    new_submited_line_multi_check.append([var_select_multi_check, new_submited_options_multi_check])
                    dict2[position_multi_check][1] = new_submited_line_multi_check[0][1]
                    current_datadicc.loc[current_datadicc[
                                             'Variable'] == variable_submited, 'Answer Options'] = select_answer_options_multi_check + '88, Other'
                    if variable_submited + '_otherl2' in list(current_datadicc['Variable']):
                        current_datadicc.loc[current_datadicc[
                                                 'Variable'] == variable_submited + '_otherl2', 'Answer Options'] = NOT_select_answer_options_multi_check + '88, Other'
                position_multi_check += 1
            multilist_variable_choicesSubmit = dict2

            checked.append(variable_submited)
            tree_items = html.Div(
                dash_treeview_antd.TreeView(
                    id='input',
                    multiple=False,
                    checkable=True,
                    checked=current_datadicc['Variable'].loc[current_datadicc['Variable'].isin(checked)],
                    expanded=current_datadicc['Variable'].loc[current_datadicc['Variable'].isin(checked)],
                    data=TREE_ITEMS_DATA),
                id='tree_items_container',
                className='tree-item',
            )
            return False, current_datadicc.to_json(date_format='iso', orient='split'), json.dumps(
                ulist_variable_choicesSubmit), json.dumps(multilist_variable_choicesSubmit), tree_items
        else:
            return False, dash.no_update, dash.no_update, dash.no_update, dash.no_update

    elif button_id == 'modal_cancel':
        # Just close the modal without doing anything else
        return False, dash.no_update, dash.no_update, dash.no_update, dash.no_update

    return dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update


@app.callback(
    Output("output-files-store", "data"),
    Input("output-files-checkboxes", "value")
)
def update_store(checked_values):
    return checked_values


def get_trigger_id(ctx):
    # Check which input triggered the callback
    if not ctx.triggered:
        trigger_id = 'No clicks yet'
    else:
        trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]
    return trigger_id


def get_crf_name(crf_name, checked_values):
    if crf_name is not None:
        if isinstance(crf_name, list):
            crf_name = crf_name[0]
    else:
        extracted_text = [item for sublist in checked_values for item in sublist if item]
        if len(extracted_text) > 0:
            crf_name = extracted_text[0]
    if not crf_name:
        crf_name = 'no_name'
    logger.info(f'crf_name: {crf_name}')
    return crf_name


@app.callback(
    [
        Output("loading-output-generate", "children"),
        Output("download-dataframe-csv", "data"),
        Output("download-compGuide-pdf", "data"),
        Output("download-projectxml-pdf", "data"),
        Output("download-paperlike-pdf", "data")
    ],
    [
        Input("crf_generate", "n_clicks"),
    ],
    [
        State("selected_data-store", "data"),
        State('selected-version-store', 'data'),
        State('selected-language-store', "data"),
        State({'type': 'template_check', 'index': dash.ALL}, "value"),
        State("crf_name", "value"),
        State("output-files-store", "data"),
        State("browser-info-store", "data"),
    ],
    prevent_initial_call=True
)
def on_generate_click(n_clicks, json_data, selected_version_data, selected_language_data, checked_presets, crf_name,
                      output_files, browser_info):
    ctx = dash.callback_context

    if not n_clicks:
        # Return empty or initial state if button hasn't been clicked
        return "", None, None, None, None

    if not any(json.loads(json_data).values()):
        # Nothing ticked
        return "", None, None, None, None

    trigger_id = get_trigger_id(ctx)

    if trigger_id == 'crf_generate':
        date = datetime.today().strftime('%Y-%m-%d')
        crf_name = get_crf_name(crf_name, checked_presets)

        selected_variables_fromData = pd.read_json(io.StringIO(json_data), orient='split')
        currentVersion = selected_version_data.get('selected_version', None)
        language = selected_language_data.get('selected_language', None)

        df = arc.generateCRF(selected_variables_fromData)
        pdf_crf = paper_crf.generate_pdf(df, currentVersion, crf_name, language)
        pdf_data = paper_crf.generate_completionguide(selected_variables_fromData, currentVersion, crf_name)

        # CSV
        csv_buffer = io.BytesIO()
        df.loc[df['Field Type'] == 'descriptive', 'Field Label'] = df.loc[
            df['Field Type'] == 'descriptive', 'Field Label'].apply(
            lambda
                x: f'<div class="rich-text-field-label"><h5 style="text-align: center;"><span style="color: #236fa1;">{x}</span></h5></div>')
        if language != 'English':
            df['Form Name'] = df['Form Name'].apply(lambda x: unidecode(str(x)))

        df.to_csv(csv_buffer, index=False, encoding='utf8')

        csv_buffer.seek(0)

        # XML
        xml_file_name = 'ISARIC Clinical Characterisation Setup.xml'
        xml_file_path = f'{CONFIG_DIR_FULL}/{xml_file_name}'
        with open(xml_file_path, 'rb') as file:
            xml_content = file.read()

        # if safari
        is_safari = browser_info and "Safari" in browser_info and "Chrome" not in browser_info

        if is_safari:
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, 'w') as zip_file:
                if 'redcap_csv' in output_files:
                    zip_file.writestr(f"{crf_name}_DataDictionary_{date}.csv", csv_buffer.getvalue())
                if 'paper_like' in output_files:
                    zip_file.writestr(f"{crf_name}_Completion_Guide_{date}.pdf", pdf_data)
                    zip_file.writestr(f"{crf_name}_paperlike_{date}.pdf", pdf_crf)
                if 'redcap_xml' in output_files:
                    zip_file.writestr(xml_file_name, xml_content)
            zip_buffer.seek(0)
            return "", dcc.send_bytes(zip_buffer.getvalue(), f"{crf_name}_bundle_{date}.zip"), None, None, None

        return (
            "",
            dcc.send_bytes(csv_buffer.getvalue(),
                           f"{crf_name}_DataDictionary_{date}.csv") if 'redcap_csv' in output_files else None,
            dcc.send_bytes(pdf_data,
                           f"{crf_name}_Completion_Guide_{date}.pdf") if 'paper_like' in output_files else None,
            dcc.send_bytes(xml_content, xml_file_name) if 'redcap_xml' in output_files else None,
            dcc.send_bytes(pdf_crf, f"{crf_name}_paperlike_{date}.pdf") if 'paper_like' in output_files else None
        )

    else:
        return "", None, None, None, None


@app.callback(
    [
        Output('loading-output-save', 'children'),
        Output('save-crf', 'data'),
    ],
    [
        Input('crf_save', 'n_clicks'),
        Input({'type': 'template_check', 'index': dash.ALL}, 'value'),
        Input('input', 'checked'),
    ],
    [
        State('current_datadicc-store', 'data'),
        State('selected-version-store', 'data'),
        State('selected-language-store', 'data'),
        State('crf_name', 'value'),
    ],
    prevent_initial_call=True
)
def on_save_click(n_clicks, checked_template_values, checked_variables, current_datadicc_saved, selected_version_data,
                  selected_language_data, crf_name):
    ctx = dash.callback_context

    if not n_clicks or not checked_variables:
        return '', None

    trigger_id = get_trigger_id(ctx)

    if trigger_id == 'crf_save':
        crf_name = get_crf_name(crf_name, [])

        current_version = selected_version_data.get('selected_version', None)
        current_language = selected_language_data.get('selected_language', None)
        date = datetime.today().strftime('%Y-%m-%d')
        # Naming convention expected when uploading
        version_string = current_version.replace('.', '_')
        filename_csv = f'template_{crf_name}_{version_string}_{current_language}_{date}.csv'

        df_current_datadicc = pd.read_json(io.StringIO(current_datadicc_saved), orient='split')
        df_save = df_current_datadicc.loc[df_current_datadicc['Variable'].isin(checked_variables)][['Variable']]

        output = io.BytesIO()
        df_save.to_csv(output, index=False, encoding='utf8')
        output.seek(0)

        return '', dcc.send_bytes(output.getvalue(), filename_csv)
    else:
        return '', None


@app.callback(
    [
        Output('upload-version-store', 'data', allow_duplicate=True),
        Output('upload-language-store', 'data', allow_duplicate=True),
    ],
    [
        Input('upload-crf', 'filename'),
        Input('upload-crf', 'contents'),
    ],
    prevent_initial_call=True
)
def on_upload_crf(filename, file_contents):
    if filename:
        try:
            upload_version = re.search(r'v\d_\d_\d', filename).group(0)
            upload_language = filename.split(f'{upload_version}_')[1].split('_')[0]
        except AttributeError as e:
            logger.error(e)
            raise AttributeError(f'Failed to determine ARC version and/or language from file {filename}')
        return (
            {'upload_version': upload_version.replace('_', '.')},
            {'upload_language': upload_language},
        )

    return dash.no_update


@app.callback(
    [
        Output('selected-version-store', 'data', allow_duplicate=True),
        Output('selected-language-store', 'data', allow_duplicate=True),
        Output('commit-store', 'data', allow_duplicate=True),
        Output('preset-accordion', 'children', allow_duplicate=True),
        Output('grouped_presets-store', 'data', allow_duplicate=True),
        Output('current_datadicc-store', 'data', allow_duplicate=True),
        Output('upload-crf-ready', 'data'),
        Output('crf_name', 'value', allow_duplicate=True),
    ],
    [
        Input('upload-version-store', 'data'),
        Input('upload-language-store', 'data'),
    ],
    [
        State('selected-version-store', 'data'),
        State('selected-language-store', 'data'),
    ],
    prevent_initial_call=True
)
def load_upload_arc_version(upload_version_data, upload_language_data, selected_version_data, selected_language_data):
    ctx = dash.callback_context

    if not ctx.triggered:
        return dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, False, None

    upload_version = upload_version_data.get('upload_version', None)
    upload_language = upload_language_data.get('upload_language', None)

    if ((selected_version_data and upload_version == selected_version_data.get('selected_version', None)) and (
            selected_language_data and upload_language == selected_language_data.get('selected_language', None))):
        return dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, False, None

    try:
        df_upload_version, version_commit, version_grouped_presets, version_accordion_items = get_version_language_related_data(
            upload_version, upload_language)
        logger.info(f'upload_version: {upload_version}')
        logger.info(f'upload_language: {upload_language}')
        return (
            {'selected_version': upload_version},
            {'selected_language': upload_language},
            {'commit': version_commit},
            version_accordion_items,
            version_grouped_presets,
            df_upload_version.to_json(date_format='iso', orient='split'),
            True,
            None,
        )
    except json.JSONDecodeError:
        return dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, False, None


@app.callback(
    [
        Output('tree_items_container', 'children', allow_duplicate=True),
        Output('current_datadicc-store', 'data', allow_duplicate=True),
        Output('ulist_variable_choices-store', 'data', allow_duplicate=True),
        Output('multilist_variable_choices-store', 'data', allow_duplicate=True),
        Output('upload-crf', 'contents'),
    ],
    [
        Input('upload-crf-ready', 'data'),
    ],
    [
        State('upload-version-store', 'data'),
        State('upload-language-store', 'data'),
        State('upload-crf', 'contents'),
        State('current_datadicc-store', 'data'),
    ],
    prevent_initial_call=True
)
def update_output_upload_crf(upload_crf_ready, upload_version_data, upload_language_data, upload_crf_contents,
                             current_datadicc_saved):
    ctx = dash.callback_context

    if not ctx.triggered:
        return dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update

    upload_version = upload_version_data.get('upload_version', None)
    upload_language = upload_language_data.get('upload_language', None)
    upload_type, upload_string = upload_crf_contents.split(',')
    upload_decoded = base64.b64decode(upload_string)
    df_upload = pd.read_csv(io.StringIO(upload_decoded.decode('utf-8')))
    checked = list(df_upload['Variable'])

    df_current_datadicc = pd.read_json(io.StringIO(current_datadicc_saved), orient='split')
    tree_items_current_datadicc = arc.getTreeItems(df_current_datadicc, upload_version)

    tree_items = html.Div(
        dash_treeview_antd.TreeView(
            id='input',
            multiple=False,
            checkable=True,
            checked=checked,
            expanded=checked,
            data=tree_items_current_datadicc),
        id='tree_items_container',
        className='tree-item',
    )

    upload_answer_opt_dict1 = []
    upload_answer_opt_dict2 = []

    df_current_datadicc, upload_answer_opt_dict1, upload_answer_opt_dict2 = update_for_template_options(
        upload_version, upload_language, df_current_datadicc, upload_answer_opt_dict1, upload_answer_opt_dict2)

    return (
        tree_items,
        df_current_datadicc.to_json(date_format='iso', orient='split'),
        json.dumps(upload_answer_opt_dict1),
        json.dumps(upload_answer_opt_dict2),
        None,
    )


@app.callback(
    Output('row2_options', 'children'),
    [Input('row1_radios', 'value')]
)
def update_row2_options(selected_value):
    if selected_value == "Characterisation":
        options = [
            {"label": "What are the case defining features?", "value": "CD_Features"},
            {"label": "What is the spectrum of clinical features in this disease?",
             "value": "Spectrum_Clinical_Features"},
        ]
    elif selected_value == "Risk/Prognosis":
        options = [
            {"label": "What are the clinical features occurring in those with patient outcome?",
             "value": "Clinical_Features_Patient_Outcome"},
            {"label": "What are the risk factors for patient outcome?", "value": "Risk_Factors_Patient_Outcome"},
        ]
    elif selected_value == "Clinical Management":
        options = [
            {"label": "What treatment/intervention are received by those with patient outcome?",
             "value": "Treatment_Intervention_Patient_Outcome"},
            {"label": "What proportion of patients with clinical feature are receiving treatment/intervention?",
             "value": "Clinical_Features_Treatment_Intervention"},
            {"label": "What proportion of patient outcome recieved treatment/intervention?",
             "value": "Patient_Outcome_Treatment_Intervention"},
            {"label": "What duration of treatment/intervention is being used in patient outcome?",
             "value": "Duration_Treatment_Intervention_Patient_Outcome"},

        ]
    else:
        options = []

    question_options = html.Div(
        [
            dbc.RadioItems(
                id="row2_radios",
                className="btn-group",
                inputClassName="btn-check",
                labelClassName="btn btn-outline-primary",
                labelCheckedClassName="active",
                options=options,
            ),
            html.Div(id="rq_questions_div"),
        ],
        className="radio-group",
    )

    return question_options


def init_grid(dataframe, id_grid):
    # Define the new column definitions
    columnDefs = [
        {'field': 'Form'},
        {'field': 'Section'},
        {'field': 'Question'},
    ]

    # Convert the DataFrame to a dictionary in a format suitable for Dash AgGrid
    # Use `records` to get a list of dict, each representing a row in the DataFrame
    rowData = dataframe.to_dict('records')

    return dag.AgGrid(
        id=id_grid,
        rowData=rowData,
        columnDefs=columnDefs,
        defaultColDef={'resizable': True},
        columnSize="sizeToFit",
        dashGridOptions={
            "rowDragManaged": True,
            "rowDragEntireRow": True,
            "rowDragMultiRow": True,
            "rowSelection": "multiple",
            "suppressMoveWhenRowDragging": True
        },
        # Since the rowClassRules were based on color, you might want to remove or modify this part
        # You can define new rules based on 'form', 'section', or 'label' if needed
        rowClassRules={},
        getRowId="params.data.id",  # Ensure your DataFrame includes an 'id' column for this to work
    )


def createFeatureSelection(id_so, title, feat_options):
    # This function creates a feature selection component with dynamic IDs.
    return html.Div([
        html.Div(id={'type': 'feature_title', 'index': id_so}, children=title, style={"cursor": "pointer"}),
        dbc.Fade(
            html.Div([
                dcc.Checklist(
                    id={'type': 'feature_selectall', 'index': id_so},
                    options=[{'label': 'Select all', 'value': 'all'}],
                    value=['all']
                ),
                dcc.Checklist(
                    id={'type': 'feature_checkboxes', 'index': id_so},
                    options=feat_options,
                    value=[option['value'] for option in feat_options],
                    style={'overflowY': 'auto', 'maxHeight': '100px'}
                )
            ]),
            id={'type': 'feature_fade', 'index': id_so},
            is_in=False,
            appear=False,
        )
    ])


def feature_text(current_datadicc, selected_variables, features):
    selected_variables = selected_variables.copy()
    selected_variables = selected_variables.loc[selected_variables['Variable'].isin(features['Variable'])]
    if (selected_variables is None):
        return ''
    else:
        text = ''
        selected_features = current_datadicc.loc[current_datadicc['Variable'].isin(selected_variables['Variable'])]
        for sec in selected_features['Section'].unique():
            # Add section title in bold and a new line
            text += f"\n\n**{sec}**\n"
            for label in selected_features['Question'].loc[selected_features['Section'] == sec]:
                # Add each label as a bullet point with a new line
                text += f"  - {label}\n"
        return text


def feature_accordion(features, id_feat, selected):
    feat_accordion_items = []
    cont = 0

    for sec in features['Section'].unique():
        if selected is None:
            selection = []
        else:
            selection = selected['Variable'].loc[selected['Section'] == sec]
            # For each group, create a checklist
        checklist = dbc.Checklist(
            options=[{"label": row['Question'], "value": row['Variable']} for _, row in
                     features.loc[features['Section'] == sec].iterrows()],
            value=selection,
            id=id_feat + '_' + f'checklist-{str(cont)}',
            switch=True,
        )
        cont += 1
        # Create an accordion item with the checklist
        feat_accordion_items.append(
            dbc.AccordionItem(
                title=sec.split(":")[0],
                children=html.Div(checklist, style={'height': '100px', 'overflowY': 'auto'})
            )
        )
    return dbc.Accordion(feat_accordion_items)


def paralel_elements(features, id_feat, current_datadicc, selected_variables):
    text = feature_text(current_datadicc, selected_variables, features)
    accord = feature_accordion(features, id_feat, selected=selected_variables)

    pararel_features = html.Div([
        # First column with the title and the Available Columns table
        html.Div([
            html.H5('Available Features', style={'textAlign': 'center'}),
            accord

        ], style={'width': '49%', 'display': 'inline-block', 'verticalAlign': 'top'}),

        # Second column with the buttons
        html.Div(style={'width': '1%', 'display': 'inline-block', 'textAlign': 'center'}),

        # Third column with the title and the Display Columns table
        html.Div([
            html.H5('Selected Features', style={'textAlign': 'center'}),
            dcc.Markdown(id=id_feat + '_text-content', children=text,
                         style={'height': '300px', 'overflowY': 'scroll', 'border': '1px solid #ddd', 'padding': '10px',
                                'color': 'black'}),

        ], style={'width': '50%', 'display': 'inline-block', 'verticalAlign': 'top'}),
    ], style={'width': '100%', 'display': 'flex'})
    return pararel_features


@app.callback(
    [Output('row3_tabs', 'children'), Output('selected_question', 'children')],
    [Input('row2_radios', 'value')],
    [State('selected_data-store', 'data')],
)
def update_row3_content(selected_value, json_data):
    research_question_elements = pd.read_csv(join(CONFIG_DIR_FULL, 'researchQuestions.csv'))

    group_elements = []
    for tq_opGroup in research_question_elements['Option Group'].unique():
        all_elements = []
        for rq_element in research_question_elements['Relavent variable names on ARC'].loc[
            research_question_elements['Option Group'] == tq_opGroup]:
            if type(rq_element) == str:
                for rq_aux in rq_element.split(';'):
                    all_elements.append(rq_aux.strip())
        group_elements.append([tq_opGroup, all_elements])

    group_elements = pd.DataFrame(data=group_elements, columns=['Group Option', 'Variables'])

    if json_data is None:
        selected_variables_fromData = None
    else:
        selected_variables_fromData = pd.read_json(json_data, orient='split')
        selected_variables_fromData = selected_variables_fromData[['Variable', 'Form', 'Section', 'Question']]

    tabs_content = []
    selected_question = ''

    if selected_value == "CD_Features":
        OptionGroup = ["Case Defining Features"]
        caseDefiningVariables = group_elements['Variables'].loc[group_elements['Group Option'].isin(OptionGroup)]
        paralel_elements_features = paralel_elements(
            CURRENT_DATADICC.loc[CURRENT_DATADICC['Variable'].isin(list(caseDefiningVariables.iloc[0]))], 'case_feat',
            CURRENT_DATADICC, selected_variables_fromData)
        tabs_content.append(dbc.Tab(label="Features", children=[html.P(" "), paralel_elements_features]))
        selected_question = "What are the [case defining features]?"

    elif selected_value == "Spectrum_Clinical_Features":
        OptionGroup = ["Clinical Features"]
        clinicalVariables = group_elements['Variables'].loc[group_elements['Group Option'].isin(OptionGroup)]
        paralel_elements_features = paralel_elements(
            CURRENT_DATADICC.loc[CURRENT_DATADICC['Variable'].isin(list(clinicalVariables.iloc[0]))], 'clinic_feat',
            CURRENT_DATADICC, selected_variables_fromData)
        tabs_content.append(dbc.Tab(label="Clinical Features", children=[html.P(" "), paralel_elements_features]))
        selected_question = "What is the spectrum of [clinical features] in this disease?"

    elif selected_value == "Clinical_Features_Patient_Outcome":
        OptionGroup = ["Clinical Features"]
        clinicalVariables = group_elements['Variables'].loc[group_elements['Group Option'].isin(OptionGroup)]
        paralel_elements_features = paralel_elements(
            CURRENT_DATADICC.loc[CURRENT_DATADICC['Variable'].isin(list(clinicalVariables.iloc[0]))], 'clinic_feat',
            CURRENT_DATADICC, selected_variables_fromData)
        OptionGroup = ["Patient Outcome"]
        outcomeVariables = group_elements['Variables'].loc[group_elements['Group Option'].isin(OptionGroup)]
        paralel_elements_outcomes = paralel_elements(
            CURRENT_DATADICC.loc[CURRENT_DATADICC['Variable'].isin(list(outcomeVariables.iloc[0]))], 'outcome',
            CURRENT_DATADICC, selected_variables_fromData)
        tabs_content.append(dbc.Tab(label="Clinical Features", children=[html.P(" "), paralel_elements_features]))
        tabs_content.append(dbc.Tab(label="Patient Outcomes", children=[html.P(" "), paralel_elements_outcomes]))
        selected_question = "What are the [clinical features] occuring in those with [patient outcome]?"

    elif selected_value == "Risk_Factors_Patient_Outcome":
        OptionGroup = ["Risk Factors: Demographics",
                       "Risk Factors: Socioeconomic", "Risk Factors: Comorbidities"]
        riskVariables = group_elements['Variables'].loc[group_elements['Group Option'].isin(OptionGroup)]
        allRiskVarr = []
        for rv in riskVariables:
            allRiskVarr += list(rv)
        paralel_elements_risk = paralel_elements(CURRENT_DATADICC.loc[CURRENT_DATADICC['Variable'].isin(allRiskVarr)],
                                                 'risk', CURRENT_DATADICC, selected_variables_fromData)
        OptionGroup = ["Patient Outcome"]
        outcomeVariables = group_elements['Variables'].loc[group_elements['Group Option'].isin(OptionGroup)]
        paralel_elements_outcomes = paralel_elements(
            CURRENT_DATADICC.loc[CURRENT_DATADICC['Variable'].isin(list(outcomeVariables.iloc[0]))], 'outcome',
            CURRENT_DATADICC, selected_variables_fromData)
        tabs_content.append(dbc.Tab(label="Risk Factors", children=[html.P(" "), paralel_elements_risk]))
        tabs_content.append(dbc.Tab(label="Patient Outcomes", children=[html.P(" "), paralel_elements_outcomes]))
        selected_question = "What are the [risk factors] for [patient outcome]?"

    elif selected_value == "Treatment_Intervention_Patient_Outcome":

        OptionGroup = ["Treatment/Intevention"]
        TreatmentsVariables = group_elements['Variables'].loc[group_elements['Group Option'].isin(OptionGroup)]
        paralel_elements_treatments = paralel_elements(
            CURRENT_DATADICC.loc[CURRENT_DATADICC['Variable'].isin(list(TreatmentsVariables.iloc[0]))], 'treatment',
            CURRENT_DATADICC, selected_variables_fromData)
        OptionGroup = ["Patient Outcome"]
        outcomeVariables = group_elements['Variables'].loc[group_elements['Group Option'].isin(OptionGroup)]
        paralel_elements_outcomes = paralel_elements(
            CURRENT_DATADICC.loc[CURRENT_DATADICC['Variable'].isin(list(outcomeVariables.iloc[0]))], 'outcome',
            CURRENT_DATADICC, selected_variables_fromData)
        tabs_content.append(
            dbc.Tab(label="Treatments/Interventions", children=[html.P(" "), paralel_elements_treatments]))
        tabs_content.append(dbc.Tab(label="Patient Outcomes", children=[html.P(" "), paralel_elements_outcomes]))

        selected_question = "What [treatment/intervention] are received by those with  [patient outcome]?"
    elif selected_value == "Clinical_Features_Treatment_Intervention":

        selected_question = "What proportion of patients with [clinical feature] are receiving [treatment/intervention]?"

        OptionGroup = ["Clinical Features"]
        clinicalVariables = group_elements['Variables'].loc[group_elements['Group Option'].isin(OptionGroup)]
        paralel_elements_features = paralel_elements(
            CURRENT_DATADICC.loc[CURRENT_DATADICC['Variable'].isin(list(clinicalVariables.iloc[0]))], 'clinic_feat',
            CURRENT_DATADICC, selected_variables_fromData)
        tabs_content.append(dbc.Tab(label="Clinical Features", children=[html.P(" "), paralel_elements_features]))
        OptionGroup = ["Treatment/Intevention"]
        TreatmentsVariables = group_elements['Variables'].loc[group_elements['Group Option'].isin(OptionGroup)]
        paralel_elements_treatments = paralel_elements(
            CURRENT_DATADICC.loc[CURRENT_DATADICC['Variable'].isin(list(TreatmentsVariables.iloc[0]))], 'treatment',
            CURRENT_DATADICC, selected_variables_fromData)
        tabs_content.append(
            dbc.Tab(label="Treatments/Interventions", children=[html.P(" "), paralel_elements_treatments]))

    elif selected_value == "Patient_Outcome_Treatment_Intervention":
        OptionGroup = ["Treatment/Intevention"]
        TreatmentsVariables = group_elements['Variables'].loc[group_elements['Group Option'].isin(OptionGroup)]
        paralel_elements_treatments = paralel_elements(
            CURRENT_DATADICC.loc[CURRENT_DATADICC['Variable'].isin(list(TreatmentsVariables.iloc[0]))], 'treatment',
            CURRENT_DATADICC, selected_variables_fromData)
        tabs_content.append(
            dbc.Tab(label="Treatments/Interventions", children=[html.P(" "), paralel_elements_treatments]))

        OptionGroup = ["Patient Outcome"]
        outcomeVariables = group_elements['Variables'].loc[group_elements['Group Option'].isin(OptionGroup)]
        paralel_elements_outcomes = paralel_elements(
            CURRENT_DATADICC.loc[CURRENT_DATADICC['Variable'].isin(list(outcomeVariables.iloc[0]))], 'outcome',
            CURRENT_DATADICC, selected_variables_fromData)
        tabs_content.append(dbc.Tab(label="Patient Outcomes", children=[html.P(" "), paralel_elements_outcomes]))

        selected_question = "What proportion of [patient outcome] recieved [treatment/intervention]?"
    elif selected_value == "Duration_Treatment_Intervention_Patient_Outcome":
        OptionGroup = ["Treatment/Intevention"]
        TreatmentsVariables = group_elements['Variables'].loc[group_elements['Group Option'].isin(OptionGroup)]
        paralel_elements_treatments = paralel_elements(
            CURRENT_DATADICC.loc[CURRENT_DATADICC['Variable'].isin(list(TreatmentsVariables.iloc[0]))], 'treatment',
            CURRENT_DATADICC, selected_variables_fromData)
        tabs_content.append(
            dbc.Tab(label="Treatments/Interventions", children=[html.P(" "), paralel_elements_treatments]))

        OptionGroup = ["Patient Outcome"]
        outcomeVariables = group_elements['Variables'].loc[group_elements['Group Option'].isin(OptionGroup)]
        paralel_elements_outcomes = paralel_elements(
            CURRENT_DATADICC.loc[CURRENT_DATADICC['Variable'].isin(list(outcomeVariables.iloc[0]))], 'outcome',
            CURRENT_DATADICC, selected_variables_fromData)
        tabs_content.append(dbc.Tab(label="Patient Outcomes", children=[html.P(" "), paralel_elements_outcomes]))
        selected_question = "What duration of [treatment/intervention] is being used in [patient outcome]?"

    parts = re.split(r'(\[.*?\])', selected_question)  # Split by text inside brackets, keeping the brackets

    styled_parts = []
    for part in parts:
        if part.startswith('[') and part.endswith(']'):
            # Text inside brackets, apply red color
            styled_parts.append(html.Span(part, style={'color': '#BA0225'}))
        else:
            # Regular text, no additional styling needed
            styled_parts.append(html.Span(part))
    # Add more conditions as necessary for other options

    return tabs_content, styled_parts


@app.callback(
    Output('case_feat_text-content', 'children'),
    [Input(f'case_feat_checklist-{key}', 'value') for key in range(4)],
    prevent_initial_call=True
)
def update_Researh_questions_grid(*args):
    checked_values = args
    text = ''
    all_checked = []
    for cck_v in checked_values:
        for element in cck_v:
            all_checked.append(element)
    selected_features = CURRENT_DATADICC.loc[CURRENT_DATADICC['Variable'].isin(all_checked)]
    for sec in selected_features['Section'].unique():
        # Add section title in bold and a new line
        text += f"\n\n**{sec}**\n"
        for label in selected_features['Question'].loc[selected_features['Section'] == sec]:
            # Add each label as a bullet point with a new line
            text += f"  - {label}\n"
    return text


@app.callback(
    Output('clinic_feat_text-content', 'children'),
    [Input(f'clinic_feat_checklist-{key}', 'value') for key in range(8)],
    prevent_initial_call=True
)
def update_ClenicalFeat_questions_grid(*args):
    checked_values = args
    text = ''
    all_checked = []
    for cck_v in checked_values:
        for element in cck_v:
            all_checked.append(element)
    selected_features = CURRENT_DATADICC.loc[CURRENT_DATADICC['Variable'].isin(all_checked)]
    for sec in selected_features['Section'].unique():
        # Add section title in bold and a new line
        text += f"\n\n**{sec}**\n"
        for label in selected_features['Question'].loc[selected_features['Section'] == sec]:
            # Add each label as a bullet point with a new line
            text += f"  - {label}\n"
    return text


@app.callback(
    Output('outcome_text-content', 'children'),
    [Input(f'outcome_checklist-{key}', 'value') for key in range(4)],
    prevent_initial_call=True
)
def update_outcome_questions_grid(*args):
    checked_values = args
    text = ''
    all_checked = []
    for cck_v in checked_values:
        for element in cck_v:
            all_checked.append(element)
    selected_features = CURRENT_DATADICC.loc[CURRENT_DATADICC['Variable'].isin(all_checked)]
    for sec in selected_features['Section'].unique():
        # Add section title in bold and a new line
        text += f"\n\n**{sec}**\n"
        for label in selected_features['Question'].loc[selected_features['Section'] == sec]:
            # Add each label as a bullet point with a new line
            text += f"  - {label}\n"
    return text


@app.callback(
    Output('risk_text-content', 'children'),
    [Input(f'risk_checklist-{key}', 'value') for key in range(7)],
    prevent_initial_call=True
)
def update_risk_questions_grid(*args):
    checked_values = args
    text = ''
    all_checked = []
    for cck_v in checked_values:
        for element in cck_v:
            all_checked.append(element)
    selected_features = CURRENT_DATADICC.loc[CURRENT_DATADICC['Variable'].isin(all_checked)]
    for sec in selected_features['Section'].unique():
        # Add section title in bold and a new line
        text += f"\n\n**{sec}**\n"
        for label in selected_features['Question'].loc[selected_features['Section'] == sec]:
            # Add each label as a bullet point with a new line
            text += f"  - {label}\n"
    return text


@app.callback(
    Output('treatment_text-content', 'children'),
    [Input(f'treatment_checklist-{key}', 'value') for key in range(2)],
    prevent_initial_call=True
)
def update_risk_questions_grid(*args):
    checked_values = args
    text = ''
    all_checked = []
    for cck_v in checked_values:
        for element in cck_v:
            all_checked.append(element)
    selected_features = CURRENT_DATADICC.loc[CURRENT_DATADICC['Variable'].isin(all_checked)]
    for sec in selected_features['Section'].unique():
        # Add section title in bold and a new line
        text += f"\n\n**{sec}**\n"
        for label in selected_features['Question'].loc[selected_features['Section'] == sec]:
            # Add each label as a bullet point with a new line
            text += f"  - {label}\n"
    return text


@app.callback(
    [Output('rq_modal', 'is_open', allow_duplicate=True), Output('row3_tabs', 'children', allow_duplicate=True),
     Output('row1_radios', 'value'), Output('row2_radios', 'value')],
    [Input('rq_modal_submit', 'n_clicks'), Input('rq_modal_cancel', 'n_clicks')],
    prevent_initial_call=True
)
def on_rq_modal_button_click(submit_n_clicks, cancel_n_clicks):
    ctx = callback_context
    if not ctx.triggered:
        return dash.no_update

    button_id = ctx.triggered[0]['prop_id'].split('.')[0]

    if button_id == 'rq_modal_submit':
        return False, [], [], []
    elif button_id == 'rq_modal_cancel':
        # Close the modal and clear its content
        return False, [], [], []
    else:
        return dash.no_update


if __name__ == "__main__":
    app.run_server(debug=True, use_reloader=False)
    # app.run_server(debug=True, host='0.0.0.0', port='8080')#change for deploy
