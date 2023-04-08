# Python
from enum import Enum, auto

# 3rd Party

# 1st Party

class LyricFetcherType(Enum):
    #Disabled = auto()
    LocalFile = auto()
    Pypi_LyricsGenius = auto()
    Pypi_LyricsExtractor = auto()
    #Website_LyricsDotOvh = auto()

# Potential future source: https://www.musixmatch.com/