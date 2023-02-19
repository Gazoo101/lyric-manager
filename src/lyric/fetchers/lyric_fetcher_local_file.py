# Python
from __future__ import annotations
import logging
from pathlib import Path
from typing import Tuple, TYPE_CHECKING

# 3rd Party


# 1st Party
from .lyric_fetcher_interface import LyricFetcherInterface
from ..dataclasses_and_types import LyricFetcherType
from ..dataclasses_and_types import LyricValidity


if TYPE_CHECKING:
    from ...audio_lyric_align_task import AudioLyricAlignTask

class LyricFetcherLocalFile(LyricFetcherInterface):
    """ Fetches local .txt files containing lyrics for a given song. """

    def __init__(self, path_to_working_dir:Path = None):
        super().__init__(LyricFetcherType.LocalFile, ".txt", path_to_working_dir)


    def fetch_lyrics(self, audio_lyric_align_task:AudioLyricAlignTask) -> Tuple[str, LyricValidity]:
        """ Returns a tuple consisting of lyrics in a string along with Validity of said lyrics.

        The lyric .txt file is expected to share the exact same filename as the song it matches, e.g.
        "Blur - Song 2.txt", would match "Blur - Song 2.<audio extension>".

        Two locations are searched for matching .txt files:
            - The same directory as the audio file.
            - LyricManager's working directory.

        NOTE: Since .txt files are provided manually by the user, LyricManager will assume Validity for all such files.
        """

        local_lyric_filename = audio_lyric_align_task.path_to_audio_file.with_suffix(self.file_extension).name

        path_to_local_copy_next_to_audio = audio_lyric_align_task.path_to_audio_file.parent / local_lyric_filename
        path_to_local_copy_in_working_dir = self.path_to_working_dir / local_lyric_filename

        path_to_lyric_txt_file = None
        if path_to_local_copy_next_to_audio.exists():
            path_to_lyric_txt_file = path_to_local_copy_next_to_audio

        if path_to_local_copy_in_working_dir.exists():
            path_to_lyric_txt_file = path_to_local_copy_in_working_dir


        if not path_to_lyric_txt_file:
            return "", LyricValidity.NotFound

        logging.info(f"Using local copy: {path_to_lyric_txt_file}")
        
        file_content = None

        with open(path_to_lyric_txt_file, 'r', encoding='utf8', errors='ignore') as file:
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