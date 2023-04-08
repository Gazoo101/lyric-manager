# Python
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path


# 3rd Party


# 1st Party
from ...components import FileOperations


@dataclass
class WordAndTiming():
    word: str
    time_start: float
    time_end: float


class LyricAlignerInterface(ABC):

    def __init__(self, file_extension, path_aligner_temp_dir, path_to_output_dir: Path = None):
        self.file_extension = file_extension

        self.path_aligner_temp_dir = path_aligner_temp_dir

        logging.info(f"LyricAligner Temp path: {self.path_aligner_temp_dir}")
        self.path_aligner_temp_dir.mkdir(parents=True, exist_ok=True)
        self.path_to_output_dir = path_to_output_dir


    def _get_cached_aligned_output_file(self, path_to_audio_file:Path) -> Path:
        """ Retrieves a previously generated aligned output file.

        It is time-consuming to align lyrics to an audio file. For example, NUSAutoLyrixAlign takes roughly 1 minutes of
        time for 1 minute of audio, leading to a lot of time consumed to parse an entire library.

        Two locations are checked for pre-exiting output:

        1. The specified output directory of the LyricAligner.

        2. The location next to the audio file itself.
        
        """
        # alignment_file is the aligner cached file of a song, e.g. ABBA - Money.nusalaoffline

        path_to_alignment_file_next_to_audio_file = path_to_audio_file.with_suffix(self.file_extension)
        alignment_filename = path_to_alignment_file_next_to_audio_file.name

        if self.path_to_output_dir:
            path_to_lyric_aligned_in_output_folder = self.path_to_output_dir / alignment_filename
            
            if path_to_lyric_aligned_in_output_folder.exists():
                return path_to_lyric_aligned_in_output_folder
        
        if path_to_alignment_file_next_to_audio_file.exists():
            return path_to_alignment_file_next_to_audio_file
        
        return None

    def get_corresponding_aligned_lyric_file(self, path_to_audio_file:Path):
        path_to_lyric_aligned_file = path_to_audio_file.with_suffix(self.file_extension)

        if self.path_to_output_dir:
            path_to_lyric_aligned_file = self.path_to_output_dir / path_to_lyric_aligned_file.name

        return path_to_lyric_aligned_file

    # def aligned_lyrics_exists(self, path_to_audio_file):
    #     path_to_aligned_lyric_file = path_to_audio_file.with_suffix(self.file_extension)

    #     return path_to_aligned_lyric_file.exists()

    def copy_aligned_lyrics_to_working_directory(self, path_to_aligned_lyrics: Path, path_to_audio_file: Path):
        """ Copies 'lyric_aligned.txt' from a temporary output path to LyricManagers working directory.

        Args:
            path_to_aligned_lyrics: Path to the temporary 'lyric_aligned.txt' file.
            path_to_audio_file: Path to the audio file to which the lyrics are aligned. Only used for naming, i.e. to
                create 'artist - song title.aligned_lyrics'
        Returns:
            A path to the 'lyric_aligned.txt' file in the working directory.
        """
        path_to_aligned_lyric_file = self.get_corresponding_aligned_lyric_file(path_to_audio_file)
        FileOperations.copy_and_rename(path_to_aligned_lyrics, path_to_aligned_lyric_file)
        return path_to_aligned_lyric_file


    @abstractmethod
    def align_lyrics(self, path_to_audio_file: Path, path_to_lyric_input: Path, use_preexisting: bool) -> list[WordAndTiming]:
        raise NotImplementedError

    @abstractmethod
    def _convert_to_wordandtiming(self, input):
        raise NotImplementedError