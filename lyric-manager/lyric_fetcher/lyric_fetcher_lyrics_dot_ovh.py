from abc import ABC, abstractmethod
from pathlib import Path
from components import AudioLyricAlignTask

from lyric_fetcher_type import LyricFetcherType

class LyricFetcherLyricsDotOvh(ABC):
    """ Retrieves Lyrics from Lyrics.ovh via <to-be-decided>.
    
    Note: This class is not yet implemented.
    
    """

    def __init__(self, file_extension: str, path_to_output_dir: Path=None):
        super().__init__(LyricFetcherType.LyricsDotOvh, ".ovh", path_to_output_dir)

        self.file_extension = file_extension
        self.path_to_output_dir = path_to_output_dir

    @abstractmethod
    def fetch_lyrics(self, audio_lyric_align_task:AudioLyricAlignTask):
        raise NotImplementedError
