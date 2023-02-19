# Python
from __future__ import annotations
from pathlib import Path
from typing import TYPE_CHECKING, List

# 3rd Party

# 1st Party
from .lyric_fetcher_interface import LyricFetcherInterface
from ..dataclasses_and_types import LyricFetcherType

if TYPE_CHECKING:
    from audio_lyric_align_task import AudioLyricAlignTask


class LyricFetcherWebsiteLyricsDotOvh(LyricFetcherInterface):
    """ Retrieves Lyrics from Lyrics.ovh via it's API, perhaps using Curl...?
    
    Note: This class is not yet implemented. It may never be, as it appears Lyrics.ovh depends on LyricMania which
    has possibly banned Lyrics.ovh from accessing its data:

    https://github.com/NTag/lyrics.ovh/issues/15
    """

    def __init__(self, file_extension: str, path_to_working_dir: Path=None):
        super().__init__(LyricFetcherType.Website_LyricsDotOvh, ".ovh", path_to_working_dir)


    def fetch_lyrics(self, audio_lyric_align_task:AudioLyricAlignTask):
        raise NotImplementedError
    
    def sanitize_raw_lyrics(self, audio_lyric_align_task:AudioLyricAlignTask) -> List[str]:
        """ Returns a sanitized list of lyric strings based on the raw lyrics likely fetched in the function above. """
        raise NotImplementedError
