from abc import ABC, abstractmethod
from pathlib import Path
from components import AudioLyricAlignTask

class LyricFetcherLyricsDotOvh(ABC):
    """ Retrieves Lyrics from Lyrics.ovh via <to-be-decided>. """

    def __init__(self, file_extension: str, path_to_output_dir: Path=None):
        self.file_extension = file_extension
        self.path_to_output_dir = path_to_output_dir

    @abstractmethod
    def fetch_lyrics(self, audio_lyric_align_task:AudioLyricAlignTask):
        raise NotImplementedError
