# Python
from __future__ import annotations
import logging
from pathlib import Path
from typing import TYPE_CHECKING, List, Tuple, Any

# 3rd Party
from lyrics_extractor import SongLyrics, LyricScraperException

# 1st Party
from .lyric_fetcher_base import LyricFetcherBase
from ..dataclasses_and_types import LyricPayload
from ..dataclasses_and_types import LyricFetcherType
from ..dataclasses_and_types import LyricValidity

if TYPE_CHECKING:
    from ..dataclasses_and_types import LyricAlignTask


class LyricFetcherPyPiLyricsExtractor(LyricFetcherBase):
    """ Retrieves Lyrics from PyPi's lyrics_extractor package which relies on...

    Uses https://pypi.org/project/lyrics-extractor/
    
    """

    def __init__(self,
                 path_to_working_dir: Path,
                 google_custom_search_api_key: str,
                 google_custom_search_engine_id: str):
        super().__init__(LyricFetcherType.Pypi_LyricsExtractor, ".le", path_to_working_dir)

        self.lyric_extractor = SongLyrics(google_custom_search_api_key, google_custom_search_engine_id)

        # This fetcher relies on the 'Google Custom Search' API which has an easily exceeded quota. Once it's been
        # hit, there's no need badger the API.
        self.quota_exceeded = False

    def _get_lyric_text_raw_from_source(self, source: Any) -> str:
        """ Each fetcher will have a somewhat different source, so we must implement this - rewrite this code description. """
        return source["lyrics"]


    def _validate_lyrics(self, lyric_align_task:LyricAlignTask, raw_source: dict) -> LyricValidity:
        """ Returns a LyricValidity Enum indicating whether the given lyric content is valid or not.
        
        Each LyricFetcher is responsible for validating its own sourced lyrics, as each source will have its own set of
        rules by which it attempts to determine validity, e.g., local files are expected to be user provided and thus
        always considered valid. Online sources may provide garbage data unique to that particular source.
        """
        # For now we always consider the lyrics valid, but this is expected to change in the near future.

        # For debugging purposes we'll log the name of the filename and the returned title to try and help validate
        # things a bit.



        return LyricValidity.Valid
    
    def _fetch_lyrics_payload(self, lyric_align_task:LyricAlignTask) -> LyricPayload:

        lyrics = LyricPayload()

        if self.quota_exceeded:
            logging.warning("GCS quota exceeded in Pypi_LyricsExtractor - Not fetching lyrics.")
            # We intentionally return the Lyrics object with validity defaulting to NotSet, as we're prevented
            # from accessing the source due quota being exceeded.
            return lyrics
        
        # For this lyrics fetcher, we have a very low error tolerance so as to not exhaust any quotas.
        if self.fetch_history[lyric_align_task.filename].get_total_error_amount() >= 1:
            lyrics.validity = LyricValidity.Skipped_Due_To_Fetch_Errors
            logging.info(f"Skipping {lyric_align_task.filename} due to previous fetch errors.")
            return lyrics

        try:
            # Can it handle artist *and* songname...?
            data = self.lyric_extractor.get_lyrics(lyric_align_task.filename)
        except LyricScraperException as e:

            # To complicate matters, the lyrics_extractor package returns different objects depending on the type of
            # error it encounters, e.g:
            # - If the lyrics aren't found, the exception reference e contains:
            # (
            #   { "error": "No results found" } 
            # )
            # - If the search quota has been exhausted, the exception reference e contains:
            # (
            #   { "error": <dict containing further information> }
            # )
            exception_contents_at_error = e.args[0]['error']

            if exception_contents_at_error == "No results found":
                self.fetch_history[lyric_align_task.filename].not_found += 1
            else:
                if isinstance(exception_contents_at_error, dict):
                    if exception_contents_at_error['code'] == 429:
                        self.quota_exceeded = True
                        logging.warning("Quota exceeded error")
                        # We intentionally return the Lyrics object with validity defaulting to NotSet, as we're
                        # prevented from accessing the source due quota being exceeded.
                        return lyrics
                    else:

                        self.fetch_history[lyric_align_task.filename].unknown += 1
                        #logging.info("Unknown error encountered when fetching lyrics.")
                        logging.exception("Unknown error encountered when fetching lyrics.", e)

            self._save_fetch_history()

            # # Also raises quota exception which should then turn this one off?
            # # also institute checking for no lyrics found.
            # error_code = e.args[0]['error']['code']
            # error_message = e.args[0]['error']['message'] 

            

            # Not finding any results raises an Exception which is... strange. I wouldn't consider it particularly
            # exceptional behavior to not find lyrics for a given song. It's a heavy run-time penalty for what's
            # likely to be a fairly common occurrence. Unfortunately, without modifying the lyrics_extractor package
            # we're stuck catching it and returning invalid lyrics in case of failure.
            lyrics.validity = LyricValidity.NotFound
            return lyrics

        lyrics.source = data
        lyrics.validity = self._validate_lyrics(lyric_align_task, data)

        return lyrics

        # path_to_cached_lyrics = self.path_to_working_dir / lyric_align_task.path_to_audio_file.name
        # path_to_cached_lyrics = path_to_cached_lyrics.with_suffix(self.file_extension_raw)

        # # Possibly test if raw is decent here or not...

        # # data["title"] is expected to contain the matching artist - song name - consider comparing likeness for these

        # with open(path_to_cached_lyrics, 'w', encoding="utf-8") as file:
        #     file.write(data["lyrics"])      # If there are UTF-8 chars - non unicode, we're effed'



        # hello = 2


    def _sanitize_lyrics_raw(self, lyric_align_task:LyricAlignTask, raw_source:dict) -> str:
        """ Returns a sanitized list of lyric strings based on the raw lyrics likely fetched in the function above.
        
        The function accepts a AudioLyricAlignTask object (as opposed to a string) as some sanitization requires
        knowledge of a songs name, e.g., removing the very first line containing the song title.

        It's convenient from a code perspective to convert lyrics into a list of individual lyric lines here.
        """

        lyrics = self._get_lyric_text_raw_from_source(raw_source)

        lyrics = lyrics.splitlines()

        # Clears non-lyric content like [verse 1] and empty lines
        lyrics = self.lyric_sanitizer.remove_non_lyrics(lyrics)
        # TODO: ALSO SPLITS string, this isn't clear and should be 'separated out' or unified somehow with the
        # local file handler/sanitizer.

        lyrics = self.lyric_sanitizer.replace_difficult_characters(lyrics)

        lyrics = '/n'.join(lyrics)

        return lyrics