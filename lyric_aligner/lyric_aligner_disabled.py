from lyric_aligner import LyricAlignerInterface

# Used to be named 'Off', but this is interpreted as 'False' by PyYaml
class LyricAlignerDisabled(LyricAlignerInterface):

    def __init__(self, path_temp_dir):
        super().__init__(path_temp_dir)

    def _convert_to_wordandtiming(self, input):
        return []

    def align_lyrics(self, path_to_audio_file, path_to_lyric_input):
        return ""