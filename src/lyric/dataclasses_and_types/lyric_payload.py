# Python
from dataclasses import dataclass
from typing import Any

# 3rd Party


# 1st Party
from .lyric_validity import LyricValidity


@dataclass
class LyricPayload():
    """ Represents Lyrics data generated and passed around in lyric fetchers

    Intentionally kept separate from the LyricAlignTask.

    Names such because just 'Lyrics' is far too generic.

    """

    # source represents the rawest output from a given LyricFetcher. In some cases - such as LyricFetcherLocalFile -
    # it's just raw text. In other cases it's a dict, or even an object.
    #
    # Storing it serves two purposes:
    # - It eases development by allowing us to simulate what remotely fetching data looks like without having to
    #   actually fetch it.
    # - When the data is simple enough, an on-disk version is easily read and can aid in post-error debugging.
    source: Any = None
    text_raw: str = ""
    text_sanitized: str = ""

    # Multipliers refers to LyricManager specific annotations to ease lyric notation
    contains_multipliers: bool = ""
    validity: LyricValidity = LyricValidity.NotSet