# Python
from enum import Enum

# 3rd Party

# 1st Party


class StringEnum(Enum):
    ''' Similar to Python's IntEnum except based on the String primitive.

    Usage example:

        class Type(Enum):
            Off = "Off"
            NUSAutoLyrixAlignOnline = "NUSAutoLyrixAlignOnline"
            NUSAutoLyrixAlignOffline = "NUSAutoLyrixAlignOffline"

    Note the missing comma separator. If it's present Python will instead
    interpret the entry as a (string,None) tuple. '''

    @classmethod
    def as_dict(cls):
        return { enumEntry.value.lower() : enumEntry for enumEntry in cls }

    # Useful when converting into a list of strings for ArgumentParser
    def __str__(self):
        return self.value