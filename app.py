import io
import json

import dash
import dash_bootstrap_components as dbc
import dash_treeview_antd
import pandas as pd
from dash import callback_context, html, Input, Output, State
from dash.exceptions import PreventUpdate

import bridge.generate_pdf.form as form
from bridge.arc import arc
from bridge.arc.arc_api import ArcApiClient
from bridge.create_outputs.arc_data import ARCData
from bridge.create_outputs.generate import Generate
from bridge.create_outputs.save import Save
from bridge.create_outputs.upload import Upload
from bridge.layout import index
from bridge.layout.app_layout import define_app_layout, main_app, SideBar
from bridge.layout.dropdowns import Dropdowns
from bridge.layout.radios import Radios
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
app = Dropdowns.register_callbacks(app)
app = Generate().register_callbacks(app)
app = Radios.register_callbacks(app)
app = Save.register_callbacks(app)
app = SideBar.register_callbacks(app)
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
        selected_variables = arc.get_include_not_show(selected_variables['Variable'], current_datadicc)

        # Select Units Transformation
        arc_var_units_selected, delete_this_variables_with_units = arc.get_select_units(selected_variables['Variable'],
                                                                                        current_datadicc)
        if arc_var_units_selected is not None:
            selected_variables = arc.add_transformed_rows(selected_variables, arc_var_units_selected,
                                                          arc.get_variable_order(current_datadicc))
            if len(delete_this_variables_with_units) > 0:  # This remove all the unit variables that were included in a select unit type question
                selected_variables = selected_variables.loc[
                    ~selected_variables['Variable'].isin(delete_this_variables_with_units)]

        selected_variables = arc.generate_daily_data_type(selected_variables)

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


# TODO: This displays the modal popup
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
    dict_ulist = json.loads(ulist_variable_choices_saved)
    dict_multilist = json.loads(multilist_variable_choices_saved)
    dict_lists = dict_ulist + dict_multilist
    df_datadicc = pd.read_json(io.StringIO(current_datadicc_saved), orient='split')

    if selected:
        selected_variable = selected[0]
        if selected_variable in list(df_datadicc['Variable']):
            question = df_datadicc['Question'].loc[df_datadicc['Variable'] == selected_variable].iloc[0]
            definition = df_datadicc['Definition'].loc[df_datadicc['Variable'] == selected_variable].iloc[0]
            completion = \
                df_datadicc['Completion Guideline'].loc[df_datadicc['Variable'] == selected_variable].iloc[0]
            ulist_variables = [i[0] for i in dict_lists]
            if selected_variable in ulist_variables:
                for item in dict_lists:
                    if item[0] == selected_variable:
                        options = []
                        checked_items = []
                        for i in item[1]:
                            options.append({"number": int(i[0]), "label": str(i[0]) + ', ' + i[1],
                                            "value": str(i[0]) + '_' + i[1]})
                            if i[2] == 1:
                                checked_items.append(str(i[0]) + '_' + i[1])

                sorted_options = sorted(options, key=lambda x: x['number'])
                for option in sorted_options:
                    del option['number']

                return True, question + ' [' + selected_variable + ']', definition, completion, {"maxHeight": "250px",
                                                                                                 "overflowY": "auto"}, {
                    "display": "none"}, sorted_options, checked_items, []
            else:
                options = []
                answ_options = \
                    df_datadicc['Answer Options'].loc[df_datadicc['Variable'] == selected_variable].iloc[0]
                if isinstance(answ_options, str):
                    for i in answ_options.split('|'):
                        options.append(dbc.ListGroupItem(i))
                else:
                    options = []
                return True, question + ' [' + selected_variable + ']', definition, completion, {"display": "none"}, {
                    "maxHeight": "250px", "overflowY": "auto"}, [], [], options

    return False, '', '', '', {"display": "none"}, {"display": "none"}, [], [], []


# TODO: This says what has been expanded on the LHS
@app.callback(
    Output('output-expanded', 'children'),
    [
        Input('input', 'expanded'),
    ])
def display_expanded(expanded):
    return 'You have expanded {}'.format(expanded)


