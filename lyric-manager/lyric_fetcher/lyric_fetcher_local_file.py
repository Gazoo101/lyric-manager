import logging
from pathlib import Path
from typing import Tuple

# 3rd Party


# 1st Party
from .lyric_fetcher_interface import LyricFetcherInterface
from .lyric_fetcher_type import LyricFetcherType
from components import AudioLyricAlignTask
from components import LyricValidity

class LyricFetcherLocalFile(LyricFetcherInterface):

    def __init__(self, path_to_output_dir:Path = None):
        super().__init__(LyricFetcherType.LocalFile, ".txt", path_to_output_dir)


    def fetch_lyrics(self, audio_lyric_align_task:AudioLyricAlignTask) -> Tuple[str, LyricValidity]:

        local_lyric_filename = audio_lyric_align_task.path_to_audio_file.with_suffix(self.file_extension).name

        path_to_local_copy_next_to_audio = audio_lyric_align_task.path_to_audio_file.parent / local_lyric_filename
        path_to_local_copy_in_output = self.path_to_output_dir / local_lyric_filename

        path_to_local_copy = None
        if path_to_local_copy_next_to_audio.exists():
            path_to_local_copy = path_to_local_copy_next_to_audio

        if path_to_local_copy_in_output.exists():
            path_to_local_copy = path_to_local_copy_in_output


        if not path_to_local_copy:
            return "", LyricValidity.NotFound

        logging.info(f"Using local copy: {path_to_local_copy}")
        
        file_content = None

        with open(path_to_local_copy, 'r', encoding='utf8', errors='ignore') as file:
            file_content = file.read()
        
        # Currently, we *always* assume that local lyric files are valid.
        return file_content, LyricValidity.Valid


    """ See LyricFetcherInterface.sanitize_raw_lyrics() for description. """
    def sanitize_raw_lyrics(self, audio_lyric_align_task:AudioLyricAlignTask) -> str:
        lyrics = audio_lyric_align_task.lyric_text_raw

        # We remove []'s and their contents inside
        lyrics_list = self.lyric_sanitizer.remove_non_lyrics(lyrics)

        lyrics = "\n".join(lyrics_list)

        lyrics = lyrics.replace('[', '').replace(']', '')
        lyrics = lyrics.replace('-', '')

        all_lyric_lines = lyrics.splitlines()

        # Removes empty lines
        non_empty_lyric_lines = [lyric_line for lyric_line in all_lyric_lines if lyric_line]

        return non_empty_lyric_lines