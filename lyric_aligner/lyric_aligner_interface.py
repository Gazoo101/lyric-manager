# Python
from abc import ABC, abstractmethod
import logging
from collections import namedtuple

# 3rd Party

# 1st Party
import components

WordAndTiming = namedtuple("WordAndTiming", ["word", "time_start", "time_end"])

class LyricAlignerInterface(ABC):

    def __init__(self, file_extension, path_temp_dir):
        self.file_extension = file_extension

        self.path_temp_dir = path_temp_dir

        logging.info(f"LyricAligner Temp path: {self.path_temp_dir}")
        self.path_temp_dir.mkdir(parents=True, exist_ok=True)

    def get_corresponding_aligned_lyric_file(self, path_to_audio_file):
        return path_to_audio_file.with_suffix(self.file_extension)

    # def aligned_lyrics_exists(self, path_to_audio_file):
    #     path_to_aligned_lyric_file = path_to_audio_file.with_suffix(self.file_extension)

    #     return path_to_aligned_lyric_file.exists()

    def copy_aligned_lyrics_output(self, path_to_audio_file, path_to_aligned_lyrics):
        path_to_aligned_lyric_file = self.get_corresponding_aligned_lyric_file(path_to_audio_file)
        components.FileOperations.copy_and_rename(path_to_aligned_lyrics, path_to_aligned_lyric_file)
        return path_to_aligned_lyric_file

    @abstractmethod
    def align_lyrics(self, path_to_audio_file, path_to_lyric_input):
        raise NotImplementedError

    @abstractmethod
    def _convert_to_wordandtiming(self, input):
        raise NotImplementedError