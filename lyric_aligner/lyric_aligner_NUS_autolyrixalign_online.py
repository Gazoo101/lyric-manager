from .lyric_aligner_interface import LyricAlignerInterface

class LyricAlignerNUSAutoLyrixAlignOnline(LyricAlignerInterface):

    def __init__(self, path_temp_dir):
        super().__init__(".nusalaonline", path_temp_dir)

    def _convert_to_wordandtiming(self, input):
        return []

    def align_lyrics(self, path_to_audio_file, path_to_lyric_input):
        return ""