@app.callback(
    [
        Output('selected-version-store', 'data', allow_duplicate=True),
        Output('selected-language-store', 'data', allow_duplicate=True),
        Output('commit-store', 'data', allow_duplicate=True),
        Output('preset-accordion', 'children', allow_duplicate=True),
        Output('grouped_presets-store', 'data'),
        Output('current_datadicc-store', 'data', allow_duplicate=True),
        Output('templates_checks_ready', 'data'),
        Output('ulist_variable_choices-store', 'data', allow_duplicate=True),
        Output('multilist_variable_choices-store', 'data', allow_duplicate=True),
    ],
    [
        Input({'type': 'dynamic-version', 'index': dash.ALL}, 'n_clicks'),
        Input({'type': 'dynamic-language', 'index': dash.ALL}, 'n_clicks'),
    ],
    [
        State('selected-version-store', 'data'),
        State('selected-language-store', 'data'),
        State('language-list-store', 'data'),
        State('upload-crf-ready', 'data'),
    ],
    prevent_initial_call=True  # Evita que se dispare al inicio
)
def store_clicked_item(n_clicks_version, n_clicks_language, selected_version_data, selected_language_data,
                       language_list_data, upload_crf_ready):
    ctx = dash.callback_context

    # Si no hay cambios (es decir, no hay un input activado), no se hace nada
    if not ctx.triggered:
        return (dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, False,
                dash.no_update, dash.no_update)

    button_id = ctx.triggered[0]['prop_id'].split(".")[0]
    button_index = json.loads(button_id)["index"]
    button_type = json.loads(button_id)["type"]

    selected_version = None
    selected_language = None

    if button_type == 'dynamic-version':
        arc_version_list, _arc_version_latest = arc.get_arc_versions()
        selected_version = arc_version_list[button_index]
        if selected_version_data and selected_version == selected_version_data.get('selected_version', None):
            return (dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update,
                    False, dash.no_update, dash.no_update)
        # Reset to English to ensure the data is present
        selected_language = 'English'

    elif button_type == 'dynamic-language':
        if not upload_crf_ready:
            selected_language = language_list_data[button_index]
        else:
            # We don't have the button_index if loading from file
            selected_language = selected_language_data.get('selected_language', None)
        selected_version = selected_version_data.get('selected_version')

    try:
        (
            df_version,
            version_commit,
            version_presets,
            version_accordion_items,
            version_ulist_variable_choices,
            version_multilist_variable_choices
        ) = ARCData(selected_version, selected_language).get_version_language_related_data()
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
            True,
            version_ulist_variable_choices,
            version_multilist_variable_choices
        )
    except json.JSONDecodeError:
        return (dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, False,
                dash.no_update, dash.no_update)


def update_for_template_options(version, language, df_current_datadicc, ulist_variable_choices,
                                multilist_variable_choices, checked_key=None):
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
            ulist_variable_choices.append([row_tem_ul['Variable'], dict1_options])
        elif row_tem_ul['Type'] == 'multi_list':
            multilist_variable_choices.append([row_tem_ul['Variable'], dict2_options])
    return df_current_datadicc, ulist_variable_choices, multilist_variable_choices


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

    df_version, version_presets, version_commit = arc.get_arc(current_version)
    df_version = arc.add_required_datadicc_columns(df_version)
    df_version_language = ARCData(current_version, current_language).get_dataframe_arc_language(df_version)

    tree_items_data = arc.get_tree_items(df_version_language, current_version)

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
    ulist_variable_choices = []
    multilist_variable_choices = []

    if len(checked_template_list) > 0:
        for ps in checked_template_list:
            checked_key = 'preset_' + ps[0] + '_' + ps[1]
            if checked_key in df_current_datadicc:
                checked = checked + list(
                    df_current_datadicc['Variable'].loc[df_current_datadicc[checked_key].notnull()])

            df_current_datadicc, ulist_variable_choices, multilist_variable_choices = update_for_template_options(
                current_version, current_language, df_current_datadicc, ulist_variable_choices,
                multilist_variable_choices,
                checked_key=checked_key)

    else:
        df_current_datadicc, ulist_variable_choices, multilist_variable_choices = update_for_template_options(
            current_version, current_language, df_current_datadicc, ulist_variable_choices, multilist_variable_choices)

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
        json.dumps(ulist_variable_choices),
        json.dumps(multilist_variable_choices)
    )


