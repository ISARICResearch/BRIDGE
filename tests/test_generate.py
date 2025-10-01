from contextvars import copy_context
from datetime import date, datetime
from unittest import mock

import pandas as pd
import pytest

import bridge.callbacks.generate as generate


@pytest.mark.parametrize(
    "n_clicks, json_data, selected_version_data, selected_language_data, checked_presets, crf_name, output_files, browser_info, expected_output",
    [
        (None, None, None, None, None, None, None, None, ("", None, None, None, None)),
        (1, '{}', None, None, None, None, None, None, ("", None, None, None, None)),
    ]
)
def test_on_generate_click_no_action(n_clicks,
                                     json_data,
                                     selected_version_data,
                                     selected_language_data,
                                     checked_presets,
                                     crf_name,
                                     output_files,
                                     browser_info,
                                     expected_output):
    output = get_output_on_generate_click(n_clicks,
                                          json_data,
                                          selected_version_data,
                                          selected_language_data,
                                          checked_presets,
                                          crf_name,
                                          output_files,
                                          browser_info)

    assert output == expected_output


@pytest.mark.parametrize(
    "selected_language_data, browser_info, expected_output",
    [
        ({'selected_language': 'English'}, 'Chrome/139.0.0.0 Safari/537.36',
         ('',
          'UEsDBBQAAAAAANJmQVvCdv2k',
          'UEsDBBQAAAAAANJmQVvCdv2k',
          'UEsDBBQAAAAAANJmQVvCdv2k',
          'UEsDBBQAAAAAANJmQVvCdv2k')
         ),
        ({'selected_language': 'French'}, 'Safari/537.36',
         ('',
          'UEsDBBQAAAAAANJmQVvCdv2k',
          None,
          None,
          None)
         ),
    ]
)
@mock.patch('bridge.callbacks.generate.dcc.send_bytes')
@mock.patch('bridge.callbacks.generate.paper_crf.generate_completion_guide')
@mock.patch('bridge.callbacks.generate.paper_crf.generate_pdf')
@mock.patch('bridge.callbacks.generate.arc.generate_crf')
@mock.patch('bridge.callbacks.generate.datetime')
@mock.patch('bridge.callbacks.generate.get_crf_name', return_value='test_crf')
@mock.patch('bridge.callbacks.generate.get_trigger_id', return_value='crf_generate')
def test_on_generate_click(
        mock_trigger_id,
        mock_crf_name,
        mock_date,
        mock_crf_csv,
        mock_crf_pdf,
        mock_guide_pdf,
        mock_send_bytes,
        selected_language_data,
        browser_info,
        expected_output,
):
    mock_date.today.return_value = datetime(2025, 9, 30)
    mock_date.side_effect = lambda *args, **kw: date(*args, **kw)

    n_clicks = 1
    json_data = '{"columns":["Form"], "index":[0], "data":[["presentation"]]}'  # This isn't being used, but needs to be readable
    selected_version_data = {'selected_version': 'v1.1.2'}
    checked_presets = [[], [], [], [], []]
    crf_name = 'test'
    output_files = ['redcap_xml', 'redcap_csv', 'paper_like']
    mock_pdf = b'%PDF-1.4\n%\x93\x8c\x8b\x9e ReportLab Generated PDF document http://www.reportlab.com\n'
    data = {
        'Variable / Field Name': ['subjid',
                                  'inclu_disease',
                                  'inclu_consentdes'],
        'Form Name': ['presentation',
                      'presentation',
                      'presentation'],
        'Field Type': ['text',
                       'radio',
                       'descriptive'],
        'Field Label': ['Participant Identification Number (PIN)',
                        'Suspected or confirmed infection',
                        '<div class=""rich-text-field-label""><h5 style=""text-align: center;""><span style=""color: #236fa1;"">Consent:</span></h5></div>']
    }
    df = pd.DataFrame.from_dict(data)

    mock_crf_csv.return_value = df
    mock_crf_pdf.return_value = mock_pdf
    mock_guide_pdf.return_value = mock_pdf
    mock_send_bytes.return_value = 'UEsDBBQAAAAAANJmQVvCdv2k'

    output = get_output_on_generate_click(n_clicks,
                                          json_data,
                                          selected_version_data,
                                          selected_language_data,
                                          checked_presets,
                                          crf_name,
                                          output_files,
                                          browser_info)
    assert output == expected_output


@pytest.mark.parametrize(
    "n_clicks, json_data, selected_version_data, selected_language_data, checked_presets, crf_name, output_files, browser_info, expected_output",
    [
        (1, '{"columns":["Form"], "index":[0], "data":[["presentation"]]}', None, None, None, None, None, None,
         ("", None, None, None, None)),
    ]
)
@mock.patch('bridge.callbacks.generate.get_trigger_id', return_value='crf_not_generate')
def test_on_generate_click_wrong_trigger_id(mock_trigger_id,
                                            n_clicks,
                                            json_data,
                                            selected_version_data,
                                            selected_language_data,
                                            checked_presets,
                                            crf_name,
                                            output_files,
                                            browser_info,
                                            expected_output):
    output = get_output_on_generate_click(n_clicks,
                                          json_data,
                                          selected_version_data,
                                          selected_language_data,
                                          checked_presets,
                                          crf_name,
                                          output_files,
                                          browser_info)

    assert output == expected_output


def get_output_on_generate_click(n_clicks,
                                 json_data,
                                 selected_version_data,
                                 selected_language_data,
                                 checked_presets,
                                 crf_name,
                                 output_files,
                                 browser_info):
    def run_callback():
        return generate.on_generate_click(n_clicks,
                                          json_data,
                                          selected_version_data,
                                          selected_language_data,
                                          checked_presets,
                                          crf_name,
                                          output_files,
                                          browser_info)

    ctx = copy_context()
    output = ctx.run(run_callback)
    return output
