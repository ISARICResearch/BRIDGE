import io
import json
import re
from datetime import datetime
from os.path import join, abspath, dirname
from urllib.parse import parse_qs, urlparse

import dash
import dash_ag_grid as dag
import dash_bootstrap_components as dbc
import dash_treeview_antd
import pandas as pd
from dash import callback_context, dcc, html, Input, Output, State
from dash.exceptions import PreventUpdate

from src import generate_form, paper_crf, arc, bridge_modals, index
from src.bridge_main import MainContent, NavBar, SideBar, Settings, Presets, TreeItems

pd.options.mode.copy_on_write = True

CONFIG_DIR_FULL = join(dirname(abspath(__file__)), 'assets', 'config_files')
ASSETS_DIR = 'assets'
ICONS_DIR = f'{ASSETS_DIR}/icons'
LOGOS_DIR = f'{ASSETS_DIR}/logos'
SCREENSHOTS_DIR = f'{ASSETS_DIR}/screenshots'

app = dash.Dash(__name__,
                external_stylesheets=[dbc.themes.BOOTSTRAP, 'https://use.fontawesome.com/releases/v5.8.1/css/all.css'],
                suppress_callback_exceptions=True)
server = app.server
app.title = 'BRIDGE'

modified_list = []

versions, recentVersion = arc.getARCVersions()

currentVersion = recentVersion
current_datadicc, presets, commit = arc.getARC(recentVersion)
print('Beginning')

current_datadicc[['Sec', 'vari', 'mod']] = current_datadicc['Variable'].str.split('_', n=2, expand=True)
current_datadicc[['Sec_name', 'Expla']] = current_datadicc['Section'].str.split(r'[(|:]', n=1, expand=True)

tree_items_data = arc.getTreeItems(current_datadicc, recentVersion)

# List content Transformation
ARC_lists, list_variable_choices = arc.getListContent(current_datadicc, currentVersion, commit)
current_datadicc = arc.addTransformedRows(current_datadicc, ARC_lists, arc.getVariableOrder(current_datadicc))

# User List content Transformation
ARC_ulist, ulist_variable_choices = arc.getUserListContent(current_datadicc, currentVersion, modified_list, commit)

current_datadicc = arc.addTransformedRows(current_datadicc, ARC_ulist, arc.getVariableOrder(current_datadicc))
ARC_multilist, multilist_variable_choices = arc.getMultuListContent(current_datadicc, currentVersion, commit)

current_datadicc = arc.addTransformedRows(current_datadicc, ARC_multilist, arc.getVariableOrder(current_datadicc))
initial_current_datadicc = current_datadicc.to_json(date_format='iso', orient='split')
initial_ulist_variable_choices = json.dumps(ulist_variable_choices)
initial_multilist_variable_choices = json.dumps(multilist_variable_choices)

ARC_versions = versions

# Grouping presets by the first column
grouped_presets = {}

for key, value in presets:
    grouped_presets.setdefault(key, []).append(value)

initial_grouped_presets = json.dumps(grouped_presets)

app.layout = html.Div(
    [
        dcc.Store(id='show-Take a Look at Our Other Tools', data=True),  # Store to manage which page to display

        dcc.Store(id='current_datadicc-store', data=initial_current_datadicc),
        dcc.Store(id='ulist_variable_choices-store', data=initial_ulist_variable_choices),
        dcc.Store(id='multilist_variable_choices-store', data=initial_multilist_variable_choices),
        dcc.Store(id='grouped_presets-store', data=initial_grouped_presets),
        dcc.Store(id='tree_items_data-store', data=initial_grouped_presets),

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
        dcc.Store(id='selected-version-store'),
        dcc.Store(id='commit-store'),
        dcc.Store(id='selected_data-store'),
    ]
)

app = SideBar.add_sidebar(app)


