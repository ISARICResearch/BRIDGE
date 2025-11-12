import pandas as pd

from bridge.arc import arc_translations
from bridge.arc.arc_api import ArcApiClient
from bridge.logging.logger import setup_logger

logger = setup_logger(__name__)


def get_list_content(df_current_datadicc: pd.DataFrame, version: str, language: str) -> tuple[pd.DataFrame, list]:
    all_rows_lists = []
    list_variable_choices = []
    df_datadicc_lists = df_current_datadicc.loc[df_current_datadicc['Type'] == 'list']

    translations_for_language = arc_translations.get_translations(language)
    select_text = translations_for_language['select']
    specify_text = translations_for_language['specify']
    specify_other_text = translations_for_language['specify_other']
    specify_other_infection_text = translations_for_language['specify_other_infection']
    select_additional_text = translations_for_language['select_additional']
    any_additional_text = translations_for_language['any_additional']
    other_text = translations_for_language['other']

    for _, row in df_datadicc_lists.iterrows():
        if pd.isnull(row['List']):
            logger.warning('List without corresponding repository file')

        else:
            df_list_options = ArcApiClient().get_dataframe_arc_list_version_language(version, language,
                                                                                     str(row['List']).replace('_', '/'))

            list_choices = ''
            list_variable_choices_aux = []

            for list_option in df_list_options[df_list_options.columns[0]]:
                cont_lo = set_cont_lo(df_list_options, str(list_option))
                try:
                    list_variable_choices_aux.append([cont_lo, list_option])
                    list_choices += str(cont_lo) + ', ' + str(list_option) + ' | '
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
        cont_lo = df_list_options[df_list_options.columns[0]].values.tolist().index(list_option) + 1

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

    translations_for_language = arc_translations.get_translations(language)
    select_text = translations_for_language['select']
    specify_text = translations_for_language['specify']
    specify_other_text = translations_for_language['specify_other']
    other_agent_text = translations_for_language['other_agent']
    other_text = translations_for_language['other']

    for _, row in datadicc_disease_lists.iterrows():
        if pd.isnull(row['List']):
            logger.warning('List without corresponding repository file')
        else:
            df_list_options = ArcApiClient().get_dataframe_arc_list_version_language(version, language,
                                                                                     str(row['List']).replace('_', '/'))

            l2_choices = ''
            l1_choices = ''
            list_variable_choices_aux = []
            for lo in df_list_options[df_list_options.columns[0]]:
                cont_lo = set_cont_lo(df_list_options, str(lo))
                try:
                    df_list_options['Selected'] = pd.to_numeric(df_list_options['Selected'], errors='coerce')

                    if df_list_options['Selected'].loc[df_list_options[df_list_options.columns[0]] == lo].iloc[0] == 1:
                        l1_choices += str(cont_lo) + ', ' + str(lo) + ' | '
                        list_variable_choices_aux.append([cont_lo, lo, 1])
                    else:
                        l2_choices += str(cont_lo) + ', ' + str(lo) + ' | '
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
            if list_type == 'multi_list':
                dropdown_row['Skip Logic'] = '[' + row['Variable'] + "(88)]='1'"

            else:
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
