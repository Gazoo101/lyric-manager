# Python

# 3rd Party

# 1st Party
from .lyric_fetcher_interface import LyricFetcherInterface


class LyricFetcherDisabled(LyricFetcherInterface):
    """ A dummy 'disabled' class to allow for skipping Lyric fetching.
    
    Not sure this actually has any real use anymore. Consider deprecating.
    
    """

    @classmethod
    def create(cls, **kwargs):
        return cls()

    def __init__(self):
        super()

    def fetch_lyrics(self, audio_lyric_align_task):
        return ""