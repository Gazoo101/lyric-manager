# Python
from enum import Enum, auto


class AudioArtistAndSongNameSource(Enum):
    FileName = auto()
    FileTags = auto()