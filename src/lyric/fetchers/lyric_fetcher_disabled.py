# Python
from typing import List
from pathlib import Path

# 3rd Party

# 1st Party
from .lyric_fetcher_base import LyricFetcherBase
from ..dataclasses_and_types import LyricPayload

from ..dataclasses_and_types import LyricFetcherType


class LyricFetcherDisabled(LyricFetcherBase):
    """ A dummy 'disabled' class to allow for skipping Lyric fetching.
    
    Not sure this actually has any real use anymore. Consider deprecating.
    
    """

    def __init__(self, path_to_working_dir:Path = None):
        """ Creates the Dummy class for skipping lyric fetching.
        
        It mimics the LyricFetcherInterface design so the calling code can be kept simple.
        """
        super().__init__(LyricFetcherType.Disabled, ".na", path_to_working_dir)

    def _sanitize_lyrics_raw(self, lyrics_raw: List[str]) -> List[str]:
        return []

    def _fetch_lyrics_payload(self, lyric_align_task) -> LyricPayload:
        return LyricPayload()
    
    def _get_lyric_text_raw_from_source(self, source):
        return ""