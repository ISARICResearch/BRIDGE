import re

import numpy as np
import pandas as pd

from bridge.arc.arc_api import ArcApiClient
from bridge.logging.logger import setup_logger

logger = setup_logger(__name__)

pd.options.mode.copy_on_write = True


def add_required_datadicc_columns(df_datadicc: pd.DataFrame) -> pd.DataFrame:
    df_datadicc[['Sec', 'vari', 'mod']] = df_datadicc['Variable'].str.split('_', n=2, expand=True)
    df_datadicc[['Sec_name', 'Expla']] = df_datadicc['Section'].str.split(r'[(|:]', n=1, expand=True)
    return df_datadicc


def get_arc_translation(language: str,
                        version: str,
                        current_datadicc: pd.DataFrame) -> pd.DataFrame:
    try:
        datadicc_english = ArcApiClient().get_dataframe_arc_version_language(version, 'English')

        df_merged_english = current_datadicc[['Variable']].merge(
            datadicc_english.set_index('Variable'), on='Variable', how='left')

        current_datadicc['Question_english'] = current_datadicc['Variable'].map(
            df_merged_english.set_index('Variable')['Question'])

        current_datadicc['Question_english'] = current_datadicc['Question_english'].astype(str)

        datadicc_translated = ArcApiClient().get_dataframe_arc_version_language(version, language)

        df_merged = current_datadicc[['Variable']].merge(
            datadicc_translated.set_index('Variable'), on='Variable', how='left'
        )
        columns_to_update = ['Form', 'Section', 'Question', 'Answer Options', 'Definition', 'Completion Guideline']

        for col in columns_to_update:
            current_datadicc.loc[df_merged[col].notna(), col] = df_merged.loc[df_merged[col].notna(), col]

        def normalize_logic_syntax(skip_logic_column):
            # Reemplazar patrones del tipo [variable(numero)]='valor' por [variable]='numero'
            normalized = re.sub(r"\[([a-zA-Z0-9_]+)\((\d+)\)\]='(\d+)'", r"[\1]='\2'", skip_logic_column)
            return normalized

        def extract_logic_components(skip_logic_column):
            # Asegurarse de que la entrada es una cadena válida
            if isinstance(skip_logic_column, str) and pd.notna(skip_logic_column):
                # Normalizar la sintaxis antes de realizar la extracción
                normalized_logic = normalize_logic_syntax(skip_logic_column)

                # Extraer variables dentro de corchetes
                variables = re.findall(r"\[([a-zA-Z0-9_]+)\]", normalized_logic)

                # Extraer valores que están siendo comparados (números o cadenas entre comillas)
                raw_values = re.findall(r"[=!<>]=?\s*('[^']*'|\d+\.?\d*)", normalized_logic)
                values = []
                for val in raw_values:
                    if val.startswith("'") and val.endswith("'"):
                        # Si es una cadena (encerrada en comillas), eliminar las comillas
                        values.append(val.strip("'"))
                    else:
                        # Convertir a int o float según corresponda
                        if '.' in val:
                            values.append(float(val))  # Convertir a float si contiene un punto decimal
                        else:
                            values.append(int(val))  # Convertir a int en caso contrario

                # Extraer operadores de comparación (e.g., =, ==, <, >, <=, >=, <>)
                comparison_operators = re.findall(r"(<=|>=|<>|[=><!]=?)", normalized_logic)

                # Extraer operadores lógicos (e.g., and, or)
                logical_operators = re.findall(r"\b(and|or)\b", normalized_logic)

                return variables, values, comparison_operators, logical_operators

            # Devolver listas vacías si la entrada no es válida
            return [], [], [], []

        def process_skip_logic(row, current_datadicc):
            skip_logic = row['Skip Logic']
            extracted_variables, labels, comparison_operators, logical_operators = extract_logic_components(skip_logic)
            branch = []
            logical_operators = logical_operators + [' ']
            for i in range(len(extracted_variables)):
                # Extraer las opciones de respuesta y mapear valores
                try:
                    answers = \
                        current_datadicc['Answer Options'].loc[
                            current_datadicc['Variable'] == extracted_variables[i]].iloc[
                            0]
                    # Verificar si `answers` es una cadena válida
                    question = \
                        current_datadicc['Question'].loc[current_datadicc['Variable'] == extracted_variables[i]].iloc[0]
                    comp_operators = comparison_operators[i]
                    if isinstance(answers, str) and pd.notna(answers):
                        pairs = answers.split(" | ")
                        dic_answer = {pair.split(", ")[0]: pair.split(", ")[1] for pair in pairs}
                        answers_label = dic_answer.get(labels[i], "Unknown")

                    else:
                        answers_label = labels[i]
                    branch.append(f"({question} {comp_operators} {answers_label}) {logical_operators[i]}")

                except IndexError:
                    branch.append("Variable not found getARCTranslation")
                except Exception as e:
                    branch.append(f"Error getARCTranslation: {str(e)}")

            return "  ".join(branch)

        current_datadicc['Branch'] = current_datadicc.apply(lambda row: process_skip_logic(row, current_datadicc),
                                                            axis=1)
    except Exception as e:
        logger.error(e)
        raise RuntimeError("Failed to fetch remote file")

    return current_datadicc


