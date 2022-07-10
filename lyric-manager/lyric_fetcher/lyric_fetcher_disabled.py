from lyric_fetcher import LyricFetcherInterface

class LyricFetcherDisabled(LyricFetcherInterface):

    def __init__(self):
        pass

    def fetch_lyrics(self, audio_lyric_align_task):
        return ""


# Alt source: https://www.musixmatch.com/