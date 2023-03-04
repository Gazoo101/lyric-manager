# Python
from __future__ import annotations
from pathlib import Path
from typing import TYPE_CHECKING, List, Tuple

# 3rd Party

# 1st Party
from .lyric_fetcher_base import LyricFetcherBase
from ..dataclasses_and_types import LyricFetcherType

if TYPE_CHECKING:
    from ..dataclasses_and_types import LyricAlignTask
    from ..dataclasses_and_types import LyricValidity


class LyricFetcherWebsiteLyricsDotOvh(LyricFetcherBase):
    """ Retrieves Lyrics from Lyrics.ovh via it's API, perhaps using Curl...?
    
    Note: This class is not yet implemented. It may never be, as it appears Lyrics.ovh depends on LyricMania which
    has possibly banned Lyrics.ovh from accessing its data:

    https://github.com/NTag/lyrics.ovh/issues/15
    """

    def __init__(self, path_to_working_dir: Path=None):
        super().__init__(LyricFetcherType.Website_LyricsDotOvh, ".ovh", path_to_working_dir)


    def _fetch_lyrics_payload(self, lyric_align_task:LyricAlignTask) -> Tuple[str, LyricValidity]:
        raise NotImplementedError
    
    def _sanitize_lyrics_raw(self, lyric_align_task:LyricAlignTask) -> List[str]:
        """ Returns a sanitized list of lyric strings based on the raw lyrics likely fetched in the function above. """
        raise NotImplementedError
