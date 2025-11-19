from functools import partial
from io import BytesIO
from os.path import join, dirname, abspath

import numpy as np
import pandas as pd
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.pdfmetrics import registerFontFamily
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate

from bridge.arc.arc_core import ArcApiClient
from bridge.generate_pdf.form import generate_form
from bridge.generate_pdf.guide import generate_guide_doc
from bridge.generate_pdf.header_footer import generate_paperlike_header_footer
from bridge.generate_pdf.opener import generate_opener
from bridge.logging.logger import setup_logger

logger = setup_logger(__name__)

REGISTERED_FONT = 'DejaVuSans'
REGISTERED_FONT_BOLD = 'DejaVuSans-Bold'

ASSETS_DIR_FULL = join(dirname(dirname(dirname(abspath(__file__)))), 'assets')
FONTS_DIR_FULL = join(ASSETS_DIR_FULL, 'fonts')

pdfmetrics.registerFont(TTFont(REGISTERED_FONT, join(FONTS_DIR_FULL, f'{REGISTERED_FONT}.ttf')))
pdfmetrics.registerFont(TTFont(REGISTERED_FONT_BOLD, join(FONTS_DIR_FULL, f'{REGISTERED_FONT_BOLD}.ttf')))

registerFontFamily(
    REGISTERED_FONT,
    normal=REGISTERED_FONT,
    bold=REGISTERED_FONT_BOLD
)


def generate_paperlike_pdf(df_datadicc: pd.DataFrame,
                           version: str,
                           db_name: str,
                           language: str) -> bytes:
    buffer = BytesIO()
    df_datadicc = df_datadicc[~df_datadicc['Field Label'].str.startswith(('>', '->'))]

    details = ArcApiClient().get_dataframe_paper_like_details(version, language)
    supplemental_phrases = ArcApiClient().get_dataframe_supplemental_phrases(version, language)

    # Locate the phrase in the supplemental phrases DataFrame
    def locate_phrase(variable: str) -> dict:
        try:
            phrase = supplemental_phrases.loc[supplemental_phrases['variable'] == variable, 'text'].values[0]
            return {"error": False, "text": phrase}
        except IndexError:
            logger.warning(f"Variable '{variable}' not found in supplemental phrases.")
            return {"error": True, "text": ""}

    left_margin = 0.3 * inch
    right_margin = 0.3 * inch
    top_margin = 0.7 * inch
    bottom_margin = 0.7 * inch

    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        leftMargin=left_margin,
        rightMargin=right_margin,
        topMargin=top_margin,
        bottomMargin=bottom_margin
    )

    element_list = []
    element_list = generate_opener(element_list, details, db_name)
    df_datadicc['Section Header'] = df_datadicc['Section Header'].replace({'': np.nan})
    element_list = generate_form(df_datadicc, element_list, locate_phrase)
    header_footer_partial = partial(generate_paperlike_header_footer, title=db_name)

    try:
        doc.build(element_list, onFirstPage=header_footer_partial, onLaterPages=header_footer_partial)
    except ValueError as e:
        logger.error(e)
        raise RuntimeError("Failed to build Paperlike PDF")

    buffer.seek(0)
    return buffer.getvalue()


def generate_completion_guide(df_datadicc: pd.DataFrame,
                              version: str,
                              db_name: str) -> bytes:
    df_datadicc = df_datadicc.copy()
    buffer = BytesIO()
    generate_guide_doc(df_datadicc, version, db_name, buffer)
    buffer.seek(0)
    return buffer.getvalue()