def get_arc_versions() -> tuple[list, str]:
    version_list = ArcApiClient().get_arc_version_list()
    logger.info(f'version_list: {version_list}')
    return version_list, max(version_list)


def get_variable_order(df_current_datadicc: pd.DataFrame) -> list:
    df_current_datadicc['Sec_vari'] = df_current_datadicc['Sec'] + '_' + df_current_datadicc['vari']
    order = df_current_datadicc[['Sec_vari']]
    order = order.drop_duplicates().reset_index()
    return list(order['Sec_vari'])


def get_arc(version: str) -> tuple[pd.DataFrame, list, str]:
    logger.info(f'version: {version}')

    commit_sha = ArcApiClient().get_arc_version_sha(version)
    df_datadicc = ArcApiClient().get_dataframe_arc_sha(commit_sha)

    try:
        df_dependencies = get_dependencies(df_datadicc)
        df_datadicc = pd.merge(df_datadicc, df_dependencies[['Variable', 'Dependencies']], on='Variable')

        # Find preset columns
        preset_column_list = [col for col in df_datadicc.columns if "preset_" in col]
        preset_list = []
        # Iterate through each string in the list
        for preset_column in preset_column_list:
            parts = preset_column.split('_')[1:]
            if len(parts) > 2:
                parts[1] = ' '.join(parts[1:])
                del parts[2:]
            preset_list.append(parts)

        df_datadicc['Question_english'] = df_datadicc['Question']
        return df_datadicc, preset_list, commit_sha
    except Exception as e:
        logger.error(e)
        raise RuntimeError("Failed to format ARC data")


def get_dependencies(df_datadicc: pd.DataFrame) -> pd.DataFrame:
    mandatory = ['subjid']

    df_dependencies = df_datadicc[['Variable', 'Skip Logic']]
    field_dependencies = []
    for skip_logic_str in df_dependencies['Skip Logic']:
        cont = 0
        variable_dependencies = []
        if type(skip_logic_str) != float:
            for i in skip_logic_str.split('['):
                variable = (i[:i.find(']')])
                if '(' in variable:
                    variable = (variable[:variable.find('(')])
                if cont != 0:
                    variable_dependencies.append(variable)
                cont += 1
        field_dependencies.append(variable_dependencies)

    df_dependencies['Dependencies'] = field_dependencies
    for variable in df_dependencies['Variable']:
        if 'other' in variable:
            if len(df_dependencies['Dependencies'].loc[
                       df_dependencies['Variable'] == variable.replace('other', '')]) >= 1:
                df_dependencies['Dependencies'].loc[df_dependencies['Variable'] == variable.replace('other', '')].iloc[
                    0].append(variable)

        if 'units' in variable:
            if len(df_dependencies['Dependencies'].loc[
                       df_dependencies['Variable'] == variable.replace('units', '')]) >= 1:
                df_dependencies['Dependencies'].loc[df_dependencies['Variable'] == variable.replace('units', '')].iloc[
                    0].append(variable)

        for mandatory_variable in mandatory:
            df_dependencies['Dependencies'].loc[df_dependencies['Variable'] == variable].iloc[0].append(
                mandatory_variable)

    return df_dependencies


def set_select_units(df_datadicc: pd.DataFrame) -> pd.DataFrame:
    mask_true = df_datadicc['select units'] == True
    for index, row in df_datadicc[mask_true].iterrows():
        mask_sec_vari = (df_datadicc['Sec'] == row['Sec']) & (df_datadicc['vari'] == row['vari'])
        df_datadicc.loc[mask_sec_vari, 'select units'] = True
    return df_datadicc


