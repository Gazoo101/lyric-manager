# Python
from __future__ import annotations
from pathlib import Path
from typing import TYPE_CHECKING, List

# 3rd Party
from lyrics_extractor import SongLyrics

# 1st Party
from .lyric_fetcher_interface import LyricFetcherInterface
from ..dataclasses_and_types import LyricFetcherType

if TYPE_CHECKING:
    from audio_lyric_align_task import AudioLyricAlignTask


class LyricFetcherPyPiLyricsExtractor(LyricFetcherInterface):
    """ Retrieves Lyrics from PyPi's lyrics_extractor package which relies on...

    Uses https://pypi.org/project/lyrics-extractor/
    
    """

    def __init__(self,
                 path_to_working_dir: Path,
                 google_custom_search_api_key: str,
                 google_custom_search_engine_id: str):
        super().__init__(LyricFetcherType.Pypi_LyricsExtractor, ".le", path_to_working_dir)

        self.lyric_extractor = SongLyrics(google_custom_search_api_key, google_custom_search_engine_id)


    def fetch_lyrics(self, audio_lyric_align_task:AudioLyricAlignTask):

        gettems = self._fetch_lyrics_cached(audio_lyric_align_task)

        # Can it handle artist *and* songname...?
        data = self.lyric_extractor.get_lyrics(audio_lyric_align_task.filename)

        hello = 2


    def sanitize_raw_lyrics(self, audio_lyric_align_task:AudioLyricAlignTask) -> List[str]:
        """ Returns a sanitized list of lyric strings based on the raw lyrics likely fetched in the function above.
        
        The function accepts a AudioLyricAlignTask object (as opposed to a string) as some sanitization requires
        knowledge of a songs name, e.g., removing the very first line containing the song title.

        It's convenient from a code perspective to convert lyrics into a list of individual lyric lines here.
        """
        raise NotImplementedError