# Python
from __future__ import annotations # Why is this needed in Python 3.11?
import json
import jsons as jsonserializer
import logging
from pathlib import Path
from dataclasses import dataclass
from abc import ABC, abstractmethod
from collections import defaultdict
from typing import TYPE_CHECKING, Any, DefaultDict



# 3rd Party
import jsonpickle

# 1st Party
from ...components.file_operations import FileOperations
from ..dataclasses_and_types import LyricFetcherType
from ..dataclasses_and_types import LyricValidity
from ..dataclasses_and_types import LyricPayload
import src.lyric as lll

if TYPE_CHECKING:
    from ..dataclasses_and_types import LyricAlignTask


""" Lyric Annotations:

This section is a work-in-progress and needs to be more fleshed out in the future re. how differing sources of lyrics
use various types of annotation to inform how we handle things in code.

- Brackets are commonly used in multiple sources to denote lyric sections, e.g., "[Intro]", "[Verse 1]", "[Chorus]" or
  titles and artists, e.g., "[Produced by Dr. Dre & Mike Elizondo]".
- Squiggly brackets are LyricManager's supported annotations to simplify Lyric management, e.g.,
  "{Safe in the eyes of the morning|3}" or
  "{Keeping on, keeping on track
   Keeping on track
   Keeping on, keeping on track|2}"


"""

# FetchErrors is a @dataclass so we can construct defaultdict(FetchErrors) which can be serialized using jsons.
# defaultdict(defaultdict(Enum)) cannot be serialized in using jsons.
@dataclass
class FetchErrors():
    time_out : int = 0
    not_found : int = 0
    unknown : int = 0

    def get_total_error_amount(self):
        return self.time_out + self.not_found + self.unknown

    
