# Python
from __future__ import annotations
from pathlib import Path
from typing import TYPE_CHECKING

# 3rd Party
import lyrics_extractor

# 1st Party
from .lyric_fetcher_interface import LyricFetcherInterface
from .lyric_fetcher_type import LyricFetcherType

if TYPE_CHECKING:
    from audio_lyric_align_task import AudioLyricAlignTask


class LyricFetcherPyPiLyricsExtractor(LyricFetcherInterface):
    """ Retrieves Lyrics from PyPi's lyrics_extractor package which relies on...
    
    """

    def __init__(self, file_extension: str, path_to_working_dir: Path=None):
        super().__init__(LyricFetcherType.Website_LyricsDotOvh, ".ovh", path_to_working_dir)


    @abstractmethod
    def fetch_lyrics(self, audio_lyric_align_task:AudioLyricAlignTask):
        raise NotImplementedError
