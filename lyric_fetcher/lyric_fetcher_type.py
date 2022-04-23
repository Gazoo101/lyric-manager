from components import StringEnum

class LyricFetcherType(StringEnum):
    Disabled = "Disabled"
    LocalFile = "LocalFile"
    Genius = "Genius"
    LyricsDotOvh = "LyricsDotOvh"