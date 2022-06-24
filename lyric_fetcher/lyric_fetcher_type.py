from enum import Enum, auto

class LyricFetcherType(Enum):
    Disabled = auto()
    LocalFile = auto()
    Genius = auto()
    LyricsDotOvh = auto()