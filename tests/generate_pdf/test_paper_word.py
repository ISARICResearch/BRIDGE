# -- IMPORTS --

# -- Standard libraries --
import sys

# -- 3rd party libraries --

# -- Internal libraries --
from bridge.generate_pdf.paper_word import df_to_word


class TestGeneratePaperlikeWord:
    def test_generate_paperlike_crf_word__hantavirus_crf(
        self, ccpuk_hantavirus_data_dictionary_2026
    ):
        data_dictionary = ccpuk_hantavirus_data_dictionary_2026
        received_word = df_to_word(data_dictionary)

        assert isinstance(received_word, bytes)
        assert sys.getsizeof(received_word) > 0
