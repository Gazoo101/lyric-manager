# Python
from __future__ import annotations
import logging
from pathlib import Path
from typing import Tuple, List, TYPE_CHECKING

# 3rd Party


# 1st Party
from .lyric_fetcher_interface import LyricFetcherInterface
from .lyric_fetcher_interface import Lyrics

from ..dataclasses_and_types import LyricFetcherType
from ..dataclasses_and_types import LyricValidity



if TYPE_CHECKING:
    from ..dataclasses_and_types import AudioLyricAlignTask

class LyricFetcherLocalFile(LyricFetcherInterface):
    """ Fetches local .txt files containing lyrics for a given song. """

    def __init__(self, path_to_working_dir:Path = None):
        super().__init__(LyricFetcherType.LocalFile, ".txt", path_to_working_dir)

    
    def _validate_lyrics(self, audio_lyric_align_task: AudioLyricAlignTask, lyrics: str):
        """ Returns a LyricValidity Enum indicating whether the given lyric content is valid or not.
        
        Each LyricFetcher is responsible for validating its own sourced lyrics, as each source will have its own set of
        rules by which it attempts to determine validity, e.g., local files are expected to be user provided and thus
        always considered valid. Online sources may provide garbage data unique to that particular source.
        """
        return LyricValidity.Valid
    

    def fetch_lyrics(self, audio_lyric_align_task:AudioLyricAlignTask) -> Lyrics:
        """ Returns the raw and sanitized lyrics, along with a guesstimation of the validity of the lyrics.

        Local file lyrics are not subject to additional caching, so we override this function directly to disable the
        caching behavior.        
        """
        lyrics = Lyrics()

        path_to_local_copy_in_working_dir = self.path_to_working_dir / audio_lyric_align_task.path_to_audio_file.name
        path_to_local_copy_in_working_dir = path_to_local_copy_in_working_dir.with_suffix(self.file_extension)

        path_to_local_copy_next_to_audio = audio_lyric_align_task.path_to_audio_file.with_suffix(self.file_extension)

        # Local files will either be next to the audio file, or in the working directory.
        path_to_lyric_txt_file = None
        if path_to_local_copy_next_to_audio.exists():
            path_to_lyric_txt_file = path_to_local_copy_next_to_audio

        if path_to_local_copy_in_working_dir.exists():
            path_to_lyric_txt_file = path_to_local_copy_in_working_dir

        if not path_to_lyric_txt_file:
            return lyrics
        
        file_content = self._read_file_utf8(path_to_lyric_txt_file)
        lyrics.raw = file_content
        lyrics.sanitized = file_content
        lyrics.contains_multipliers = False # To be fixed!
        lyrics.validity = LyricValidity.Valid

        return lyrics


    # def _fetch_lyrics_raw(self, audio_lyric_align_task:AudioLyricAlignTask) -> Tuple[str, LyricValidity]:
    #     """ Returns a tuple consisting of lyrics in a string along with Validity of said lyrics.

    #     The lyric .txt file is expected to share the exact same filename as the song it matches, e.g.
    #     "Blur - Song 2.txt", would match "Blur - Song 2.<audio extension>".

    #     Two locations are searched for matching .txt files:
    #         - The same directory as the audio file.
    #         - LyricManager's working directory.

    #     NOTE: Since .txt files are provided manually by the user, LyricManager will assume Validity for all such files.
    #     """

    #     local_lyric_filename = audio_lyric_align_task.path_to_audio_file.with_suffix(self.file_extension).name

    #     path_to_local_copy_next_to_audio = audio_lyric_align_task.path_to_audio_file.parent / local_lyric_filename
    #     path_to_local_copy_in_working_dir = self.path_to_working_dir / local_lyric_filename

    #     path_to_lyric_txt_file = None
    #     if path_to_local_copy_next_to_audio.exists():
    #         path_to_lyric_txt_file = path_to_local_copy_next_to_audio

    #     if path_to_local_copy_in_working_dir.exists():
    #         path_to_lyric_txt_file = path_to_local_copy_in_working_dir


    #     if not path_to_lyric_txt_file:
    #         return "", LyricValidity.NotFound

    #     logging.info(f"Using local copy: {path_to_lyric_txt_file}")
        
    #     file_content = None

    #     with open(path_to_lyric_txt_file, 'r', encoding='utf8', errors='ignore') as file:
    #         file_content = file.read()
        
    #     # Currently, we *always* assume that local lyric files are valid.
    #     return file_content, LyricValidity.Valid


    """ See LyricFetcherInterface.sanitize_raw_lyrics() for description. """
    def _sanitize_lyrics_raw(self, lyrics_raw: List[str]) -> List[str]:
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