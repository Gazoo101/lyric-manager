from abc import ABC, abstractmethod

class LyricFetcherInterface(ABC):

    def __init__(self, file_extension):
        self.file_extension = file_extension

    @abstractmethod
    def fetch_lyrics(self, path_to_song):
        raise NotImplementedError
