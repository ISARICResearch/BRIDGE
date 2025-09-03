import io
import json
import zipfile
from datetime import datetime
from os.path import join, dirname, abspath

import dash
import pandas as pd
from dash import dcc, Input, Output, State
from unidecode import unidecode

from bridge.arc import arc
from bridge.generate_pdf import paper_crf
from bridge.create_outputs.utils import get_crf_name, get_trigger_id

pd.options.mode.copy_on_write = True


class Generate:

    def __init__(self):
        self.config_dir = join(dirname(dirname(dirname(abspath(__file__)))), 'assets', 'config_files')
        self.xml_file_name = 'ISARIC Clinical Characterisation Setup.xml'

    def register_callbacks(self, app):

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
        def on_generate_click(n_clicks, json_data, selected_version_data, selected_language_data, checked_presets,
                              crf_name, output_files, browser_info):
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

                selected_variables_from_data = pd.read_json(io.StringIO(json_data), orient='split')
                current_version = selected_version_data.get('selected_version', None)
                language = selected_language_data.get('selected_language', None)

                df = arc.generate_crf(selected_variables_from_data)
                pdf_crf = paper_crf.generate_pdf(df, current_version, crf_name, language)
                pdf_data = paper_crf.generate_completion_guide(selected_variables_from_data, current_version, crf_name)

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
                xml_file_path = f'{self.config_dir}/{self.xml_file_name}'
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
                            zip_file.writestr(self.xml_file_name, xml_content)
                    zip_buffer.seek(0)
                    return "", dcc.send_bytes(zip_buffer.getvalue(), f"{crf_name}_bundle_{date}.zip"), None, None, None

                return (
                    "",
                    dcc.send_bytes(csv_buffer.getvalue(),
                                   f"{crf_name}_DataDictionary_{date}.csv") if 'redcap_csv' in output_files else None,
                    dcc.send_bytes(pdf_data,
                                   f"{crf_name}_Completion_Guide_{date}.pdf") if 'paper_like' in output_files else None,
                    dcc.send_bytes(xml_content, self.xml_file_name) if 'redcap_xml' in output_files else None,
                    dcc.send_bytes(pdf_crf,
                                   f"{crf_name}_paperlike_{date}.pdf") if 'paper_like' in output_files else None
                )

            else:
                return "", None, None, None, None

        return app
