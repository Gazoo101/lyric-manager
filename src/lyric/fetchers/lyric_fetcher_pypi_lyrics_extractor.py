# Python
from __future__ import annotations
from pathlib import Path
from typing import TYPE_CHECKING, List, Tuple

# 3rd Party
from lyrics_extractor import SongLyrics

# 1st Party
from .lyric_fetcher_interface import LyricFetcherInterface
from ..dataclasses_and_types import LyricFetcherType
from ..dataclasses_and_types import LyricValidity

if TYPE_CHECKING:
    from ..dataclasses_and_types import AudioLyricAlignTask


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


    def _validate_lyrics(self, lyrics: str) -> LyricValidity:
        """ Returns a LyricValidity Enum indicating whether the given lyric content is valid or not.
        
        Each LyricFetcher is responsible for validating its own sourced lyrics, as each source will have its own set of
        rules by which it attempts to determine validity, e.g., local files are expected to be user provided and thus
        always considered valid. Online sources may provide garbage data unique to that particular source.
        """
        # For now we always consider the lyrics valid, but this is expected to change in the near future.
        return LyricValidity.Valid
    

    def _fetch_lyrics_raw(self, audio_lyric_align_task:AudioLyricAlignTask) -> Tuple[str, LyricValidity]:

        lyrics, validity = self._fetch_lyrics_cached(audio_lyric_align_task)

        # Do something about return early if valid otherwise re-fetch or something... Not sure yet.

        horse = 22

        # Can it handle artist *and* songname...?
        data = self.lyric_extractor.get_lyrics(audio_lyric_align_task.filename)

        path_to_cached_lyrics = self.path_to_working_dir / audio_lyric_align_task.path_to_audio_file.name
        path_to_cached_lyrics = path_to_cached_lyrics.with_suffix(self.file_extension_raw)

        # Possibly test if raw is decent here or not...

        # data["title"] is expected to contain the matching artist - song name - consider comparing likeness for these

        with open(path_to_cached_lyrics, 'w', encoding="utf-8") as file:
            file.write(data["lyrics"])      # If there are UTF-8 chars - non unicode, we're effed'



        hello = 2


    def _sanitize_lyrics_raw(self, lyrics_raw: List[str]) -> List[str]:
        """ Returns a sanitized list of lyric strings based on the raw lyrics likely fetched in the function above.
        
        The function accepts a AudioLyricAlignTask object (as opposed to a string) as some sanitization requires
        knowledge of a songs name, e.g., removing the very first line containing the song title.

        It's convenient from a code perspective to convert lyrics into a list of individual lyric lines here.
        """

        lyrics = lyrics_raw

        # Clears non-lyric content like [verse 1] and empty lines
        lyrics = self.lyric_sanitizer.remove_non_lyrics_v2(lyrics)
        # TODO: ALSO SPLITS string, this isn't clear and should be 'separated out' or unified somehow with the
        # local file handler/sanitizer.

        lyrics = self.lyric_sanitizer.replace_difficult_characters(lyrics)

        return lyrics