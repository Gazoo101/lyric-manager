from lyric_fetcher import LyricFetcherInterface
from .lyric_fetcher_type import LyricFetcherType

class LyricFetcherDisabled(LyricFetcherInterface):

    def __init__(self):
        super()

    def fetch_lyrics(self, audio_lyric_align_task):
        return ""


# Alt source: https://www.musixmatch.com/