def get_tree_items(datadicc: pd.DataFrame, version: str) -> dict:
    version = version.replace('ICC', 'ARC')
    include_not_show = ['otherl3', 'otherl2', 'route', 'route2', 'agent', 'agent2', 'warn', 'warn2', 'warn3', 'units',
                        'add', 'vol', 'txt', 'calc']

    if 'Dependencies' not in datadicc.columns:
        dependencies = get_dependencies(datadicc)
        datadicc = pd.merge(datadicc, dependencies[['Variable', 'Dependencies']], on='Variable')

    datadicc = add_required_datadicc_columns(datadicc)

    datadicc['select units'] = (datadicc['Question'].str.contains('(select units)', case=False, na=False, regex=False))
    datadicc = set_select_units(datadicc)

    for_item = datadicc[['Form', 'Sec_name', 'vari', 'mod', 'Question', 'Variable', 'Type']].loc[
        ~datadicc['mod'].isin(include_not_show)]
    for_item = for_item[for_item['Sec_name'].notna()]

    tree = {'title': version, 'key': 'ARC', 'children': []}
    seen_forms = set()
    seen_sections = {}
    primary_question_keys = {}  # To keep track of primary question nodes

    for index, row in for_item.iterrows():
        form = row['Form'].upper()
        sec_name = row['Sec_name'].upper()
        vari = row['vari']
        mod = row['mod']
        if row['Type'] == 'user_list':
            question = '↳ ' + row['Question']
        elif row['Type'] == 'multi_list':
            question = '⇉ ' + row['Question']
        else:
            question = row['Question']
        variable_name = row['Variable']
        question_key = f"{variable_name}"

        # Add form node if not already added
        if form not in seen_forms:
            form_node = {'title': form, 'key': form, 'children': []}
            tree['children'].append(form_node)
            seen_forms.add(form)
            seen_sections[form] = set()

        # Add section node if not already added for this form
        if sec_name not in seen_sections[form]:
            sec_node = {'title': sec_name, 'key': f"{form}-{sec_name}", 'children': []}
            for child in tree['children']:
                if child['title'] == form:
                    child['children'].append(sec_node)
                    break
            seen_sections[form].add(sec_name)

        # Check if the question is a primary node or a child node
        if mod is None or pd.isna(mod):
            # Primary node
            primary_question_node = {'title': question, 'key': question_key, 'children': []}
            primary_question_keys[(form, vari)] = question_key
            for form_child in tree['children']:
                if form_child['title'] == form:
                    for sec_child in form_child['children']:
                        if sec_child['title'] == sec_name:
                            sec_child['children'].append(primary_question_node)
                            break
        else:
            # Child node of a primary node
            primary_key = primary_question_keys.get((form, vari))
            if primary_key:
                question_node = {'title': question, 'key': question_key}
                # Find the correct primary question node to add this question
                for form_child in tree['children']:
                    if form_child['title'] == form:
                        for sec_child in form_child['children']:
                            if sec_child['title'] == sec_name:
                                for primary_question in sec_child['children']:
                                    if primary_question['key'] == primary_key:
                                        primary_question['children'].append(question_node)
                                        break

    return tree


def extract_parenthesis_content(text: str) -> str:
    match = re.search(r'\(([^)]+)\)', text)
    return match.group(1) if match else text


def get_include_not_show(selected_variables: pd.Series,
                         df_current_datadicc: pd.DataFrame) -> pd.DataFrame:
    include_not_show = ['otherl2', 'otherl3', 'route', 'route2', 'site', 'agent', 'agent2', 'warn', 'warn2', 'warn3',
                        'units', 'add', 'type', 'vol', 'site', '0item', '0otherl2',
                        '0addi', '1item', '1otherl2', '1addi', '2item', '2otherl2', '2addi', '3item', '3otherl2',
                        '3addi',
                        '4item', '4otherl2', '4addi', 'txt']

    # Get the include not show for the selected variables
    possible_vars_to_include = [f"{var}_{suffix}" for var in selected_variables for suffix in include_not_show]
    actual_vars_to_include = [var for var in possible_vars_to_include if var in df_current_datadicc['Variable'].values]
    selected_variables = list(selected_variables) + list(actual_vars_to_include)
    # Deduplicate the final list in case of any overlaps
    selected_variables = list(set(selected_variables))
    df_include_not_show = df_current_datadicc.loc[df_current_datadicc['Variable'].isin(selected_variables)].reset_index(
        drop=True)
    return df_include_not_show


def get_select_units(selected_variables: pd.Series,
                     df_current_datadicc: pd.DataFrame) -> tuple[pd.DataFrame, list] | \
                                                           tuple[None, None]:
    df_current_datadicc['select units'] = (
        df_current_datadicc['Question_english'].str.contains('(select units)', case=False, na=False, regex=False))

    df_current_datadicc_units = df_current_datadicc.loc[
        df_current_datadicc['Question_english'].str.contains('(select units)', regex=False)]
    units_lang = df_current_datadicc_units.sample(n=1)['Question'].iloc[0]
    units_lang = extract_parenthesis_content(units_lang)
    df_current_datadicc = set_select_units(df_current_datadicc)

    df_selected_select_unit = df_current_datadicc.loc[df_current_datadicc['select units'] &
                                                      df_current_datadicc['Variable'].isin(selected_variables) &
                                                      df_current_datadicc['mod'].notna()]

    df_selected_select_unit['count'] = df_selected_select_unit.groupby(['Sec', 'vari']).transform('size')

    select_unit_rows = []
    seen_variables = set()

    delete_this_variables_with_units = []

    for _, row in df_selected_select_unit.iterrows():
        if row['count'] > 1:
            matching_rows = df_selected_select_unit[(df_selected_select_unit['Sec'] == row['Sec']) &
                                                    (df_selected_select_unit['vari'] == row['vari'])]

            for delete_variable in matching_rows['Variable']:
                delete_this_variables_with_units.append(delete_variable)

            max_value = pd.to_numeric(matching_rows['Maximum'], errors='coerce').max()
            min_value = pd.to_numeric(matching_rows['Minimum'], errors='coerce').min()
            options = ' | '.join([f"{idx + 1},{extract_parenthesis_content(r['Question'])}" for idx, (_, r) in
                                  enumerate(matching_rows.iterrows())])

            row_value = row.copy()
            row_value['Variable'] = row['Sec'] + '_' + row['vari']
            row_value['Answer Options'] = None
            row_value['Type'] = 'text'
            row_value['Maximum'] = max_value
            row_value['Minimum'] = min_value
            row_value['Question'] = row['Question'].split('(')[0]
            row_value['Validation'] = None
            row_value['Validation'] = 'number'

            row_units = row.copy()
            row_units['Variable'] = row['Sec'] + '_' + row['vari'] + '_units'
            row_units['Answer Options'] = options
            row_units['Type'] = 'radio'
            row_units['Maximum'] = None
            row_units['Minimum'] = None
            row_units['Question'] = row['Question'].split('(')[0] + '(' + units_lang + ')'
            row_units['Validation'] = None

            if row_value['Variable'] not in seen_variables:
                select_unit_rows.append(row_value)
                seen_variables.add(row_value['Variable'])

            if row_units['Variable'] not in seen_variables:
                select_unit_rows.append(row_units)
                seen_variables.add(row_units['Variable'])

    if len(select_unit_rows) > 0:
        df_icc_var_units_selected_rows = pd.DataFrame(select_unit_rows).reset_index(drop=True)
        return df_icc_var_units_selected_rows, sorted(list(
            set(delete_this_variables_with_units) - set(df_icc_var_units_selected_rows['Variable'])))
    return None, None


