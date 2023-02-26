# Python
from pathlib import Path

# 1st Party
from .lyric_aligner_interface import LyricAlignerInterface
from .lyric_aligner_interface import WordAndTiming

# 3rd Party


class LyricAlignerNUSAutoLyrixAlignOnline(LyricAlignerInterface):
    """ Lyric aligner based on the online version of the NUS Auto Lyrix Align project located here:
    https://autolyrixalign.hltnus.org

    At the time of writing, 01-07-2022, the page appears to be offline. Plans to complete this implementation are very
    low priority. You're encouraged to use LyricAlignerNUSAutoLyrixAlignOffline instead.
    """

    def __init__(self, path_temp_dir):
        super().__init__(".nusalaonline", path_temp_dir)

    def _convert_to_wordandtiming(self, input):
        return []

    def align_lyrics(self, path_to_audio_file: Path, path_to_lyric_input: Path, use_preexisting: bool) -> list[WordAndTiming]:
        return ""