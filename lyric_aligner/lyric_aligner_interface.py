# Python
from abc import ABC, abstractmethod
import logging
from collections import namedtuple

# 3rd Party

# 1st Party
from components import StringEnum

WordAndTiming = namedtuple("WordAndTiming", ["word", "time_start", "time_end"])

class LyricAlignerInterface(ABC):

    class Type(StringEnum):
        Disabled = "Disabled"
        NUSAutoLyrixAlignOnline = "NUSAutoLyrixAlignOnline"
        NUSAutoLyrixAlignOffline = "NUSAutoLyrixAlignOffline"

    def __init__(self, path_temp_dir):
        self.path_temp_dir = path_temp_dir

        logging.info(f"LyricAligner Temp path: {self.path_temp_dir}")

    @abstractmethod
    def align_lyrics(self, path_to_audio_file, path_to_lyric_input):
        raise NotImplementedError

    @abstractmethod
    def _convert_to_wordandtiming(self, input):
        raise NotImplementedError