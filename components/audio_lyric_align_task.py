# Python
from dataclasses import dataclass, field
from pathlib import Path

# 3rd Party


# 1st Party


# TODO: Explain the 3 phases the text goes through

@dataclass
class AudioLyricAlignTask:
    path_to_audio_file: Path
    artist: float = field(init=False)
    song_name: float = field(init=False)
    lyric_text_raw: str = ""                # Local .txt, Genius DB, or other source
    lyric_text_sanitized: str = ""          # Lyric text more suitable for NUSAutoAlignLyrix
    lyric_text_alignment_ready: str = ""

    def __post_init__(self):
        """ Parses given data into more granular data. """

        # For now we assume songs always come in this filename form: <artist> - <song name>
        # We split at " - ", as opposed to "-", because hyphens can often appear in both the artist or song name.
        filename_parts = self.path_to_audio_file.stem.split(" - ") # stem, to get file without extension

        self.artist = filename_parts[0].strip()
        self.song_name = filename_parts[1].strip()