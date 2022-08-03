# Python
from dataclasses import dataclass, field
from pathlib import Path
import sys
sys.path.append("..") # Haxx to access LyricFetcherType

# 3rd Party


# 1st Party
from .lyric_state import LyricValidity
from .lyric_matcher import MatchResult
from lyric_fetcher import LyricFetcherType

# TODO: Explain the 3 phases the text goes through

# TODO: In the future, this dataclass should be able to house multiple lyric sources, for now, it can only manage
# one.

@dataclass
class AudioLyricAlignTask:
    path_to_audio_file: Path
    # filename without extension
    filename: str                   = ""                            # Contained in path_to_audio_file, mostly for convenience / debugging
    artist: float                   = field(init=False)
    song_name: float                = field(init=False)
    lyric_text_raw: str             = ""                            # Local .txt, Genius DB, or other source
    lyric_text_sanitized: list[str] = field(default_factory=list)   # Individual lines of lyrics, used for re-assembling the json/timing .aligned_lyrics
    lyric_text_expanded:  list[str] = field(default_factory=list)   # Detected and replaced {xxxx|4} with xxxx xxxx xxxx xxxx
    lyric_text_alignment_ready: str = ""                            # Lyric text more suitable for NUSAutoAlignLyrix

    # Turn into Enum
    lyric_source: LyricFetcherType  = LyricFetcherType.Disabled

    # Whether [8x], [16x], (4x) or (10x) is in the raw lyrics
    detected_multiplier: bool       = False

    lyric_validity: LyricValidity = LyricValidity.NotSet

    # A dict of the aligned lyric data (generated by convert_aligmentlyrics_to_dict())
    lyrics_aligned: dict            = field(default_factory=dict)

    match_result: MatchResult       = field(default_factory=MatchResult)


    def __post_init__(self):
        """ Parses given data into more granular data. """

        # For now we assume songs always come in this filename form: <artist> - <song name>
        # We split at " - ", as opposed to "-", because hyphens can often appear in both the artist or song name.
        filename_parts = self.path_to_audio_file.stem.split(" - ") # stem, to get file without extension

        self.filename = self.path_to_audio_file.stem

        self.artist = filename_parts[0].strip()
        self.song_name = filename_parts[1].strip()