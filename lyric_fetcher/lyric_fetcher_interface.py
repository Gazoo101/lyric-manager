from abc import ABC, abstractmethod

from components import StringEnum

class LyricFetcherInterface(ABC):

    class Type(StringEnum):
        Disabled = "Disabled"
        LocalFile = "LocalFile"
        Genius = "Genius"

    def __init__(self, file_extension):
        self.file_extension = file_extension

    @abstractmethod
    def fetch_lyrics(self, path_to_song):
        raise NotImplementedError