def main_app():
    return html.Div([
        NavBar.navbar,
        SideBar.sidebar,
        Settings(ARC_versions).settings_column,
        Presets.preset_column,
        TreeItems(tree_items_data).tree_column,
        MainContent.main_content,
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


####################
# get URL parameter
####################
@app.callback(
    [
        Output('crf_name', 'value'),
        Output({'type': 'template_check', 'index': dash.ALL}, 'value')
    ],
    [Input('templates_checks_ready', 'data')],
    [State('url', 'href')],
    prevent_initial_call=True,
)
def update_output_based_on_url(template_check_flag, href):
    if not template_check_flag:
        return dash.no_update

    if href is None:
        return [''] + [[] for _ in grouped_presets.keys()]

    if '?param=' in href:
        # Parse the URL to extract the parameters
        parsed_url = urlparse(href)
        params = parse_qs(parsed_url.query)

        # Accessing the 'param' parameter
        param_value = params.get('param', [''])[0]  # Default to an empty string if the parameter is not present

        # Example: Split param_value by underscore
        group, value = param_value.split('_') if '_' in param_value else (None, None)

        # Prepare the outputs
        checklist_values = {key: [] for key in grouped_presets.keys()}

        if group in grouped_presets and value in grouped_presets[group]:
            checklist_values[group] = [value]

        # Return the value for 'crf_name' and checklist values
        return [value], [checklist_values[key] for key in grouped_presets.keys()]
    else:
        return dash.no_update


#################################


@app.callback([Output('CRF_representation_grid', 'columnDefs'),
               Output('CRF_representation_grid', 'rowData'),
               Output('selected_data-store', 'data')],
              [Input('input', 'checked')],
              [State('current_datadicc-store', 'data')],
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

                formatted_choices = generate_form.format_choices(row['Answer Options'], row['Type'])
                row['Answer Options'] = formatted_choices
            elif row['Validation'] == 'date_dmy':
                date_str = "[_D_][_D_]/[_M_][_M_]/[_2_][_0_][_Y_][_Y_]"
                row['Answer Options'] = date_str
            else:
                row['Answer Options'] = paper_crf.line_placeholder

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
    Output('options-checklist', 'style'),
    Output('options-list-group', 'style'),
    Output('options-checklist', 'options'),
    Output('options-checklist', 'value'),
    Output('options-list-group', 'children')],
    [Input('input', 'selected')],
    [State('ulist_variable_choices-store', 'data'), State('multilist_variable_choices-store', 'data'),
     State('modal', 'is_open')])
def display_selected(selected, ulist_variable_choices_saved, multilist_variable_choices_saved, is_open):
    dict1 = json.loads(ulist_variable_choices_saved)
    dict2 = json.loads(multilist_variable_choices_saved)
    datatatata = dict1 + dict2

    if (selected is not None):
        if len(selected) > 0:
            if selected[0] in list(current_datadicc['Variable']):
                question = current_datadicc['Question'].loc[current_datadicc['Variable'] == selected[0]].iloc[0]
                definition = current_datadicc['Definition'].loc[current_datadicc['Variable'] == selected[0]].iloc[0]
                completion = \
                    current_datadicc['Completion Guideline'].loc[current_datadicc['Variable'] == selected[0]].iloc[0]
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

                    return True, question + ' [' + selected[0] + ']', definition, completion, {"padding": "20px",
                                                                                               "maxHeight": "250px",
                                                                                               "overflowY": "auto"}, {
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
                    return True, question + ' [' + selected[0] + ']', definition, completion, {"display": "none"}, {
                        "maxHeight": "250px", "overflowY": "auto"}, [], [], options

    return False, '', '', '', {"display": "none"}, {"display": "none"}, [], [], []


@app.callback(Output('output-expanded', 'children'),
              [Input('input', 'expanded')])
def display_expanded(expanded):
    return 'You have expanded {}'.format(expanded)


@app.callback(
    [Output('selected-version-store', 'data', allow_duplicate=True),
     Output('commit-store', 'data', allow_duplicate=True),
     Output('preset-accordion', 'children', allow_duplicate=True),
     Output('grouped_presets-store', 'data'),
     Output('current_datadicc-store', 'data', allow_duplicate=True),
     Output('templates_checks_ready', 'data')],
    [Input({'type': 'dynamic-version', 'index': dash.ALL}, 'n_clicks')],
    [State('selected-version-store', 'data')],  # Obtenemos el valor actual del store
    prevent_initial_call=True  # Evita que se dispare al inicio
)
def store_clicked_item(n_clicks, selected_version_data):
    ctx = dash.callback_context

    # Si no hay cambios (es decir, no hay un input activado), no se hace nada
    if not ctx.triggered:
        return dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, False

    button_id = ctx.triggered[0]['prop_id'].split(".")[0]  # Extraer la ID del botón

    # Revisar si el valor ha cambiado antes de ejecutar el callback
    version_index = json.loads(button_id)["index"]
    new_selected_version = ARC_versions[version_index]

    if new_selected_version == selected_version_data:  # No hay cambios
        return dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, False

    # Si hay un cambio, procesamos la lógica
    try:
        selected_version = new_selected_version
        current_datadicc, presets, commit = arc.getARC(selected_version)
        current_datadicc[['Sec', 'vari', 'mod']] = current_datadicc['Variable'].str.split('_', n=2, expand=True)
        current_datadicc[['Sec_name', 'Expla']] = current_datadicc['Section'].str.split(r'[(|:]', n=1, expand=True)

        ARC_lists, list_variable_choices = arc.getListContent(current_datadicc, selected_version, commit)
        current_datadicc = arc.addTransformedRows(current_datadicc, ARC_lists, arc.getVariableOrder(current_datadicc))

        ARC_ulist, ulist_variable_choices = arc.getUserListContent(current_datadicc, selected_version, modified_list,
                                                                   commit)
        current_datadicc = arc.addTransformedRows(current_datadicc, ARC_ulist, arc.getVariableOrder(current_datadicc))

        ARC_multilist, multilist_variable_choices = arc.getMultuListContent(current_datadicc, selected_version, commit)
        current_datadicc = arc.addTransformedRows(current_datadicc, ARC_multilist,
                                                  arc.getVariableOrder(current_datadicc))

        grouped_presets = {}
        for key, value in presets:
            grouped_presets.setdefault(key, []).append(value)

        accordion_items = [
            dbc.AccordionItem(
                title=key,
                children=dbc.Checklist(
                    options=[{"label": value, "value": value} for value in values],
                    value=[],
                    id={'type': 'template_check', 'index': key},
                    switch=True,
                )
            )
            for key, values in grouped_presets.items()
        ]
        print('this is the selected version in store click', selected_version)
        print('presets in store click', grouped_presets)
        return (
            {'selected_version': selected_version},  # Actualizamos el store con la nueva versión
            {'commit': commit},
            accordion_items,
            grouped_presets,
            current_datadicc.to_json(date_format='iso', orient='split'),
            True
        )
    except json.JSONDecodeError:
        return dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, False


@app.callback(
    Output("dropdown-ARC_version_input", "value"),
    [Input('selected-version-store', 'data')]
)
def update_input(data):
    if data is None:
        return dash.no_update
    return data.get('selected_version')


@app.callback(
    [
        Output('tree_items_container', 'children'),
        Output('current_datadicc-store', 'data', allow_duplicate=True),
        Output('ulist_variable_choices-store', 'data', allow_duplicate=True),
        Output('multilist_variable_choices-store', 'data', allow_duplicate=True)
    ],
    [Input({'type': 'template_check', 'index': dash.ALL}, 'value')],
    [
        State('current_datadicc-store', 'data'),
        State('grouped_presets-store', 'data'),
        State('selected-version-store', 'data')
    ],
    prevent_initial_call=True  # Ensure callback doesn't fire on initialization
)
def update_output(values, current_datadicc_saved, grouped_presets, selected_version_data):
    # Check the context to determine the triggering input
    ctx = dash.callback_context
    currentVersion = selected_version_data.get('selected_version', None)

    current_datadicc_temp, presets, commit = arc.getARC(currentVersion)
    current_datadicc_temp[['Sec', 'vari', 'mod']] = current_datadicc_temp['Variable'].str.split('_', n=2, expand=True)
    current_datadicc_temp[['Sec_name', 'Expla']] = current_datadicc_temp['Section'].str.split(r'[(|:]', n=1,
                                                                                              expand=True)

    tree_items_data = arc.getTreeItems(current_datadicc_temp, currentVersion)
    print('values en update output', values)

    if (not ctx.triggered) | (all(not sublist for sublist in values)):
        tree_items = html.Div(
            dash_treeview_antd.TreeView(
                id='input',
                multiple=False,
                checkable=True,
                checked=[],
                expanded=[],
                data=tree_items_data), id='tree_items_container',
            style={
                'overflow-y': 'auto',  # Vertical scrollbar when needed
                'height': '75vh',  # Fixed height
                'width': '100%',  # Fixed width, or you can specify a value in px
                'white-space': 'normal',  # Allow text to wrap
                'overflow-x': 'hidden',  # Hide overflowed content
                'text-overflow': 'ellipsis',  # Indicate more content with an ellipsis
            }
        )
        return (tree_items,  # Empty content for the tree items container
                dash.no_update,  # Clear the current datadicc-store
                dash.no_update,  # Clear ulist_variable_choices-store
                dash.no_update  # Clear multilist_variable_choices-store
                )

    # Identify the specific component that triggered the callback
    if currentVersion is None or grouped_presets is None:
        raise PreventUpdate  # Prevent update if data is missing

    # Proceed with your logic
    current_datadicc = pd.read_json(io.StringIO(current_datadicc_saved), orient='split')
    currentVersion = selected_version_data.get('selected_version', None)

    current_datadicc_temp, presets, commit = arc.getARC(currentVersion)
    current_datadicc_temp[['Sec', 'vari', 'mod']] = current_datadicc_temp['Variable'].str.split('_', n=2, expand=True)
    current_datadicc_temp[['Sec_name', 'Expla']] = current_datadicc_temp['Section'].str.split(r'[(|:]', n=1,
                                                                                              expand=True)

    tree_items_data = arc.getTreeItems(current_datadicc_temp, currentVersion)

    templa_answer_opt_dict1 = []
    templa_answer_opt_dict2 = []

    checked_values = values
    print('checked_values', checked_values)
    print(' grouped_presets in update output', grouped_presets)
    formatted_output = []
    for key, values in zip(grouped_presets.keys(), checked_values):
        if values:  # Check if the list of values is not empty
            for value in values:
                formatted_output.append([key, value.replace(' ', '_')])
    checked = []
    if len(formatted_output) > 0:
        for ps in formatted_output:
            checked_key = 'preset_' + ps[0] + '_' + ps[1]
            if checked_key in current_datadicc:
                checked = checked + list(current_datadicc['Variable'].loc[current_datadicc[checked_key].notnull()])

            ##########Modificacion para template options in userlist
            template_ulist_var = current_datadicc.loc[current_datadicc['Type'].isin(['user_list', 'multi_list'])]
            print('esta es la version seleccionada', currentVersion)
            root = 'https://raw.githubusercontent.com/ISARICResearch/ARC/'
            for index_tem_ul, row_tem_ul in template_ulist_var.iterrows():
                dict1_options = []
                dict2_options = []
                t_u_list = row_tem_ul['List']
                list_path = root + commit + '/Lists/' + t_u_list.replace('_', '/') + '.csv'
                try:
                    list_options = pd.read_csv(list_path, encoding='latin1')

                except Exception as e:
                    print(f"Failed to fetch remote file due to: {e}. Attempting to read from local file.")
                    continue

                list_options = list_options.sort_values(by=list_options.columns[0], ascending=True)
                cont_lo = 1
                select_answer_options = ''

                NOT_select_answer_options = ''
                for index, row in list_options.iterrows():
                    if cont_lo == 88:
                        cont_lo = 89
                    elif cont_lo == 99:
                        cont_lo = 100

                    if checked_key in list_options.columns:
                        selected_column = checked_key
                    else:
                        selected_column = 'Selected'

                    if (row[selected_column] == 1):
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
                current_datadicc.loc[current_datadicc['Variable'] == row_tem_ul[
                    'Variable'], 'Answer Options'] = select_answer_options + '88, Other'
                if row_tem_ul['Variable'] + '_otherl2' in list(current_datadicc['Variable']):
                    current_datadicc.loc[current_datadicc['Variable'] == row_tem_ul[
                        'Variable'] + '_otherl2', 'Answer Options'] = NOT_select_answer_options + '88, Other'

                if row_tem_ul['Type'] == 'user_list':
                    templa_answer_opt_dict1.append([row_tem_ul['Variable'], dict1_options])
                elif row_tem_ul['Type'] == 'multi_list':
                    templa_answer_opt_dict2.append([row_tem_ul['Variable'], dict2_options])


    else:
        template_ulist_var = current_datadicc.loc[current_datadicc['Type'].isin(['user_list', 'multi_list'])]

        root = 'https://raw.githubusercontent.com/ISARICResearch/ARC/'

        for index_tem_ul, row_tem_ul in template_ulist_var.iterrows():
            dict1_options = []
            dict2_options = []
            t_u_list = row_tem_ul['List']
            list_path = root + commit + '/Lists/' + t_u_list.replace('_', '/') + '.csv'
            try:
                list_options = pd.read_csv(list_path, encoding='latin1')
            except Exception as e:
                print(f"Failed to fetch remote file due to: {e}. Attempting to read from local file.")
                continue

            list_options = list_options.sort_values(by=list_options.columns[0], ascending=True)
            cont_lo = 1
            select_answer_options = ''

            NOT_select_answer_options = ''
            for index, row in list_options.iterrows():
                if cont_lo == 88:
                    cont_lo = 89
                elif cont_lo == 99:
                    cont_lo = 100

                selected_column = 'Selected'

                if (row[selected_column] == 1):
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
            current_datadicc.loc[current_datadicc['Variable'] == row_tem_ul[
                'Variable'], 'Answer Options'] = select_answer_options + '88, Other'
            if row_tem_ul['Variable'] + '_otherl2' in list(current_datadicc['Variable']):
                current_datadicc.loc[current_datadicc['Variable'] == row_tem_ul[
                    'Variable'] + '_otherl2', 'Answer Options'] = NOT_select_answer_options + '88, Other'

            if row_tem_ul['Type'] == 'user_list':
                templa_answer_opt_dict1.append([row_tem_ul['Variable'], dict1_options])
            elif row_tem_ul['Type'] == 'multi_list':
                templa_answer_opt_dict2.append([row_tem_ul['Variable'], dict2_options])
                ###########
    tree_items = html.Div(
        dash_treeview_antd.TreeView(
            id='input',
            multiple=False,
            checkable=True,
            checked=checked,
            expanded=checked,
            data=tree_items_data), id='tree_items_container',
        style={
            'overflow-y': 'auto',  # Vertical scrollbar when needed
            'height': '75vh',  # Fixed height
            'width': '100%',  # Fixed width, or you can specify a value in px
            'white-space': 'normal',  # Allow text to wrap
            'overflow-x': 'hidden',  # Hide overflowed content
            'text-overflow': 'ellipsis',  # Indicate more content with an ellipsis
        }
    )

    # Check all list

    return (
        tree_items,
        current_datadicc.to_json(date_format='iso', orient='split'),
        json.dumps(templa_answer_opt_dict1),
        json.dumps(templa_answer_opt_dict2)
    )


@app.callback(
    [Output('modal', 'is_open', allow_duplicate=True), Output('current_datadicc-store', 'data'),
     Output('ulist_variable_choices-store', 'data'),
     Output('multilist_variable_choices-store', 'data'),
     Output('tree_items_container', 'children', allow_duplicate=True)],
    [Input('modal_submit', 'n_clicks'), Input('modal_cancel', 'n_clicks'), Input('current_datadicc-store', 'data')],
    [State('modal_title', 'children'), State('options-checklist', 'value'), State('input', 'checked'),
     State('ulist_variable_choices-store', 'data'), State('multilist_variable_choices-store', 'data')],

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
        modified_list.append(variable_submited)
        ulist_variables = [i[0] for i in ulist_variable_choices]
        multilist_variables = [i[0] for i in multilist_variable_choices]
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

            print(list_options_checked)
            checked.append(variable_submited)
            tree_items = html.Div(
                dash_treeview_antd.TreeView(
                    id='input',
                    multiple=False,
                    checkable=True,
                    checked=current_datadicc['Variable'].loc[current_datadicc['Variable'].isin(checked)],
                    expanded=current_datadicc['Variable'].loc[current_datadicc['Variable'].isin(checked)],
                    data=tree_items_data), id='tree_items_container',
                style={
                    'overflow-y': 'auto',  # Vertical scrollbar when needed
                    'height': '75vh',  # Fixed height
                    'width': '100%',  # Fixed width, or you can specify a value in px
                    'white-space': 'normal',  # Allow text to wrap
                    'overflow-x': 'hidden',  # Hide overflowed content
                    'text-overflow': 'ellipsis',  # Indicate more content with an ellipsis
                }
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
        print(extracted_text)
        if len(extracted_text) > 0:
            crf_name = extracted_text[0]
    if not crf_name:
        crf_name = 'no_name'
    print('crf_name:', crf_name)
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
        Input("selected_data-store", "data"),
        Input('selected-version-store', 'data'),
        Input('commit-store', 'data')
    ],
    [
        State({'type': 'template_check', 'index': dash.ALL}, "value"),
        State("crf_name", "value"),
        State("output-files-store", "data")  # Adding the output-files-store as a State
    ],
    prevent_initial_call=True
)
def on_generate_click(n_clicks, json_data, selected_version_data, commit_data, checked_values, crf_name, output_files):
    print(output_files)

    ctx = dash.callback_context

    if not n_clicks:
        # Return empty or initial state if button hasn't been clicked
        return '', None, None, None, None

    if not any(json.loads(json_data).values()):
        # Nothing ticked
        return '', None, None, None, None

    trigger_id = get_trigger_id(ctx)

    if trigger_id == 'crf_generate':
        crf_name = get_crf_name(crf_name, checked_values)

        selected_variables_fromData = pd.read_json(io.StringIO(json_data), orient='split')

        date = datetime.today().strftime('%Y-%m-%d')

        datadiccDisease = arc.generateCRF(selected_variables_fromData, crf_name)

        print('#############################')
        print('#############################')
        print('#############################')
        print('#############################')
        print('#############################')
        print('#############################')
        for cosa in datadiccDisease.columns:
            print(cosa)

        currentVersion = selected_version_data.get('selected_version', None)
        commit = commit_data.get('commit', None)
        pdf_crf = paper_crf.generate_pdf(datadiccDisease, currentVersion, crf_name, commit)

        df = datadiccDisease.copy()
        output = io.BytesIO()
        df.to_csv(output, index=False, encoding='utf8')
        output.seek(0)
        pdf_data = paper_crf.generate_completionguide(selected_variables_fromData, currentVersion, crf_name, commit)

        file_name = 'ISARIC Clinical Characterisation Setup.xml'  # Set the desired download name here
        file_path = f'{CONFIG_DIR_FULL}/{file_name}'  # Change this for deploy
        # Open the XML file and read its content
        with open(file_path, 'rb') as file:  # 'rb' mode to read as binary
            content = file.read()

        return "", \
            dcc.send_bytes(output.getvalue(),
                           f"{crf_name}_DataDictionary_{date}.csv") if 'redcap_csv' in output_files else None, \
            dcc.send_bytes(pdf_data,
                           f"{crf_name}_Completion_Guide_{date}.pdf") if 'paper_like' in output_files else None, \
            dcc.send_bytes(content, file_name) if 'redcap_xml' in output_files else None, \
            dcc.send_bytes(pdf_crf, f"{crf_name}_paperlike_{date}.pdf") if 'paper_like' in output_files else None

    else:
        return "", None, None, None, None


@app.callback(
    [
        Output('loading-output-save', 'children'),
        Output('save-crf', 'data')
    ],
    [
        Input('crf_save', 'n_clicks'),
        Input('selected_data-store', 'data'),
        Input('selected-version-store', 'data'),
    ],
    State('crf_name', 'value'),
    prevent_initial_call=True
)
def on_save_click(n_clicks, json_data, selected_version_data, crf_name):
    ctx = dash.callback_context

    if not n_clicks:
        # Return empty or initial state if button hasn't been clicked
        return '', None

    if not any(json.loads(json_data).values()):
        # Nothing ticked
        return '', None

    trigger_id = get_trigger_id(ctx)

    if trigger_id == 'crf_save':
        crf_name = get_crf_name(crf_name, [])

        current_version = selected_version_data.get('selected_version', None)
        date = datetime.today().strftime('%Y-%m-%d')
        filename_csv = f'{crf_name}_{current_version}_{date}.csv'

        df_selected_variables = pd.read_json(io.StringIO(json_data), orient='split')

        df = df_selected_variables.copy()
        output = io.BytesIO()
        df.to_csv(output, index=False, encoding='utf8')
        output.seek(0)

        return '', dcc.send_bytes(output.getvalue(), filename_csv)
    else:
        return '', None


@app.callback(
    Output('output-crf-upload', 'children'),
    [
        Input('upload-crf', 'contents')
    ],
    State('upload-crf', 'filename'),
    prevent_initial_call=True
)
def on_upload_crf(list_of_contents, list_of_names):
    # TODO: Add functionality
    ctx = dash.callback_context

    if list_of_names is None:
        return ''

    print(list_of_contents)
    print(list_of_names)

    trigger_id = get_trigger_id(ctx)
    print(trigger_id)


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
            current_datadicc.loc[current_datadicc['Variable'].isin(list(caseDefiningVariables.iloc[0]))], 'case_feat',
            current_datadicc, selected_variables_fromData)
        tabs_content.append(dbc.Tab(label="Features", children=[html.P(" "), paralel_elements_features]))
        selected_question = "What are the [case defining features]?"

    elif selected_value == "Spectrum_Clinical_Features":
        OptionGroup = ["Clinical Features"]
        clinicalVariables = group_elements['Variables'].loc[group_elements['Group Option'].isin(OptionGroup)]
        paralel_elements_features = paralel_elements(
            current_datadicc.loc[current_datadicc['Variable'].isin(list(clinicalVariables.iloc[0]))], 'clinic_feat',
            current_datadicc, selected_variables_fromData)
        tabs_content.append(dbc.Tab(label="Clinical Features", children=[html.P(" "), paralel_elements_features]))
        selected_question = "What is the spectrum of [clinical features] in this disease?"

    elif selected_value == "Clinical_Features_Patient_Outcome":
        OptionGroup = ["Clinical Features"]
        clinicalVariables = group_elements['Variables'].loc[group_elements['Group Option'].isin(OptionGroup)]
        paralel_elements_features = paralel_elements(
            current_datadicc.loc[current_datadicc['Variable'].isin(list(clinicalVariables.iloc[0]))], 'clinic_feat',
            current_datadicc, selected_variables_fromData)
        OptionGroup = ["Patient Outcome"]
        outcomeVariables = group_elements['Variables'].loc[group_elements['Group Option'].isin(OptionGroup)]
        paralel_elements_outcomes = paralel_elements(
            current_datadicc.loc[current_datadicc['Variable'].isin(list(outcomeVariables.iloc[0]))], 'outcome',
            current_datadicc, selected_variables_fromData)
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
        paralel_elements_risk = paralel_elements(current_datadicc.loc[current_datadicc['Variable'].isin(allRiskVarr)],
                                                 'risk', current_datadicc, selected_variables_fromData)
        OptionGroup = ["Patient Outcome"]
        outcomeVariables = group_elements['Variables'].loc[group_elements['Group Option'].isin(OptionGroup)]
        paralel_elements_outcomes = paralel_elements(
            current_datadicc.loc[current_datadicc['Variable'].isin(list(outcomeVariables.iloc[0]))], 'outcome',
            current_datadicc, selected_variables_fromData)
        tabs_content.append(dbc.Tab(label="Risk Factors", children=[html.P(" "), paralel_elements_risk]))
        tabs_content.append(dbc.Tab(label="Patient Outcomes", children=[html.P(" "), paralel_elements_outcomes]))
        selected_question = "What are the [risk factors] for [patient outcome]?"

    elif selected_value == "Treatment_Intervention_Patient_Outcome":

        OptionGroup = ["Treatment/Intevention"]
        TreatmentsVariables = group_elements['Variables'].loc[group_elements['Group Option'].isin(OptionGroup)]
        paralel_elements_treatments = paralel_elements(
            current_datadicc.loc[current_datadicc['Variable'].isin(list(TreatmentsVariables.iloc[0]))], 'treatment',
            current_datadicc, selected_variables_fromData)
        OptionGroup = ["Patient Outcome"]
        outcomeVariables = group_elements['Variables'].loc[group_elements['Group Option'].isin(OptionGroup)]
        paralel_elements_outcomes = paralel_elements(
            current_datadicc.loc[current_datadicc['Variable'].isin(list(outcomeVariables.iloc[0]))], 'outcome',
            current_datadicc, selected_variables_fromData)
        tabs_content.append(
            dbc.Tab(label="Treatments/Interventions", children=[html.P(" "), paralel_elements_treatments]))
        tabs_content.append(dbc.Tab(label="Patient Outcomes", children=[html.P(" "), paralel_elements_outcomes]))

        selected_question = "What [treatment/intervention] are received by those with  [patient outcome]?"
    elif selected_value == "Clinical_Features_Treatment_Intervention":

        selected_question = "What proportion of patients with [clinical feature] are receiving [treatment/intervention]?"

        OptionGroup = ["Clinical Features"]
        clinicalVariables = group_elements['Variables'].loc[group_elements['Group Option'].isin(OptionGroup)]
        paralel_elements_features = paralel_elements(
            current_datadicc.loc[current_datadicc['Variable'].isin(list(clinicalVariables.iloc[0]))], 'clinic_feat',
            current_datadicc, selected_variables_fromData)
        tabs_content.append(dbc.Tab(label="Clinical Features", children=[html.P(" "), paralel_elements_features]))
        OptionGroup = ["Treatment/Intevention"]
        TreatmentsVariables = group_elements['Variables'].loc[group_elements['Group Option'].isin(OptionGroup)]
        paralel_elements_treatments = paralel_elements(
            current_datadicc.loc[current_datadicc['Variable'].isin(list(TreatmentsVariables.iloc[0]))], 'treatment',
            current_datadicc, selected_variables_fromData)
        tabs_content.append(
            dbc.Tab(label="Treatments/Interventions", children=[html.P(" "), paralel_elements_treatments]))

    elif selected_value == "Patient_Outcome_Treatment_Intervention":
        OptionGroup = ["Treatment/Intevention"]
        TreatmentsVariables = group_elements['Variables'].loc[group_elements['Group Option'].isin(OptionGroup)]
        paralel_elements_treatments = paralel_elements(
            current_datadicc.loc[current_datadicc['Variable'].isin(list(TreatmentsVariables.iloc[0]))], 'treatment',
            current_datadicc, selected_variables_fromData)
        tabs_content.append(
            dbc.Tab(label="Treatments/Interventions", children=[html.P(" "), paralel_elements_treatments]))

        OptionGroup = ["Patient Outcome"]
        outcomeVariables = group_elements['Variables'].loc[group_elements['Group Option'].isin(OptionGroup)]
        paralel_elements_outcomes = paralel_elements(
            current_datadicc.loc[current_datadicc['Variable'].isin(list(outcomeVariables.iloc[0]))], 'outcome',
            current_datadicc, selected_variables_fromData)
        tabs_content.append(dbc.Tab(label="Patient Outcomes", children=[html.P(" "), paralel_elements_outcomes]))

        selected_question = "What proportion of [patient outcome] recieved [treatment/intervention]?"
    elif selected_value == "Duration_Treatment_Intervention_Patient_Outcome":
        OptionGroup = ["Treatment/Intevention"]
        TreatmentsVariables = group_elements['Variables'].loc[group_elements['Group Option'].isin(OptionGroup)]
        paralel_elements_treatments = paralel_elements(
            current_datadicc.loc[current_datadicc['Variable'].isin(list(TreatmentsVariables.iloc[0]))], 'treatment',
            current_datadicc, selected_variables_fromData)
        tabs_content.append(
            dbc.Tab(label="Treatments/Interventions", children=[html.P(" "), paralel_elements_treatments]))

        OptionGroup = ["Patient Outcome"]
        outcomeVariables = group_elements['Variables'].loc[group_elements['Group Option'].isin(OptionGroup)]
        paralel_elements_outcomes = paralel_elements(
            current_datadicc.loc[current_datadicc['Variable'].isin(list(outcomeVariables.iloc[0]))], 'outcome',
            current_datadicc, selected_variables_fromData)
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
    selected_features = current_datadicc.loc[current_datadicc['Variable'].isin(all_checked)]
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
    selected_features = current_datadicc.loc[current_datadicc['Variable'].isin(all_checked)]
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
    selected_features = current_datadicc.loc[current_datadicc['Variable'].isin(all_checked)]
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
    selected_features = current_datadicc.loc[current_datadicc['Variable'].isin(all_checked)]
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
    selected_features = current_datadicc.loc[current_datadicc['Variable'].isin(all_checked)]
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
