# Python
from abc import ABC, abstractmethod
from pathlib import Path
from components import AudioLyricAlignTask
from typing import Tuple, List

# 3rd Party


# 1st Party
from components import LyricValidity
from components import LyricSanitizer
from .lyric_fetcher_type import LyricFetcherType

class LyricFetcherInterface(ABC):

    def __init__(self, type: LyricFetcherType, file_extension: str, path_to_output_dir: Path=None):
        self.type = type
        self.file_extension = file_extension
        self.path_to_output_dir = path_to_output_dir

        self.lyric_sanitizer = LyricSanitizer()


    @abstractmethod
    def fetch_lyrics(self, audio_lyric_align_task:AudioLyricAlignTask) -> Tuple[str, LyricValidity]:
        """ Returns lyrics and (estimated) validity for a given AudioLyricAlignTask. """
        raise NotImplementedError


    @abstractmethod
    def sanitize_raw_lyrics(self, audio_lyric_align_task:AudioLyricAlignTask) -> List[str]:
        """ Returns a sanitized list of lyric strings based on the raw lyrics likely fetched in the function above.
        
        The function accepts a AudioLyricAlignTask object (as opposed to a string) as some sanitization requires
        knowledge of a songs name, e.g., removing the very first line containing the song title.

        It's convenient from a code perspective to convert lyrics into a list of individual lyric lines here.
        """
        raise NotImplementedError