from __future__ import annotations

__all__ = [
    "clean_dataframe",
    "generate_hyperlink_tags",
    "strip_html",
    "strip_nonstandard_unicode_chars",
]

# -- IMPORTS --

# -- Standard libraries --
import re
import typing

# -- 3rd party libraries --
import pandas

# -- Internal libraries --


def strip_html(value: typing.Any) -> str | typing.Any:
    """:py:class:`typing.Any` : Strip HTML elements from a value.

    Parameters
    ----------
    value : typing.Any
        A value.

    Returns
    -------
    str, typing.Any
        Either a string stripped of all HTML elements, or the original non-
        string value.
    """
    if isinstance(value, str):
        return re.sub(r"<.*?>", "", value)

    return value


def strip_nonstandard_unicode_chars(value: typing.Any) -> str | typing.Any:
    """:py:class:`typing.Any` : Strip non-standard Unicode characters from a value.

    The non-standard Unicode characters of interest are defined within the
    function itself, and are currently limited to the "↳" (U+21B3) character,
    but may be extended to include other characters.

    Parameters
    ----------
    value : typing.Any
        A value.

    Returns
    -------
    str, typing.Any
        Either a string stripped of all non-standard Unicode characters, or the
        original non- string value.
    """
    nonstandard_unicode_chars = "↳"

    if isinstance(value, str):
        return re.sub(rf"[{nonstandard_unicode_chars}]", "", value)

    return value


def clean_dataframe(dataframe: pandas.DataFrame) -> pandas.DataFrame:
    """:py:class:`pandas.DataFrame` : A cleaned dataframe.

    The cleaning steps are the removal of HTML characters and of non-standard,
    i.e. non-textual, Unicode characters.

    Parameters
    ----------
    dataframe : pandas.DataFrame
        The original figure table as a Pandas dataframe.

    Returns
    -------
    pandas.DataFrame
        The cleaned dataframe.
    """
    # The use of `pandas.DataFrame.map` here is not absolutely optimal, as
    # `map` applies changes across the dataframe element-wise, but is the
    # safer choice given that the dataframe may contain a number of non-string
    # columns which cannot be known in advance, while the cleaning steps
    # currently only apply to string values.
    return dataframe.map(strip_html).map(strip_nonstandard_unicode_chars)


def generate_hyperlink_tags(
    comma_separated_urls: str, new_page_target: bool = True
) -> typing.Generator[str, None, None]:
    """:py:class:`typing.Generator` : A sequence of HTML hyperlink tags with new page targets.

    Parameters
    ----------
    comma_separated_urls : str
        A comma-separated string of URLs.

    new_page_target : bool, default=True
        Optionally set the tags to open in a new page, defaults to ``True``.

    Yields
    ------
    str
        HTML hyperlink
    """
    target_attrib = 'target="_blank"' if new_page_target else ""
    for url in map(str.strip, comma_separated_urls.split(",")):
        yield f'<a href="{url}" {target_attrib}>{url}</a>'
