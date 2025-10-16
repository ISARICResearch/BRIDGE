import pandas as pd

from bridge.arc import arc_core


def get_tree_items(df_datadicc: pd.DataFrame,
                   version: str | None) -> dict:
    include_not_show = [
        'otherl3', 'otherl2',
        'route', 'route2',
        'agent', 'agent2',
        'warn', 'warn2', 'warn3',
        'units',
        'add', 'vol', 'txt', 'calc'
    ]

    if 'Dependencies' not in df_datadicc.columns:
        dependencies = arc_core.get_dependencies(df_datadicc)
        df_datadicc = pd.merge(df_datadicc, dependencies[['Variable', 'Dependencies']], on='Variable')

    df_datadicc = arc_core.add_required_datadicc_columns(df_datadicc)

    df_datadicc['select units'] = (
        df_datadicc['Question'].str.contains('(select units)', case=False, na=False, regex=False))
    df_datadicc = arc_core.set_select_units(df_datadicc)

    df_for_item = df_datadicc[[
        'Form',
        'Sec_name',
        'vari',
        'mod',
        'Question',
        'Variable',
        'Type',
    ]].loc[~df_datadicc['mod'].isin(include_not_show)]
    df_for_item = df_for_item[df_for_item['Sec_name'].notna()]

    tree_dict = {
        'title': version,
        'key': 'ARC', 'children': [],
    }
    seen_forms_set = set()
    seen_sections_dict = {}
    primary_question_keys_dict = {}  # To keep track of primary question nodes

    for index, row in df_for_item.iterrows():
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
        if form not in seen_forms_set:
            form_node_dict = {
                'title': form,
                'key': form, 'children': [],
            }
            tree_dict['children'].append(form_node_dict)
            seen_forms_set.add(form)
            seen_sections_dict[form] = set()

        # Add section node if not already added for this form
        if sec_name not in seen_sections_dict[form]:
            sec_node_dict = {
                'title': sec_name,
                'key': f"{form}-{sec_name}", 'children': [],
            }
            for child_dict in tree_dict['children']:
                if child_dict['title'] == form:
                    child_dict['children'].append(sec_node_dict)
                    break
            seen_sections_dict[form].add(sec_name)

        # Check if the question is a primary node or a child node
        if mod is None or pd.isna(mod):
            # Primary node
            primary_question_node_dict = {
                'title': question,
                'key': question_key,
                'children': [],
            }
            primary_question_keys_dict[(form, vari)] = question_key
            for form_child_dict in tree_dict['children']:
                if form_child_dict['title'] == form:
                    for sec_child_dict in form_child_dict['children']:
                        if sec_child_dict['title'] == sec_name:
                            sec_child_dict['children'].append(primary_question_node_dict)
                            break
        else:
            # Child node of a primary node
            primary_key = primary_question_keys_dict.get((form, vari))
            if primary_key:
                question_node_dict = {
                    'title': question,
                    'key': question_key,
                }
                # Find the correct primary question node to add this question
                for form_child_dict in tree_dict['children']:
                    if form_child_dict['title'] == form:
                        for sec_child_dict in form_child_dict['children']:
                            if sec_child_dict['title'] == sec_name:
                                for primary_question_dict in sec_child_dict['children']:
                                    if primary_question_dict['key'] == primary_key:
                                        primary_question_dict['children'].append(question_node_dict)
                                        break

    return tree_dict
