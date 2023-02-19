# Python
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path


# 3rd Party


# 1st Party


@dataclass
class WordAndTiming():
    word: str
    time_start: float
    time_end: float


class LyricAlignerInterface(ABC):

    # @classmethod
    # @abstractmethod
    # def create(cls, **kwargs):
    #     raise NotImplementedError("All Lyric aligners must provide this implementation.")

    def __init__(self, file_extension, path_temp_dir, path_to_output_dir: Path = None):
        self.file_extension = file_extension

        self.path_temp_dir = path_temp_dir

        logging.info(f"LyricAligner Temp path: {self.path_temp_dir}")
        self.path_temp_dir.mkdir(parents=True, exist_ok=True)
        self.path_to_output_dir = path_to_output_dir

    def get_corresponding_aligned_lyric_file(self, path_to_audio_file):
        path_to_lyric_aligned_file = path_to_audio_file.with_suffix(self.file_extension)

        if self.path_to_output_dir:
            path_to_lyric_aligned_file = self.path_to_output_dir / path_to_lyric_aligned_file.name

        return path_to_lyric_aligned_file

    # def aligned_lyrics_exists(self, path_to_audio_file):
    #     path_to_aligned_lyric_file = path_to_audio_file.with_suffix(self.file_extension)

    #     return path_to_aligned_lyric_file.exists()

    def copy_aligned_lyrics_output(self, path_to_audio_file, path_to_aligned_lyrics):
        path_to_aligned_lyric_file = self.get_corresponding_aligned_lyric_file(path_to_audio_file)
        components.FileOperations.copy_and_rename(path_to_aligned_lyrics, path_to_aligned_lyric_file)
        return path_to_aligned_lyric_file

    @abstractmethod
    def align_lyrics(self, path_to_audio_file, path_to_lyric_input, use_preexisting) -> list[WordAndTiming]:
        raise NotImplementedError

    @abstractmethod
    def _convert_to_wordandtiming(self, input):
        raise NotImplementedError