class LyricFetcherBase(ABC):
    """ Base-class for LyricFetchers implementing shared functionality.

    Most lyric fetchers operate with remote sources, and this class provides the following shared functionality for
    these:
    - Cache files locally
    - Record lyric fetch history, to prevent spending time attempting to fetch lyrics for a song that's already proven
      not to exist at a particular source.

    Two cached files will typically be created:
    - Artist - Songname.{file_extension}_source             - The raw returned result from the given source.
    - Artist - Songname.{file_extension}_sanitized_text     - Sanitized source lyric text
    """

    def __init__(self, type: LyricFetcherType, file_extension: str, path_to_working_dir: Path=None):
        self.type = type

        self.file_extension = file_extension

        # The locally cached files are deliberately given unique file-extensions so users can use the OS file-explorer
        # to easily purge cached files from only a particular source, by sorting by file-extension
        self.file_extension_source = f"{file_extension}_source"
        self.file_extension_txt_sanitized = f"{file_extension}_sanitized_text"

        self.path_to_working_dir = path_to_working_dir

        self.lyric_sanitizer = lll.LyricSanitizer()

        self.path_to_fetch_history = path_to_working_dir / f"fetch_history{file_extension}"
        self.fetch_history = self._init_fetch_history()


    def _init_fetch_history(self):
        fetch_history = defaultdict(FetchErrors)

        if self.path_to_fetch_history.exists():
            file_content = self.path_to_fetch_history.read_text()
            fetch_history = jsonserializer.loads(file_content, DefaultDict[str, FetchErrors])

        return fetch_history


    def _save_fetch_history(self):
        fetch_history_serialized = jsonserializer.dumps(self.fetch_history)
        self.path_to_fetch_history.write_text(fetch_history_serialized)


    @abstractmethod
    def _sanitize_lyrics_raw(self, lyric_align_task:LyricAlignTask, raw_source: Any) -> str:
        """ Returns a sanitized list of lyric strings based on the raw lyrics likely fetched in the function above.
        
        The function accepts a LyricAlignTask object and LyricFetcher specific source, as some sanitization requires
        knowledge of a songs name, e.g., removing the very first line containing the song title.

        The raw source is provided because in some cases, like lyricgenius, some of the data that must be sanitized
        will be present in the original raw source.

        It should return a single sanitized string.
        """
        raise NotImplementedError()
    

    def _validate_lyrics(self, lyric_align_task:LyricAlignTask, raw_source: Any) -> LyricValidity:
        """ Returns a LyricValidity Enum indicating whether the given lyric content is valid or not.
        
        Each LyricFetcher is responsible for validating its own sourced lyrics, as each source will have its own set of
        rules by which it attempts to determine validity, e.g., local files are expected to be user provided and thus
        always considered valid. Online sources may provide garbage data unique to that particular source.

        Args:
            raw_source: Either a string or dict depending on the fetcher in question.
        """
        # By default we consider the lyrics to be invalid.
        return LyricValidity.NotSet
    

    def _load_json_from_disk(self, path_to_json_file: Path) -> Any:
        return jsonpickle.decode(path_to_json_file.read_text())


    def _save_json_to_disk(self, path_to_json_file: Path, data: Any):
        json_text = jsonpickle.encode(data)
        path_to_json_file.write_text(json_text)        


    @abstractmethod
    def _get_lyric_text_raw_from_source(self, source: Any):
        """ Returns raw text lyric given the source data from the same LyricFetcher.
        
        To encapsulate 'source handling' within each respective LyricFetcher, it must override this function.

        Source data varies from PyPi package-specific object, to a dict, to just plain text.
        """
        raise NotImplementedError()
    

    def fetch_lyrics(self, lyric_align_task:LyricAlignTask) -> LyricPayload:
        """ Returns a LyricPayload object containing various lyric data for the audio-file in question.

        Most LyricFetches access remote data, and a previously cached local copy is preferred to a live copy. Given that
        the data is remote its validity cannot be guaranteed, and a validity estimate is provided in the LyricPayload
        object.

        This function relies on self._fetch_lyrics_payload() to provide the LyricFetcher-unique 
        
        The logic generally works as follows:
            - If a local sanitized cached copy (.{file_extension}_sanitized_text) exists, assume it's valid and return.
            - If a local raw cached copy (.{file_extension}_source) exists, attempt to sanitize and validate and return.
            - Fetch remote copy, cache locally, validate, sanitze, and return.
        """
        lyrics = LyricPayload()

        logging.debug(f"Fetching lyrics for: {lyric_align_task.path_to_audio_file.name}")

        path_to_cached_source = self.path_to_working_dir / lyric_align_task.path_to_audio_file.name
        path_to_cached_source = path_to_cached_source.with_suffix(self.file_extension_source)
        path_to_cached_lyrics_sanitized = self.path_to_working_dir / lyric_align_task.path_to_audio_file.name
        path_to_cached_lyrics_sanitized = path_to_cached_lyrics_sanitized.with_suffix(self.file_extension_txt_sanitized)

        # 1. First try to locate locally cached sanitized lyrics
        if path_to_cached_lyrics_sanitized.exists():
            logging.debug(f"Local cached Sanitized text detected!")
            lyrics.text_sanitized = self._read_file_utf8(path_to_cached_lyrics_sanitized)

            # Sanitized lyrics are assumed to always be valid.
            lyrics.validity = LyricValidity.Valid

            # For debugging purposes, we still try to read and return the raw lyrics too
            if path_to_cached_source.exists():
                lyrics.source = self._load_json_from_disk(path_to_cached_source)
                lyrics.text_raw = self._get_lyric_text_raw_from_source(lyrics.source)

            return lyrics
        
        # 2. If locally cached sanitized lyrics aren't available, try to locate locally cached raw source lyrics
        if path_to_cached_source.exists():
            logging.debug(f"Locally cached raw source detected!")
            lyrics.source = self._load_json_from_disk(path_to_cached_source)
            
            # Locally loaded lyrics require re-validating
            lyrics.validity = self._validate_lyrics(lyric_align_task, lyrics.source)
        else:
            # 3. If neither a locally cached sanitized or locally cached raw source is available, do we fetch a fresh
            # copy.
            lyrics = self._fetch_lyrics_payload(lyric_align_task)

            # Only if the source is completely empty do we skip caching it, otherwise we'd like to retain a local cached
            # copy in order to improve validation code, etc.
            if lyrics.source is None:
                return lyrics

            # Regardless of validity, we save the source, unless not-set
            self._save_json_to_disk(path_to_cached_source, lyrics.source)

        if lyrics.validity is not LyricValidity.Valid:
            return lyrics
    
        # The transition from Lyrics object into AudioLyricAlignTest is a little... Iffy...
        lyrics.text_raw = self._get_lyric_text_raw_from_source(lyrics.source)

        lyrics.text_sanitized = self._sanitize_lyrics_raw(lyric_align_task, lyrics.source)

        self._write_file_utf8(path_to_cached_lyrics_sanitized, lyrics.text_sanitized)

        return lyrics


    @abstractmethod
    def _fetch_lyrics_payload(self, lyric_align_task:LyricAlignTask) -> LyricPayload:
        """ Returns lyrics and (estimated) validity for a given LyricAlignTask. """
        raise NotImplementedError()

    
    
    def _read_file_utf8(self, path_to_file: Path) -> str:
        return FileOperations.read_utf8_string(path_to_file)

    def _write_file_utf8(self, path_to_file: Path, data: str):
        FileOperations.write_utf8_string(path_to_file, data)

        