def get_translations(language: str) -> dict:
    translations = {
        'English': {
            'select': 'Select',
            'specify': 'Specify',
            'specify_other': 'Specify other',
            'specify_other_infection': 'Specify other infection the individual is suspected/confirmed to have',
            'other_agent': 'other agents administered while hospitalised or at discharge',
            'select_additional': 'Select additional',
            'any_additional': 'Any additional',
            'other': 'Other',
            'units': 'Units'
        },
        'Spanish': {
            'select': 'Seleccionar',
            'specify': 'Especifique',
            'specify_other': 'Especifique otro(a)',
            'specify_other_infection': 'Especifique otra infección que se sospecha/ha confirmado en el individuo',
            'other_agent': 'otros medicamentos administrados durante la hospitalización o al alta',
            'select_additional': 'Seleccionar adicional',
            'any_additional': 'Cualquier adicional',
            'other': 'Otro(a)',
            'units': 'Unidades'
        },
        'French': {
            'select': 'Sélectionnez',
            'specify': 'Précisez',
            'specify_other': 'Précisez un(e) autre',
            'specify_other_infection': 'Précisez une autre infection dont l’individu est suspecté/confirmé avoir',
            'other_agent': 'autre(s) agent(s) administré(s) lors de l’hospitalisation ou à la sortie',
            'select_additional': 'Sélectionner supplémentaire',
            'any_additional': 'Tout supplémentaire',
            'other': 'Autre',
            'units': 'Unités'
        },
        'Portuguese': {
            'select': 'Selecionar',
            'specify': 'Especifique',
            'specify_other': 'Especifique outro(a)',
            'specify_other_infection': 'Especifique outra infecção que o indivíduo é suspeito/confirmado ter',
            'other_agent': 'outros agentes administrados durante a hospitalização ou na alta',
            'select_additional': 'Selecionar adicional',
            'any_additional': 'Qualquer adicional',
            'other': 'Outro(a)',
            'units': 'Unidades'
        }
    }

    if language not in translations:
        raise ValueError(f"Language '{language}' is not supported.")

    return translations[language]


