# -- IMPORTS --

# -- Standard libraries --
import sys
import unittest.mock as mock

# -- 3rd party libraries --

# -- Internal libraries --
from bridge.generate_pdf.paper_crf import generate_paperlike_pdf


class TestGeneratePaperlikePdf:
    def test_generate_paperlike_crf_pdf__hantavirus_crf__arc_1_2_2__english(
        self,
        ccpuk_hantavirus_data_dictionary_2026,
        arc_1_2_2__english__paperlike_crf_details,
        arc_1_2_2__english__supplemental_phrases,
    ):
        # import ipdb;ipdb.set_trace()
        data_dictionary = ccpuk_hantavirus_data_dictionary_2026
        mock_arc_api_client = mock.MagicMock()
        mock_arc_api_client.get_dataframe_paper_like_details.return_value = (
            arc_1_2_2__english__paperlike_crf_details
        )
        mock_arc_api_client.get_dataframe_supplemental_phrases.return_value = (
            arc_1_2_2__english__supplemental_phrases
        )
        with mock.patch(
            "bridge.generate_pdf.paper_crf.ArcApiClient",
            return_value=mock_arc_api_client,
        ) as _:
            received_pdf = generate_paperlike_pdf(
                data_dictionary, version="1.2.2", db_name="HANTA", language="English"
            )

            mock_arc_api_client.get_dataframe_paper_like_details.assert_called_once_with(
                "1.2.2", "English"
            )
            mock_arc_api_client.get_dataframe_supplemental_phrases.assert_called_once_with(
                "1.2.2", "English"
            )
            assert isinstance(received_pdf, bytes)
            assert sys.getsizeof(received_pdf) > 0
