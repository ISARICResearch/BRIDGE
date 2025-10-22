import pandas as pd


def _qtitle(row):
    if row['Type'] == 'user_list':
        return '↳ ' + row['Question']
    elif row['Type'] == 'multi_list':
        return '⇉ ' + row['Question']
    return row['Question']


def get_tree_items(df_datadicc: pd.DataFrame,
                   version: str) -> dict:
    include_not_show = [
        'otherl3', 'otherl2', 'route', 'route2', 'agent', 'agent2',
        'warn', 'warn2', 'warn3', 'units', 'add', 'vol', 'txt', 'calc'
    ]

    # rows used for the tree (hide some mods)
    df_for_item = df_datadicc[['Form', 'Sec_name', 'vari', 'mod', 'Question', 'Variable', 'Type']].loc[
        ~df_datadicc['mod'].isin(include_not_show)
    ]

    # -------- counts per (Form, Sec_name, vari) --------
    base_for_counts = df_for_item[['Form', 'Sec_name', 'vari']].copy()
    group_counts_total = (
        base_for_counts
        .groupby(['Form', 'Sec_name', 'vari'], dropna=False)
        .size()
        .rename('n_in_vari_total')
        .reset_index()
    )
    # ---------------------------------------------------

    # prep indexing and "first question"
    df_for_item = df_for_item[df_for_item['Sec_name'].notna()].copy()
    df_for_item['_row_order'] = range(len(df_for_item))
    df_idx_first = (
        df_for_item.sort_values('_row_order')
        .groupby(['Form', 'Sec_name', 'vari'], dropna=False, as_index=False)
        .nth(0)[['Form', 'Sec_name', 'vari', 'Question', 'Variable']]
        .rename(columns={'Question': 'first_question', 'Variable': 'first_variable'})
        .reset_index(drop=True)
    )

    # merge counts + first-question
    df_for_item = (df_for_item
                   .merge(group_counts_total, on=['Form', 'Sec_name', 'vari'], how='left')
                   .merge(df_idx_first, on=['Form', 'Sec_name', 'vari'], how='left'))

    # question title prefix
    def _qtitle(row):
        if row['Type'] == 'user_list':
            return '↳ ' + row['Question']
        elif row['Type'] == 'multi_list':
            return '⇉ ' + row['Question']
        return row['Question']

    tree = {'title': version.replace('ICC', 'ARC'), 'key': 'ARC', 'children': []}
    seen_forms, seen_sections = set(), {}

    # Build tree
    for (form, sec_name), sec_df in df_for_item.groupby(['Form', 'Sec_name'], dropna=False, sort=False):
        form_upper = str(form).upper()
        sec_name_upper = str(sec_name).upper()

        # form
        if form_upper not in seen_forms:
            tree['children'].append({
                'title': form_upper,
                'key': form_upper,
                'children': [],
            })
            seen_forms.add(form_upper)
            seen_sections[form_upper] = set()
        # section
        if sec_name_upper not in seen_sections[form_upper]:
            for child in tree['children']:
                if child['title'] == form_upper:
                    child['children'].append(
                        {
                            'title': sec_name_upper,
                            'key': f'{form_upper}-{sec_name_upper}',
                            'children': [],
                        })
                    break
            seen_sections[form_upper].add(sec_name_upper)

        # find section node
        section_node = None
        for child in tree['children']:
            if child['title'] == form_upper:
                for sec_child in child['children']:
                    if sec_child['title'] == sec_name_upper:
                        section_node = sec_child
                        break

        sec_df = sec_df.sort_values('_row_order')
        for vari, vari_df in sec_df.groupby('vari', dropna=False, sort=False):
            # SPECIAL CASE: when a "(select units)" question exists in this vari,
            # make THAT row the parent, and attach all other rows (same vari) as children.
            mask_units = vari_df['Question'].str.contains('(select units)', case=False, na=False, regex=False)
            if mask_units.any():
                parent_row = vari_df.loc[mask_units].iloc[0]
                parent_title = _qtitle(parent_row)
                parent_key = f"{parent_row['Variable']}"  # use the units variable as the parent key

                parent_node = {'title': parent_title, 'key': parent_key, 'children': []}
                section_node['children'].append(parent_node)

                # add children excluding the units row
                for _, r in vari_df.loc[~mask_units].iterrows():
                    parent_node['children'].append({'title': _qtitle(r), 'key': f"{r['Variable']}"})
                continue  # this vari handled

            # Fallback: your normal grouping (>=3 => group; else flat)
            n_total = int(vari_df['n_in_vari_total'].iloc[0] if pd.notna(vari_df['n_in_vari_total'].iloc[0]) else 0)

            if n_total >= 3:
                parent_title = vari_df['first_question'].iloc[0]
                parent_key = f"{form_upper}-{sec_name_upper}-VARI-{vari}-GROUP"
                parent_node = {
                    'title': parent_title + ' (Group)',
                    'key': parent_key,
                    'children': [],
                }
                section_node['children'].append(parent_node)

                for _, r in vari_df.iterrows():
                    parent_node['children'].append({'title': _qtitle(r), 'key': f"{r['Variable']}"})
            else:
                for _, r in vari_df.iterrows():
                    section_node['children'].append({'title': _qtitle(r), 'key': f"{r['Variable']}"})

    return tree
