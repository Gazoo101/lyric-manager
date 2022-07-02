import logging
from pathlib import Path
from typing import Tuple

# 3rd Party


# 1st Party
from .lyric_fetcher_interface import LyricFetcherInterface
from components import AudioLyricAlignTask
from components import LyricValidity

class LyricFetcherLocalFile(LyricFetcherInterface):

    def __init__(self, path_to_output_dir:Path = None):
        super().__init__(".txt", path_to_output_dir)


    def fetch_lyrics(self, audio_lyric_align_task:AudioLyricAlignTask) -> Tuple[str, LyricValidity]:

        path_to_local_copy = audio_lyric_align_task.path_to_audio_file.with_suffix(self.file_extension)

        if path_to_local_copy.exists():
            logging.info(f"Using local copy: {path_to_local_copy}")
            
            file_content = None

            with open(path_to_local_copy, 'r', encoding='utf8', errors='ignore') as file:
                file_content = file.read()
            
            # Currently, we *always* assume that local lyric files are valid.
            return file_content, LyricValidity.Valid

        return "", LyricValidity.NotFound

    """ See LyricFetcherInterface.sanitize_raw_lyrics() for description. """
    def sanitize_raw_lyrics(self, audio_lyric_align_task:AudioLyricAlignTask) -> str:
        lyrics = audio_lyric_align_task.lyric_text_raw

        lyrics = lyrics.replace('[', '').replace(']', '')
        lyrics = lyrics.replace('-', '')

        all_lyric_lines = lyrics.splitlines()

        # Removes empty lines
        non_empty_lyric_lines = [lyric_line for lyric_line in all_lyric_lines if lyric_line]

        return non_empty_lyric_lines