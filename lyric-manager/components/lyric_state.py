# Python
from enum import Enum, auto

# LyricState is currently semi-hardcoded to the Genius lyric fetcher, this should be made more generic in the
# future

class LyricValidity(Enum):
    NotSet = auto()
    Valid = auto()
    NotFound = auto()
    Invalid = auto()  # Returned HTML or other unintelligable stuff (like Scarface script?!)
    Invalid_NoLyricStringFound = auto()
    Invalid_LyricStringFoundTooFarIntoString = auto()
    Invalid_TooManyChars = auto()
    Invalid_TooFewChars = auto()
    WrongSong = auto()    # Returned lyrics, but not the ones matching the song