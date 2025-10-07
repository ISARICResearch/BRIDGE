from bridge.logging.logger import setup_logger

logger = setup_logger(__name__)


def get_crf_name(crf_name, checked_values):
    if crf_name is not None:
        if isinstance(crf_name, list):
            crf_name = crf_name[0]
    else:
        extracted_text = [item for sublist in checked_values for item in sublist if item]
        if len(extracted_text) > 0:
            crf_name = extracted_text[0]
    if not crf_name:
        crf_name = 'no_name'
    logger.info(f'crf_name: {crf_name}')
    return crf_name
