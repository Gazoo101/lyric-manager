from .lyric_fetcher_interface import LyricFetcherInterface
from .lyric_fetcher_type import LyricFetcherType

class LyricFetcherDisabled(LyricFetcherInterface):

    @classmethod
    def create(cls, **kwargs):
        return cls()

    def __init__(self):
        super()

    def fetch_lyrics(self, audio_lyric_align_task):
        return ""


# Alt source: https://www.musixmatch.com/