def get_list_content(df_current_datadicc: pd.DataFrame, version: str, language: str) -> tuple[pd.DataFrame, list]:
    all_rows_lists = []
    list_variable_choices = []
    df_datadicc_lists = df_current_datadicc.loc[df_current_datadicc['Type'] == 'list']

    translations_for_language = get_translations(language)
    select_text = translations_for_language['select']
    specify_text = translations_for_language['specify']
    specify_other_text = translations_for_language['specify_other']
    specify_other_infection_text = translations_for_language['specify_other_infection']
    select_additional_text = translations_for_language['select_additional']
    any_additional_text = translations_for_language['any_additional']
    other_text = translations_for_language['other']

    for _, row in df_datadicc_lists.iterrows():
        if pd.isnull(row['List']):
            logger.warn('List without corresponding repository file')

        else:
            df_list_options = ArcApiClient().get_dataframe_arc_list_version_language(version, language,
                                                                                     row['List'].replace('_', '/'))

            list_choices = ''
            list_variable_choices_aux = []

            for lo in df_list_options[df_list_options.columns[0]]:
                cont_lo = set_cont_lo(df_list_options, lo)
                try:
                    list_variable_choices_aux.append([cont_lo, lo])
                    list_choices += str(cont_lo) + ', ' + lo + ' | '
                except Exception as e:
                    logger.error(e)
                    raise RuntimeError("Failed to determine list choices")

            list_choices = list_choices + '88, ' + other_text
            arrows = ['', '>', '->', '>->', '->->', '>->->']

            repeat_n = 5
            questions_for_this_list = []
            other_info = df_current_datadicc.loc[(df_current_datadicc['Sec'] == row['Sec']) &
                                                 (df_current_datadicc['vari'] == row['vari']) &
                                                 (df_current_datadicc['Variable'] != row['Variable'])]

            for n in range(repeat_n):
                # Falta agregar las otras opciones con el mismo sec_var
                dropdown_row = row.copy()
                dropdown_row['Variable'] = row['Sec'] + '_' + row['vari'] + '_' + str(n) + 'item'
                # dropdown_row['Answer Options'] = list_choises.replace("| 88, Other","| 88_"+str(n)+", Other")
                dropdown_row['Answer Options'] = list_choices
                dropdown_row['Type'] = "dropdown"
                dropdown_row['Validation'] = 'autocomplete'
                dropdown_row['Maximum'] = None
                dropdown_row['Minimum'] = None
                dropdown_row['List'] = None
                if row['Question_english'] != 'NSAIDs':
                    if n == 0:
                        if 'select' in row['Question_english'].lower():
                            dropdown_row['Question'] = arrows[n] + row['Question']
                        else:
                            dropdown_row['Question'] = f"{arrows[n]} {select_text} {row['Question'].lower()}"
                    else:
                        if 'select' in row['Question_english'].lower():
                            dropdown_row['Question'] = arrows[n] + row['Question'].lower() + ' ' + str(n + 1)
                        else:
                            dropdown_row[
                                'Question'] = f"{arrows[n]} {select_additional_text} {row['Question'].lower()} {str(n + 1)}"
                else:
                    if n == 0:
                        if 'select' in row['Question_english'].lower():
                            dropdown_row['Question'] = arrows[n] + row['Question']
                        else:
                            dropdown_row['Question'] = f"{arrows[n]} {select_text} {row['Question']}"
                    else:
                        if 'select' in row['Question_english'].lower():
                            dropdown_row['Question'] = arrows[n] + row['Question'] + ' ' + str(n + 1)
                        else:
                            dropdown_row[
                                'Question'] = f"{arrows[n]} {select_additional_text} {row['Question']} {str(n + 1)}"

                dropdown_row['mod'] = str(n) + 'item'
                dropdown_row['vari'] = row['vari']
                if n == 0:
                    dropdown_row['Skip Logic'] = '[' + row['Variable'] + "]='1'"
                else:
                    dropdown_row['Skip Logic'] = '[' + row['Sec'] + '_' + row['vari'] + '_' + str(
                        n - 1) + 'addi' + "]='1'"

                other_row = row.copy()
                other_row['Variable'] = row['Sec'] + '_' + row['vari'] + '_' + str(n) + 'otherl2'
                other_row['Answer Options'] = None
                other_row['Type'] = 'text'
                other_row['Maximum'] = None
                other_row['Minimum'] = None
                other_row['Skip Logic'] = '[' + dropdown_row['Variable'] + "]='88'"
                if row['Variable'] == 'inclu_disease':
                    other_row['Question'] = f"{arrows[n]} {specify_other_infection_text}"
                else:
                    if n == 0:
                        if row['Question_english'] != 'NSAIDs':
                            if 'other' in row['Question_english'].lower():
                                other_row['Question'] = f"{arrows[n]} {specify_text} {row['Question'].lower()}"
                            else:
                                other_row['Question'] = f"{arrows[n]} {specify_other_text} {row['Question'].lower()}"
                        else:
                            if 'other' in row['Question_english'].lower():
                                other_row['Question'] = f"{arrows[n]} {specify_text} {row['Question']}"
                            else:
                                other_row['Question'] = f"{arrows[n]} {specify_other_text} {row['Question']}"
                    else:
                        if row['Question_english'] != 'NSAIDs':
                            if 'other' in row['Question_english'].lower():
                                other_row[
                                    'Question'] = f"{arrows[n]} {specify_text} {row['Question'].lower()} {str(n + 1)}"
                            else:
                                other_row[
                                    'Question'] = f"{arrows[n]} {specify_other_text} {row['Question'].lower()} {str(n + 1)}"
                        else:
                            if 'other' in row['Question_english'].lower():
                                other_row['Question'] = f"{arrows[n]} {specify_text} {row['Question']} {str(n + 1)}"
                            else:
                                other_row[
                                    'Question'] = f"{arrows[n]} {specify_other_text} {row['Question']} {str(n + 1)}"
                other_row['List'] = None
                other_row['mod'] = str(n) + 'otherl2'
                other_row['vari'] = row['vari']
                questions_for_this_list.append(dropdown_row)
                questions_for_this_list.append(other_row)

                if len(other_info) > 1:
                    for index, oi in other_info.iterrows():
                        other_info_row = oi.copy()
                        if n == 0:
                            other_info_row['Question'] = arrows[n] + ' ' + oi['Question']
                        else:
                            other_info_row['Question'] = arrows[n] + ' ' + oi['Question'] + ' ' + str(n + 1)
                            other_info_row['Skip Logic'] = '[' + additional_row['Variable'] + "]='1'"
                        other_info_row['Variable'] = oi['Sec'] + '_' + oi['vari'] + '_' + str(n) + oi['mod']
                        other_info_row['Skip Logic'] = '[' + additional_row['Variable'] + "]='1'"
                        other_info_row['List'] = None
                        other_info_row['mod'] = str(n) + oi['mod']
                        other_info_row['vari'] = oi['vari']
                        questions_for_this_list.append(other_info_row)

                elif len(other_info) == 1:
                    oi = other_info.iloc[0]
                    other_info_row = oi.copy()
                    if n == 0:
                        other_info_row['Question'] = arrows[n] + '' + oi['Question']
                    else:
                        other_info_row['Question'] = arrows[n] + '' + oi['Question'] + ' ' + str(n + 1)
                        other_info_row['Skip Logic'] = '[' + additional_row['Variable'] + "]='1'"
                        other_info_row['Variable'] = oi['Sec'] + '_' + oi['vari'] + '_' + str(n) + oi['mod']
                        other_info_row['List'] = None
                        other_info_row['mod'] = str(n) + oi['mod']
                        other_info_row['vari'] = oi['vari']
                    questions_for_this_list.append(other_info_row)

                if n < repeat_n - 1:
                    additional_row = row.copy()
                    additional_row['Variable'] = row['Sec'] + '_' + row['vari'] + '_' + str(n) + 'addi'
                    additional_row['Answer Options'] = row['Answer Options']
                    additional_row['Type'] = 'radio'
                    additional_row['Maximum'] = None
                    additional_row['Minimum'] = None
                    additional_row['Skip Logic'] = dropdown_row['Skip Logic']
                    if additional_row['Question_english'] != 'NSAIDs':
                        additional_row[
                            'Question'] = f"{arrows[n]} {any_additional_text} {additional_row['Question'].lower()} ?"
                    else:
                        additional_row['Question'] = f"{arrows[n]} {any_additional_text} {additional_row['Question']} ?"
                    additional_row['List'] = None
                    additional_row['mod'] = str(n) + 'addi'
                    additional_row['vari'] = row['vari']
                    questions_for_this_list.append(additional_row)

            all_rows_lists.append(row)
            for qftl in questions_for_this_list:
                all_rows_lists.append(qftl)
            list_variable_choices.append([row['Variable'], list_variable_choices_aux])
    df_arc_list = pd.DataFrame(all_rows_lists).reset_index(drop=True)

    return df_arc_list, list_variable_choices


