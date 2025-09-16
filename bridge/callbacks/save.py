import io
import json
from datetime import datetime

import dash
import pandas as pd
from dash import dcc, Input, Output, State

from bridge.utils.crf_name import get_crf_name
from bridge.utils.trigger_id import get_trigger_id

pd.options.mode.copy_on_write = True


@dash.callback(
    [
        Output('loading-output-save', 'children'),
        Output('save-crf', 'data'),
    ],
    [
        Input('crf_save', 'n_clicks'),
        Input('input', 'checked'),
    ],
    [
        State('current_datadicc-store', 'data'),
        State('selected-version-store', 'data'),
        State('selected-language-store', 'data'),
        State('crf_name', 'value'),
        State('ulist_variable_choices-store', 'data'),
        State('multilist_variable_choices-store', 'data'),
    ],
    prevent_initial_call=True
)
def on_save_click(n_clicks, checked_variables, current_datadicc_saved, selected_version_data, selected_language_data,
                  crf_name, ulist_variable_choices_saved, multilist_variable_choices_saved):
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

        df_ulist_all = pd.DataFrame(json.loads(ulist_variable_choices_saved), columns=['Variable', 'Ulist'])
        df_multilist_all = pd.DataFrame(json.loads(multilist_variable_choices_saved),
                                        columns=['Variable', 'Multilist'])

        df_ulist_out = get_checked_data_for_list(df_ulist_all, checked_variables, 'Ulist')
        df_multilist_out = get_checked_data_for_list(df_multilist_all, checked_variables, 'Multilist')

        df_save = pd.merge(df_save, df_ulist_out, how='left', on='Variable')
        df_save = pd.merge(df_save, df_multilist_out, how='left', on='Variable')

        output = io.BytesIO()
        df_save.to_csv(output, index=False, encoding='utf8')
        output.seek(0)

        return '', dcc.send_bytes(output.getvalue(), filename_csv)
    else:
        return '', None


def get_checked_data_for_list(df_list, checked_variables, list_type) -> pd.DataFrame:
    column_list = ['Variable', f'{list_type} Selected']
    df_out = pd.DataFrame(columns=column_list)
    df_list_checked = df_list[df_list['Variable'].isin(checked_variables)]
    if not df_list_checked.empty:
        for index, row in df_list_checked.iterrows():
            list_name = row['Variable']
            list_values = row[list_type]
            selected_list = []
            df_selected = pd.DataFrame(columns=column_list)
            for list_value in list_values:
                list_value_name = list_value[1]
                list_value_checked = int(list_value[2])
                if list_value_checked == 1:
                    selected_list.append(list_value_name)
            df_selected.loc[index, 'Variable'] = str(list_name)
            df_selected.loc[index, f'{list_type} Selected'] = '|'.join(selected_list)
            df_out = pd.concat([df_out, df_selected], ignore_index=True)
    return df_out
