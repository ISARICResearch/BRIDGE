import re

import numpy as np
import pandas as pd

from bridge.arc import arc_translations
from bridge.arc.arc_api import ArcApiClient
from bridge.logging.logger import setup_logger

logger = setup_logger(__name__)

pd.options.mode.copy_on_write = True


def get_arc(version: str) -> tuple[pd.DataFrame, list, str]:
    logger.info(f'version: {version}')

    commit_sha = ArcApiClient().get_arc_version_sha(version)
    df_datadicc = ArcApiClient().get_dataframe_arc_sha(commit_sha,
                                                       version)

    try:
        df_dependencies = get_dependencies(df_datadicc)
        df_datadicc = pd.merge(df_datadicc, df_dependencies[['Variable', 'Dependencies']], on='Variable')

        df_datadicc['Branch'] = df_datadicc.apply(lambda row: arc_translations.process_skip_logic(row, df_datadicc),
                                                  axis=1)

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


def get_arc_versions() -> tuple[list, str]:
    version_list = ArcApiClient().get_arc_version_list()
    logger.info(f'version_list: {version_list}')
    return version_list, max(version_list)


def add_required_datadicc_columns(df_datadicc: pd.DataFrame) -> pd.DataFrame:
    df_datadicc[['Sec', 'vari', 'mod']] = df_datadicc['Variable'].str.split('_', n=2, expand=True)
    df_datadicc[['Sec_name', 'Expla']] = df_datadicc['Section'].str.split(r'[(|:]', n=1, expand=True)
    return df_datadicc


def get_variable_order(df_current_datadicc: pd.DataFrame) -> list:
    df_current_datadicc['Sec_vari'] = df_current_datadicc['Sec'] + '_' + df_current_datadicc['vari']
    order = df_current_datadicc[['Sec_vari']]
    order = order.drop_duplicates().reset_index()
    return list(order['Sec_vari'])


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


def extract_parenthesis_content(text: str) -> str:
    match = re.search(r'\(([^)]+)\)$', text)
    return match.group(1) if match else text


def get_include_not_show(selected_variables: pd.Series,
                         df_current_datadicc: pd.DataFrame) -> pd.DataFrame:
    include_not_show = ['otherl2', 'otherl3', 'agent', 'agent2', 'warn', 'warn2', 'warn3',
                        'units', 'add', 'vol', '0item', '0otherl2',
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


            options = ' | '.join([f"{idx + 1},{extract_parenthesis_content(str(r['Question']))}" for idx, (_, r) in
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
        return (df_icc_var_units_selected_rows,
                sorted(list(set(delete_this_variables_with_units) - set(df_icc_var_units_selected_rows['Variable']))))
    return (None,
            None)


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


def generate_crf(df_datadicc: pd.DataFrame) -> pd.DataFrame:
    # Create a new list to build the reordered rows
    new_rows = []
    used_indices = set()

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
            # Extract the prefix (e.g., "drug14_antiviral" from "drug14_antiviral_type")
            prefix = "_".join(variable.split("_")[:2])

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
    df_datadicc = _custom_alignment(df_datadicc)

    return df_datadicc


def _custom_alignment(df_datadicc: pd.DataFrame) -> pd.DataFrame:
    mask = (df_datadicc['Field Type'].isin(['checkbox', 'radio'])) & (
            (df_datadicc['Choices, Calculations, OR Slider Labels'].str.split('|').str.len() < 4) &
            (df_datadicc['Choices, Calculations, OR Slider Labels'].str.len() <= 40))
    df_datadicc.loc[mask, 'Custom Alignment'] = 'RH'
    return df_datadicc
