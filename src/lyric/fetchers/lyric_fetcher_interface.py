# Python
from __future__ import annotations # Why is this needed in Python 3.11?
import logging
from pathlib import Path
from dataclasses import dataclass
from abc import ABC, abstractmethod
from typing import Tuple, List, TYPE_CHECKING


# 3rd Party


# 1st Party
from ..dataclasses_and_types import LyricFetcherType
from ..dataclasses_and_types import LyricValidity
import src.lyric as lll

if TYPE_CHECKING:
    from ..dataclasses_and_types import AudioLyricAlignTask


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

@dataclass
class Lyrics():
    raw: str = ""
    sanitized: str = ""
    contains_multipliers: bool = ""
    validity: LyricValidity = LyricValidity.NotSet

    
class LyricFetcherInterface(ABC):
    """
    
    _raw - is unfiltered raw data from source
    _sanitized - is cleaned up and removal of useless non-lyric elements of lyric text.
    
    
    
    """

    def __init__(self, type: LyricFetcherType, file_extension: str, path_to_working_dir: Path=None):
        self.type = type

        self.file_extension = file_extension
        self.file_extension_raw = f"{file_extension}_raw"
        self.file_extension_sanitized = f"{file_extension}_sanitized"

        self.path_to_working_dir = path_to_working_dir

        self.lyric_sanitizer = lll.LyricSanitizer()


    # @abstractmethod
    # def _fetch_lyrics_raw(self, audio_lyric_align_task:AudioLyricAlignTask) -> Tuple[str, LyricValidity]:
    #     """ Returns lyrics and (estimated) validity for a given AudioLyricAlignTask. """
    #     raise NotImplementedError
    

    @abstractmethod
    def _sanitize_lyrics_raw(self, lyrics_raw: List[str]) -> List[str]:
        """ Returns a sanitized list of lyric strings based on the raw lyrics likely fetched in the function above.
        
        The function accepts a AudioLyricAlignTask object (as opposed to a string) as some sanitization requires
        knowledge of a songs name, e.g., removing the very first line containing the song title.

        It's convenient from a code perspective to convert lyrics into a list of individual lyric lines here.
        """
        raise NotImplementedError
    

    #@abstractmethod
    def _validate_lyrics(self, lyrics: str) -> LyricValidity:
        """ Returns a LyricValidity Enum indicating whether the given lyric content is valid or not.
        
        Each LyricFetcher is responsible for validating its own sourced lyrics, as each source will have its own set of
        rules by which it attempts to determine validity, e.g., local files are expected to be user provided and thus
        always considered valid. Online sources may provide garbage data unique to that particular source.
        """
        # By default we consider the lyrics to be invalid.
        return LyricValidity.NotSet
    

    def fetch_lyrics(self, audio_lyric_align_task:AudioLyricAlignTask) -> Lyrics:
        """ Returns the raw and sanitized lyrics, along with a guesstimation of the validity of the lyrics.

        For the vast majority of lyric sources, we'll want to retain local copies, except for the local copy itself...

        
        Order of fetching:
            .ext_sanitized
        if not exitent:
            .ext_raw
        
        
        """
        lyrics = Lyrics()

        path_to_cached_lyrics_raw = self.path_to_working_dir / audio_lyric_align_task.path_to_audio_file.name
        path_to_cached_lyrics_raw = path_to_cached_lyrics_raw.with_suffix(self.file_extension_raw)
        path_to_cached_lyrics_sanitized = self.path_to_working_dir / audio_lyric_align_task.path_to_audio_file.name
        path_to_cached_lyrics_sanitized = path_to_cached_lyrics_sanitized.with_suffix(self.file_extension_sanitized)

        # Sanitized lyrics are assumed to be valid
        if path_to_cached_lyrics_sanitized.exists():
            lyrics.sanitized = self._read_file_utf8(path_to_cached_lyrics_sanitized)
            lyrics.validity = LyricValidity.Valid

            # For debugging purposes, we still try to read and return the raw lyrics too
            if path_to_cached_lyrics_raw.exists():
                lyrics.raw = self._read_file_utf8(path_to_cached_lyrics_raw)

            return lyrics
        
        # Sanitized lyrics could not be found. Attempt to locate raw lyrics and validate if found.
        if path_to_cached_lyrics_raw.exists():
            lyrics.raw = self._read_file_utf8(path_to_cached_lyrics_raw)

            # THIS NEEDS FURTHER FIXING / WORK for the genius lyric grabbr
            lyrics.validity = self._validate_lyrics(lyrics.raw)

            if lyrics.validity == LyricValidity.Valid:

                # Sanitizer - for now - expects the lyrics to be in a list of strings...
                lyric_lines_raw = lyrics.raw.splitlines()

                lyric_lines_sanitized = self._sanitize_lyrics_raw(lyric_lines_raw)

                lyrics.sanitized = "/n".join(lyric_lines_sanitized)

                self._write_file_utf8(path_to_cached_lyrics_sanitized, lyrics.sanitized)

        return lyrics



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



    
    
    def _read_file_utf8(self, path_to_file: Path) -> str:
        with open(path_to_file, 'r', encoding='utf-8') as file:
            return file.read()


    def _write_file_utf8(self, path_to_file: Path, data: str):
        # Utf-8 required, as some lyrics sneak in awful non-ascii chars which break file-writing.
        with open(path_to_file, 'w', encoding="utf-8") as file:
            file.write(data)      # If there are UTF-8 chars - non unicode, we're effed'
        