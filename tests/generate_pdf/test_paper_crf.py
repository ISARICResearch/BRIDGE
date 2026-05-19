# -- IMPORTS --

# -- Standard libraries --
import sys

# -- 3rd party libraries --

# -- Internal libraries --
from bridge.generate_pdf.paper_crf import generate_paperlike_pdf


class TestGeneratePaperlikePdf:
    def test_generate_paperlike_crf_pdf__hantavirus_crf__arc_1_2_2__english(
        self, ccpuk_hantavirus_data_dictionary_2026
    ):
        data_dictionary = ccpuk_hantavirus_data_dictionary_2026
        received_pdf = generate_paperlike_pdf(
            data_dictionary, version="1.2.2", db_name="HANTA", language="English"
        )

        assert isinstance(received_pdf, bytes)
        assert sys.getsizeof(received_pdf) > 0
