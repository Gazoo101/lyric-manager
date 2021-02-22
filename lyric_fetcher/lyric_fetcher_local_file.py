# Python

# 3rd Party

# 1st Party
from .lyric_fetcher_interface import LyricFetcherInterface

class LyricFetcherLocalFile(LyricFetcherInterface):

    def __init__(self):
        super().__init__(".txt")

    def fetch_lyrics(self, path_to_song):
        return ""