# Python
import logging

# 3rd Party

# 1st Party
from .lyric_fetcher_interface import LyricFetcherInterface

class LyricFetcherLocalFile(LyricFetcherInterface):

    def __init__(self):
        super().__init__(".txt")

    def fetch_lyrics(self, path_to_song):

        path_to_local_copy = path_to_song.with_suffix(self.file_extension)

        if path_to_local_copy.exists():
            logging.info(f"Using local copy: {path_to_local_copy}")
            
            with open(path_to_local_copy, 'r') as file:
                file_contents = file.read()
            
            return file_contents

        return ""