# TODO: Modal submit
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
        State('multilist_variable_choices-store', 'data'),
        State('selected-version-store', "data"),
        State('selected-language-store', "data"),
    ],
    prevent_initial_call=True
)
def on_modal_button_click(submit_n_clicks, cancel_n_clicks, current_datadicc_saved, modal_title, checked_options,
                          checked, ulist_variable_choices_saved, multilist_variable_choices_saved,
                          selected_version_data, selected_language_data):
    ctx = callback_context

    if not ctx.triggered:
        return dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update

    df_current_datadicc = pd.read_json(io.StringIO(current_datadicc_saved), orient='split')
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]

    if button_id == 'modal_submit':

        selected_version = selected_version_data.get('selected_version', None)
        selected_language = selected_language_data.get('selected_language', None)
        translations_for_language = arc.get_translations(selected_language)
        other_text = translations_for_language['other']

        variable_submitted = modal_title.split('[')[1][:-1]

        ulist_variable_choices_dict = json.loads(ulist_variable_choices_saved)
        multilist_variable_choices_dict = json.loads(multilist_variable_choices_saved)

        ulist_variables = [i[0] for i in json.loads(ulist_variable_choices_saved)]
        multilist_variables = [i[0] for i in json.loads(multilist_variable_choices_saved)]

        if (variable_submitted in ulist_variables) | (variable_submitted in multilist_variables):
            list_options_checked = []
            for lo in checked_options:
                list_options_checked.append(lo.split('_'))

            list_options_checked = pd.DataFrame(data=list_options_checked, columns=['cod', 'Option'])

            new_submited_options = []
            new_submited_line = []
            position = 0
            for var_select in ulist_variable_choices_dict:
                if (var_select[0] == variable_submitted):
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
                    ulist_variable_choices_dict[position][1] = new_submited_line[0][1]
                    df_current_datadicc.loc[df_current_datadicc[
                                                'Variable'] == variable_submitted, 'Answer Options'] = select_answer_options + '88, ' + other_text
                    if variable_submitted + '_otherl2' in list(df_current_datadicc['Variable']):
                        df_current_datadicc.loc[df_current_datadicc[
                                                    'Variable'] == variable_submitted + '_otherl2', 'Answer Options'] = NOT_select_answer_options + '88, ' + other_text

                position += 1
            ulist_variable_choicesSubmit = ulist_variable_choices_dict

            new_submited_options_multi_check = []
            new_submited_line_multi_check = []
            position_multi_check = 0
            for var_select_multi_check in multilist_variable_choices_dict:
                if (var_select_multi_check[0] == variable_submitted):
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
                    multilist_variable_choices_dict[position_multi_check][1] = new_submited_line_multi_check[0][1]
                    df_current_datadicc.loc[df_current_datadicc[
                                                'Variable'] == variable_submitted, 'Answer Options'] = select_answer_options_multi_check + '88, ' + other_text
                    if variable_submitted + '_otherl2' in list(df_current_datadicc['Variable']):
                        df_current_datadicc.loc[df_current_datadicc[
                                                    'Variable'] == variable_submitted + '_otherl2', 'Answer Options'] = NOT_select_answer_options_multi_check + '88, ' + other_text
                position_multi_check += 1
            multilist_variable_choicesSubmit = multilist_variable_choices_dict

            checked.append(variable_submitted)

            tree_items_data = arc.get_tree_items(df_current_datadicc, selected_version)

            tree_items = html.Div(
                dash_treeview_antd.TreeView(
                    id='input',
                    multiple=False,
                    checkable=True,
                    checked=df_current_datadicc['Variable'].loc[df_current_datadicc['Variable'].isin(checked)],
                    expanded=df_current_datadicc['Variable'].loc[df_current_datadicc['Variable'].isin(checked)],
                    data=tree_items_data),
                id='tree_items_container',
                className='tree-item',
            )
            return False, df_current_datadicc.to_json(date_format='iso', orient='split'), json.dumps(
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


if __name__ == "__main__":
    app.run_server(debug=True, use_reloader=False)
    # app.run_server(debug=True, host='0.0.0.0', port='8080')#change for deploy
