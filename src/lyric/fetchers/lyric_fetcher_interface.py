# Python
from __future__ import annotations # Why is this needed in Python 3.11?
import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Tuple, List, TYPE_CHECKING


# 3rd Party


# 1st Party
from ..dataclasses_and_types import LyricFetcherType
from ..dataclasses_and_types import LyricValidity
import src.lyric as lll

if TYPE_CHECKING:
    from ...audio_lyric_align_task import AudioLyricAlignTask
    
class LyricFetcherInterface(ABC):

    def __init__(self, type: LyricFetcherType, file_extension: str, path_to_working_dir: Path=None):
        self.type = type

        self.file_extension = file_extension
        self.file_extension_raw = f"{file_extension}_raw"
        self.file_extension_sanitized = f"{file_extension}_sanitized"

        self.path_to_working_dir = path_to_working_dir

        self.lyric_sanitizer = lll.LyricSanitizer()


    @abstractmethod
    def fetch_lyrics(self, audio_lyric_align_task:AudioLyricAlignTask) -> Tuple[str, LyricValidity]:
        """ Returns lyrics and (estimated) validity for a given AudioLyricAlignTask. """
        raise NotImplementedError
    

    def _fetch_lyrics_cached(self, audio_lyric_align_task:AudioLyricAlignTask):
        """ Retrieves a locally cached version for the given lyric fetcher type.
        
        Order of fetching:
            .ext_sanitized
        if not exitent:
            .ext_raw
        
        
        """
        path_to_cached_lyrics_raw = self.path_to_working_dir / audio_lyric_align_task.path_to_audio_file.name
        path_to_cached_lyrics_raw.with_suffix(self.file_extension_raw)
        path_to_cached_lyrics_sanitized = self.path_to_working_dir / audio_lyric_align_task.path_to_audio_file.name
        path_to_cached_lyrics_sanitized.with_suffix(self.file_extension_sanitized)

        # Sanitized lyrics are assumed to be valid
        if path_to_cached_lyrics_sanitized.exists():
            file_content_sanitized = self._read_file_utf8(path_to_cached_lyrics_sanitized)
            return file_content_sanitized, LyricValidity.Valid
        
        # Sanitized lyrics could not be found. Attempt to locate raw lyrics and validate if found.
        if path_to_cached_lyrics_raw.exists():
            file_content_raw = self._read_file_utf8(path_to_cached_lyrics_sanitized)

            # THIS NEEDS FURTHER FIXING / WORK
            lyric_validity = self._validate_lyrics(audio_lyric_align_task, file_content_raw)

            if lyric_validity == LyricValidity.Valid:
                self.sanitize_raw_lyrics(file_content_raw)

            # Write to disk and return the validated version?
            return dkasjdklasjdklas

        return None, LyricValidity.NotSet



        # # Detect locally cached raw copy of lyrics source
        # path_to_cached_raw_lyrics = audio_lyric_align_task.path_to_audio_file

        # if self.path_to_working_dir:
        #     path_to_cached_raw_lyrics = self.path_to_working_dir / audio_lyric_align_task.path_to_audio_file.name

        # path_to_cached_raw_lyrics = path_to_cached_raw_lyrics.with_suffix(self.file_extension_raw)

        # if path_to_cached_raw_lyrics.exists():
        #     logging.info(f"Detected local raw copy: {path_to_cached_raw_lyrics}")
            
        #     with open(path_to_cached_raw_lyrics, 'r', encoding='utf-8') as file:
        #         file_contents = file.read()

        #     lyric_validity = self._validate_lyrics(audio_lyric_align_task, file_contents)
            
        #     return file_contents, lyric_validity


    @abstractmethod
    def sanitize_raw_lyrics(self, audio_lyric_align_task:AudioLyricAlignTask) -> List[str]:
        """ Returns a sanitized list of lyric strings based on the raw lyrics likely fetched in the function above.
        
        The function accepts a AudioLyricAlignTask object (as opposed to a string) as some sanitization requires
        knowledge of a songs name, e.g., removing the very first line containing the song title.

        It's convenient from a code perspective to convert lyrics into a list of individual lyric lines here.
        """
        raise NotImplementedError
    

    #@abstractmethod
    def _validate_lyrics(self, audio_lyric_align_task: AudioLyricAlignTask, lyrics: str):
        """ Attempts to determine whether the lyrics found are legit or not. """

        # We default to always being invalid
        return LyricValidity.NotSet
    
    
    def _read_file_utf8(self, path_to_file: Path):
        with open(path_to_file, 'r', encoding='utf-8') as file:
                return file.read()