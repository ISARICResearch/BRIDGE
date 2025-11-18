import io
import json
import zipfile
from datetime import datetime
from os.path import join, dirname, abspath

import dash
import pandas as pd
from dash import dcc, Input, Output, State
from unidecode import unidecode

from bridge.arc import arc_core
from bridge.generate_pdf import paper_crf
from bridge.generate_pdf import paper_word
from bridge.utils.crf_name import get_crf_name
from bridge.utils.trigger_id import get_trigger_id

pd.options.mode.copy_on_write = True

CONFIG_DIR = join(dirname(dirname(dirname(abspath(__file__)))), 'assets', 'config_files')
XML_FILE_NAME = 'ISARIC Clinical Characterisation Setup'


@dash.callback(
    [
        Output("loading-output-generate", "children"),
        Output("download-dataframe-csv", "data"),
        Output("download-compGuide-pdf", "data"),
        Output("download-projectxml-pdf", "data"),
        Output("download-paperlike-pdf", "data"),
        Output("download-paperlike-docx", "data"),  # NUEVO
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
def on_generate_click(n_clicks: int,
                      json_data: str,
                      selected_version_data: dict,
                      selected_language_data: dict,
                      checked_presets: list,
                      crf_name: str,
                      output_files: list,
                      browser_info: str):
    ctx = dash.callback_context

    if not n_clicks:
        return ("", None, None, None, None, None)

    if not any(json.loads(json_data).values()):
        # Nothing ticked
        return ("", None, None, None, None, None)

    trigger_id = get_trigger_id(ctx)

    if trigger_id == 'crf_generate':
        date = datetime.today().strftime('%Y-%m-%d')
        crf_name = get_crf_name(crf_name, checked_presets)

        selected_variables_from_data = pd.read_json(io.StringIO(json_data), orient='split')
        version = selected_version_data.get('selected_version')
        language = selected_language_data.get('selected_language')

        df_crf = arc_core.generate_crf(selected_variables_from_data)

        # PDFs
        pdf_crf = paper_crf.generate_pdf(df_crf, version, crf_name, language)
        pdf_data = paper_crf.generate_completion_guide(selected_variables_from_data, version, crf_name)
        
        # WORD
        word_bytes = paper_word.df_to_word(df_crf)

        # CSV 
        csv_buffer = io.BytesIO()
        df_crf.loc[df_crf['Field Type'] == 'descriptive', 'Field Label'] = df_crf.loc[
            df_crf['Field Type'] == 'descriptive', 'Field Label'].apply(
            lambda x: f'<div class="rich-text-field-label"><h5 style="text-align: center;"><span style="color: #236fa1;">{x}</span></h5></div>')
        if language != 'English':
            df_crf['Form Name'] = df_crf['Form Name'].apply(lambda x: unidecode(str(x)))

        df_crf.to_csv(csv_buffer, index=False, encoding='utf8')
        csv_buffer.seek(0)

        # XML
        xml_file_name = f'{XML_FILE_NAME}_{language}.xml'
        xml_file_path = f'{CONFIG_DIR}/{xml_file_name}'
        with open(xml_file_path, 'rb') as file:
            xml_content = file.read()

        # if safari
        is_safari = browser_info and "Safari" in browser_info and "Chrome" not in browser_info

        
        include_csv = 'redcap_csv' in output_files
        include_pdf_paper = 'paper_like' in output_files
        include_xml = 'redcap_xml' in output_files
        include_word = 'paper_word' in output_files

        if is_safari:
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, 'w') as zip_file:
                if include_csv:
                    zip_file.writestr(f"{crf_name}_DataDictionary_{date}.csv", csv_buffer.getvalue())
                if include_pdf_paper:
                    zip_file.writestr(f"{crf_name}_Completion_Guide_{date}.pdf", pdf_data)
                    zip_file.writestr(f"{crf_name}_paperlike_{date}.pdf", pdf_crf)
                if include_word:
                    zip_file.writestr(f"{crf_name}_CRFreview_{date}.docx", word_bytes)
                if include_xml:
                    zip_file.writestr(xml_file_name, xml_content)

            zip_buffer.seek(0)
            return (
                "",
                dcc.send_bytes(zip_buffer.getvalue(), f"{crf_name}_bundle_{date}.zip"),
                None,
                None,
                None,
                None,
            )

        
        return (
            "",
            dcc.send_bytes(csv_buffer.getvalue(),
                           f"{crf_name}_DataDictionary_{date}.csv") if include_csv else None,
            dcc.send_bytes(pdf_data,
                           f"{crf_name}_Completion_Guide_{date}.pdf") if include_pdf_paper else None,
            dcc.send_bytes(xml_content, xml_file_name) if include_xml else None,
            dcc.send_bytes(pdf_crf,
                           f"{crf_name}_paperlike_{date}.pdf") if include_pdf_paper else None,
            dcc.send_bytes(word_bytes,
                           f"{crf_name}_CRFreview_{date}.docx") if include_word else None,
        )

    else:
        return ("", None, None, None, None, None)

