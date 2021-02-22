from lyric_fetcher import LyricFetcherInterface

class LyricFetcherDisabled(LyricFetcherInterface):

    def __init__(self):
        pass

    def fetch_lyrics(self, path_to_song):
        return ""


# Alt source: https://www.musixmatch.com/