def set_cont_lo(df_list_options: pd.DataFrame,
                list_option: str) -> int:
    if 'Value' in df_list_options.columns:
        cont_lo = int(df_list_options['Value'].loc[df_list_options[df_list_options.columns[0]] == list_option].iloc[0])
    else:
        # fallback to index-based counting
        cont_lo = df_list_options[df_list_options.columns[0]].tolist().index(list_option) + 1

    if cont_lo == 88:
        cont_lo = 89
    elif cont_lo == 99:
        cont_lo = 100
    return cont_lo


def get_list_data(df_current_datadicc: pd.DataFrame,
                  version: str,
                  language: str,
                  list_type) -> tuple[list, list]:
    all_rows_lists = []
    list_variable_choices = []
    datadicc_disease_lists = df_current_datadicc.loc[df_current_datadicc['Type'] == list_type]

    translations_for_language = get_translations(language)
    select_text = translations_for_language['select']
    specify_text = translations_for_language['specify']
    specify_other_text = translations_for_language['specify_other']
    other_agent_text = translations_for_language['other_agent']
    other_text = translations_for_language['other']

    for _, row in datadicc_disease_lists.iterrows():
        if pd.isnull(row['List']):
            logger.warn('List without corresponding repository file')
        else:
            df_list_options = ArcApiClient().get_dataframe_arc_list_version_language(version, language,
                                                                                     row['List'].replace('_', '/'))

            l2_choices = ''
            l1_choices = ''
            list_variable_choices_aux = []
            for lo in df_list_options[df_list_options.columns[0]]:
                cont_lo = set_cont_lo(df_list_options, lo)
                try:
                    df_list_options['Selected'] = pd.to_numeric(df_list_options['Selected'], errors='coerce')

                    if df_list_options['Selected'].loc[df_list_options[df_list_options.columns[0]] == lo].iloc[0] == 1:
                        l1_choices += str(cont_lo) + ', ' + lo + ' | '
                        list_variable_choices_aux.append([cont_lo, lo, 1])
                    else:
                        l2_choices += str(cont_lo) + ', ' + lo + ' | '
                        list_variable_choices_aux.append([cont_lo, lo, 0])

                except Exception as e:
                    logger.error(e)
                    raise RuntimeError("Failed to add to lists of choices")

            l2_choices = l2_choices + '88, ' + other_text

            list_variable_choices.append([row['Variable'], list_variable_choices_aux])

            row['Answer Options'] = l1_choices + '88, ' + other_text

            dropdown_row = row.copy()
            other_row = row.copy()
            dropdown_row['Variable'] = row['Sec'] + '_' + row['vari'] + '_' + 'otherl2'
            dropdown_row['Answer Options'] = l2_choices
            dropdown_row['Type'] = "dropdown"
            dropdown_row['Validation'] = 'autocomplete'
            dropdown_row['Maximum'] = None
            dropdown_row['Minimum'] = None
            dropdown_row['List'] = None
            if row['Variable'] == 'medi_medtype':
                dropdown_row['Question'] = f"{select_text} {other_agent_text}"
                other_row['Question'] = f"{specify_text} {other_agent_text}"
            else:
                dropdown_row['Question'] = f"{select_text} {row['Question']}"
                other_row['Question'] = f"{specify_other_text} {row['Question']}"
            dropdown_row['mod'] = 'otherl2'
            dropdown_row['Skip Logic'] = '[' + row['Variable'] + "]='88'"

            other_row['Variable'] = row['Sec'] + '_' + row['vari'] + '_' + 'otherl3'
            other_row['Answer Options'] = None
            other_row['Type'] = 'text'
            other_row['Maximum'] = None
            other_row['Minimum'] = None
            if row['Variable'] != 'inclu_disease':
                other_row['Skip Logic'] = '[' + row['Sec'] + '_' + row['vari'] + '_' + 'otherl2' + "]='88'"
            else:
                other_row['Skip Logic'] = '[' + row['Variable'] + "]='88'"

            other_row['List'] = None
            other_row['mod'] = 'otherl3'

            row['Question'] = row['Question']

            all_rows_lists.append(row)
            if row['Variable'] != 'inclu_disease':
                all_rows_lists.append(dropdown_row)
            all_rows_lists.append(other_row)

    return list_variable_choices, all_rows_lists


