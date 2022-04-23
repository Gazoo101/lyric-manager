# Python
import logging
from pathlib import Path

# 3rd Party

# 1st Party
from .lyric_fetcher_interface import LyricFetcherInterface
from components import AudioLyricAlignTask

class LyricFetcherLocalFile(LyricFetcherInterface):

    def __init__(self, path_to_output_dir:Path = None):
        super().__init__(".txt", path_to_output_dir)

    def fetch_lyrics(self, audio_lyric_align_task:AudioLyricAlignTask):

        path_to_local_copy = audio_lyric_align_task.path_to_audio_file.with_suffix(self.file_extension)

        if path_to_local_copy.exists():
            logging.info(f"Using local copy: {path_to_local_copy}")
            
            #with open(path_to_local_copy, 'r') as file:
            #    file_contents = file.read()

            with open(path_to_local_copy, 'r', encoding='utf8', errors='ignore') as file2:
                file_other = file2.read()
            
            return file_other

        return ""