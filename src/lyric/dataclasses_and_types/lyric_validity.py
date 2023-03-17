# Python
from enum import Enum, auto

# 3rd Party

# 1st Party


class LyricValidity(Enum):

    def __new__(cls, value, text):
        """ Creates a new Enum object which accepts a value *and* a descriptive text string """
        obj = object.__new__(cls)
        obj._value = value
        obj.text = text
        return obj

    NotSet = auto(), "Not Set"
    Valid = auto(), "Valid Lyrics"
    NotFound = auto(), "No Lyrics Found"
    Invalid = auto(), "Invalid Lyrics - No further details."  # Returned HTML or other unintelligable stuff (like Scarface script?!)
    Invalid_NoLyricStringFound = auto(), "Invalid Lyrics - A required token ('Lyric') was not found."
    Invalid_LyricStringFoundTooFarIntoString = auto(), "Invalid Lyrics - A required token ('Lyric') was found too late into the lyrics."
    Invalid_TooManyChars = auto(), "Invalid Lyrics - Too much text to be considered valid lyrics."
    Invalid_TooFewChars = auto(), "Invalid Lyrics - Too little text to be considered valid lyrics."
    WrongSong = auto(), "Invalid Lyrics - Lyrics for a different song were found." # Returned lyrics, but not the ones matching the song
    Skipped_Due_To_Fetch_Errors = auto(), "Skipped fetching due to previous fetching errors."