def get_user_list_content(df_current_datadicc: pd.DataFrame,
                          version: str,
                          language: str) -> tuple[pd.DataFrame, list]:
    ulist_variable_choices, all_rows_lists = get_list_data(df_current_datadicc, version, language, 'user_list')
    df_arc_list = pd.DataFrame(all_rows_lists).reset_index(drop=True)
    return df_arc_list, ulist_variable_choices


def get_multi_list_content(df_current_datadicc: pd.DataFrame,
                           version: str,
                           language: str) -> tuple[pd.DataFrame, list]:
    multilist_variable_choices, all_rows_lists = get_list_data(df_current_datadicc, version, language, 'multi_list')
    df_arc_list = pd.DataFrame(all_rows_lists).reset_index(drop=True)
    return df_arc_list, multilist_variable_choices


def add_transformed_rows(df_selected_variables: pd.DataFrame,
                         df_arc_var_units_selected: pd.DataFrame,
                         variable_order: list) -> pd.DataFrame:
    df_arc_var_units_selected['Sec_vari'] = df_arc_var_units_selected['Sec'] + '_' + df_arc_var_units_selected['vari']
    df_transformed = df_selected_variables.copy().reset_index(drop=True)
    df_arc_var_units_selected = df_arc_var_units_selected[df_transformed.columns]

    for _, row in df_arc_var_units_selected.iterrows():
        variable = row['Variable']

        if variable in df_transformed['Variable'].values:
            # Get the index for the matching variable in the result DataFrame
            match_index = df_transformed.index[df_transformed['Variable'] == variable].tolist()[0]
            # Update each column separately
            for col in df_transformed.columns:
                df_transformed.at[match_index, col] = row[col]
        else:
            # Identify the base variable name by splitting at the last underscore
            base_var = '_'.join(variable.split('_')[:-1])

            if base_var in df_transformed['Variable'].values:
                # Find the index of the base variable row
                base_index = df_transformed.index[df_transformed['Variable'].str.startswith(base_var)].max()
                row_df = pd.DataFrame([row]).reset_index(drop=True)
                # Insert the new row immediately after the base variable row
                df_transformed = pd.concat(
                    [df_transformed.iloc[:base_index + 1], row_df, df_transformed.iloc[base_index + 1:]]).reset_index(
                    drop=True)


            else:
                # Variable to be added is not based on the base variable, use the order list
                variable_to_add = variable
                order_index = variable_order.index(variable_to_add) if variable_to_add in variable_order else None

                if order_index is not None:
                    # Find the next existing variable in 'result' from 'order'
                    insert_before_index = None
                    for next_variable in variable_order[order_index + 1:]:
                        if next_variable in df_transformed['Variable'].values:
                            insert_before_index = df_transformed.index[df_transformed['Variable'] == next_variable][0]
                            break

                    # Create a DataFrame from the current row
                    row_df = pd.DataFrame([row]).reset_index(drop=True)

                    # Insert the row at the determined position or append if no next variable is found
                    if insert_before_index is not None:
                        df_transformed = pd.concat(
                            [df_transformed.iloc[:insert_before_index], row_df,
                             df_transformed.iloc[insert_before_index:]]).reset_index(
                            drop=True)
                    else:
                        df_transformed = pd.concat([df_transformed, row_df]).reset_index(drop=True)
                else:
                    # If the variable is not in the order list, append it at the end (or handle as needed)
                    row_df = pd.DataFrame([row]).reset_index(drop=True)
                    df_transformed = pd.concat([df_transformed, row_df]).reset_index(drop=True)

    return df_transformed


def custom_alignment(df_datadicc: pd.DataFrame) -> pd.DataFrame:
    mask = (df_datadicc['Field Type'].isin(['checkbox', 'radio'])) & (
            (df_datadicc['Choices, Calculations, OR Slider Labels'].str.split('|').str.len() < 4) &
            (df_datadicc['Choices, Calculations, OR Slider Labels'].str.len() <= 40))
    df_datadicc.loc[mask, 'Custom Alignment'] = 'RH'
    return df_datadicc


def generate_crf(df_datadicc: pd.DataFrame) -> pd.DataFrame:
    # Create a new list to build the reordered rows
    new_rows = []
    used_indices = set()

    # Function to extract the prefix (e.g., "drug14_antiviral" from "drug14_antiviral_type")
    def get_prefix(variable):
        return "_".join(variable.split("_")[:2])

    # Loop through each row in the original dataframe
    for index, row in df_datadicc.iterrows():
        variable = row['Variable']
        variable_type = row['Type']

        # Skip rows that have already been added to the new list
        if index in used_indices:
            continue

        # Add the current row to the reordered list
        new_rows.append(row)
        used_indices.add(index)

        # If it's a multi_list or dropdown, check for corresponding _otherl2 and _otherl3
        if variable_type in ['multi_list', 'user_list']:
            prefix = get_prefix(variable)

            # Find and add the _otherl2 and _otherl3 rows right after the current one
            for suffix in ['_otherl2', '_otherl3']:
                mask = df_datadicc['Variable'].str.startswith(prefix + suffix)
                for i in df_datadicc[mask].index:
                    new_rows.append(df_datadicc.loc[i])
                    used_indices.add(i)

    # Create the final reordered dataframe
    df_datadicc = pd.DataFrame(new_rows)

    df_datadicc.loc[df_datadicc['Type'] == 'user_list', 'Type'] = 'radio'
    df_datadicc.loc[df_datadicc['Type'] == 'multi_list', 'Type'] = 'checkbox'
    df_datadicc.loc[df_datadicc['Type'] == 'list', 'Type'] = 'radio'
    df_datadicc = df_datadicc[[
        'Form',
        'Section',
        'Variable',
        'Type',
        'Question',
        'Answer Options',
        'Validation',
        'Minimum',
        'Maximum',
        'Skip Logic',
    ]]

    df_datadicc.columns = [
        "Form Name",
        "Section Header",
        "Variable / Field Name",
        "Field Type",
        "Field Label",
        "Choices, Calculations, OR Slider Labels",
        "Text Validation Type OR Show Slider Number",
        "Text Validation Min",
        "Text Validation Max",
        "Branching Logic (Show field only if...)"
    ]
    redcap_cols = [
        'Variable / Field Name',
        'Form Name',
        'Section Header',
        'Field Type',
        'Field Label',
        'Choices, Calculations, OR Slider Labels',
        'Field Note',
        'Text Validation Type OR Show Slider Number',
        'Text Validation Min',
        'Text Validation Max',
        'Identifier?',
        'Branching Logic (Show field only if...)',
        'Required Field?',
        'Custom Alignment',
        'Question Number (surveys only)',
        'Matrix Group Name',
        'Matrix Ranking?',
        'Field Annotation'
    ]
    df_datadicc = df_datadicc.reindex(columns=redcap_cols)

    df_datadicc.loc[
        df_datadicc['Field Type'].isin([
            'date_dmy',
            'number',
            'integer',
            'datetime_dmy',
        ]), 'Field Type'] = 'text'
    df_datadicc = df_datadicc.loc[
        df_datadicc['Field Type'].isin([
            'text',
            'notes',
            'radio',
            'dropdown',
            'calc',
            'file',
            'checkbox',
            'yesno',
            'truefalse',
            'descriptive',
            'slider',
        ])]
    df_datadicc['Section Header'] = df_datadicc['Section Header'].where(
        df_datadicc['Section Header'] != df_datadicc['Section Header'].shift(), np.nan)
    # For the new empty columns, fill NaN values with a default value (in this case an empty string)
    df_datadicc = df_datadicc.fillna('')

    df_datadicc['Section Header'] = df_datadicc['Section Header'].replace({'': np.nan})
    df_datadicc = custom_alignment(df_datadicc)

    return df_datadicc
