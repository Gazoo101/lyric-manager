# Python
import logging
from pathlib import Path
from dataclasses import dataclass, field
from enum import Enum, auto

# 3rd Party
import eyed3

# 1st Party
from ...developer_options import DeveloperOptions

from .lyric_payload import LyricPayload
from .lyric_match import MatchResult, MatchLyric
#from ..lyric_matcher import MatchResult
from .lyric_fetcher_type import LyricFetcherType
from .lyric_validity import LyricValidity


class LyricAlignmentOutput(Enum):
    # Automated means no human tweaked the results
    Automated = auto()

    # Tweaked means that after tha automated output, a human tweaked the results
    Tweaked = auto()

@dataclass
class LyricAlignTask:
    """ Contains lyric and lyric metadata passed through LyricManager as it fetches and aligns lyrics.

    The high-level steps of a LyricAlignTask object is:
        1. Instantiation from a path to an audio file.
        2. Lyrics related to the song are fetched.
        3. Lyrics are sanitized to prepare for alignment.
        4. Alignment data is generated and finally written to disk.

    Currently, LyricAlignTask can only house lyrics from a single source, but in the future it might be advantagous for
    it to actually house lyrics from multiple sources.
    """

    path_to_audio_file: Path
    # filename without extension
    filename: str                   = ""                            # Contained in path_to_audio_file, mostly for convenience / debugging
    artist: str                     = ""
    song_name: str                  = ""

    # Fetch-related lyric properties
    lyric_payload: LyricPayload     = field(default_factory=LyricPayload)

    # Alignment-related lyric properties
    lyric_text_expanded: str        = ""                            # Detected and replaced {xxxx|4} with xxxx xxxx xxxx xxxx
    lyric_lines_expanded: list[str] = field(default_factory=list)
    lyric_text_alignment_ready: str = ""                            # Lyric text more suitable for NUSAutoAlignLyrix

    lyric_fetcher_type_source: LyricFetcherType = None # Local .txt, Genius DB, or other source

    # Whether [8x], [16x], (4x) or (10x) is in the raw lyrics - actually {} I think...?
    detected_multiplier: bool       = False

    lyrics_aligned_automated: list[MatchLyric] = field(default_factory=list)
    lyrics_aligned_tweaked: list[MatchLyric]   = field(default_factory=list)

    # We keep a copy of the 'to disk written final aligned lyrics output' as a sanity check for then the GUI is to
    # report on the final succesful result.
    lyrics_aligned_disk_output: dict = field(default_factory=dict)

    # Performance of alignment data is measured for both the automated, and manually tweaked alignment data
    match_result_automated: MatchResult = field(default_factory=MatchResult)
    match_result_tweaked: MatchResult   = field(default_factory=MatchResult)

    # Defaults to automated, as the tweaked output is expected to always be based on top of an automated output
    final_output_type: LyricAlignmentOutput = LyricAlignmentOutput.Automated


    def __post_init__(self):
        """ Parses given data into more granular data. """
        self.filename = self.path_to_audio_file.stem

    
    @classmethod
    def create_prefer_artist_song_name_from_filename(cls, path_to_audio_file: Path):
        """ Creates LyricAlignTask given a path to an audio file, preferring to derive artist/song name from the filename.
        
        Args:
            path_to_audio_file: Path to the audio file to be processed.
        Returns:
            A LyricAlignTask object.
        """
        lyric_align_task: LyricAlignTask = cls(path_to_audio_file)

        if not lyric_align_task._derive_artist_song_name_from_filename():
            if not lyric_align_task._derive_artist_song_name_from_tags():
                logging.warning(f"Unable to derive artist and song name from: '{lyric_align_task.filename}'")
                return None

        return lyric_align_task
    
    @classmethod
    def create_prefer_artist_song_name_from_tags(cls, path_to_audio_file: Path):
        """ Creates LyricAlignTask given a path to an audio file, preferring to derive artist/song name from file tags.
        
        Args:
            path_to_audio_file: Path to the audio file to be processed.
        Returns:
            A LyricAlignTask object.
        """
        lyric_align_task: LyricAlignTask = cls(path_to_audio_file)

        if not lyric_align_task._derive_artist_song_name_from_tags():
            if not lyric_align_task._derive_artist_song_name_from_filename():
                logging.warning(f"Unable to derive artist and song name from: '{lyric_align_task.filename}'")
                return None

        return lyric_align_task


    def _derive_artist_song_name_from_tags(self) -> bool:
        """ Sets artist and song title based on the audio file's meta tags.
        
        Returns:
            True if the artist and song title was set correctly, otherwise False.
        """

        # Currently, we only support accessing .mp3 file audio tags.
        if self.path_to_audio_file.suffix != ".mp3":
            return False

        audio_file = eyed3.load(self.path_to_audio_file)

        if not audio_file:
            return False
        
        if not audio_file.tag:
            return False
        
        if audio_file.tag.artist is None or audio_file.tag.title is None:
            return False

        self.artist = audio_file.tag.artist
        self.song_name = audio_file.tag.title

        return True
    

    def _derive_artist_song_name_from_filename(self) -> bool:
        """ Sets artist and song title based on the audio file's filename.
        
        Returns:
            True if the artist and song title was set correctly, otherwise False.
        """

        # For now we assume songs always come in this filename form: <artist> - <song name>
        # We split at " - ", as opposed to "-", because hyphens can often appear in both the artist or song name.
        filename_parts = self.path_to_audio_file.stem.split(" - ")

        # With more than one free-floating hyphen it's significantly harder to determine what's the full artist and song name
        if len(filename_parts) != 2:
            return False
        
        self.artist = filename_parts[0].strip()
        self.song_name = filename_parts[1].strip()

        return True


    def get_user_friendly_result(self) -> str:
        """ Returns an interpreted user-friendly string describing the result status of the task. """

        if self.lyric_payload.validity != LyricValidity.Valid:
            return self.lyric_payload.validity.text
        
        if not self.lyric_text_alignment_ready:
            return "Valid Lyrics - No alignment done."
        
        if not self.lyrics_aligned_disk_output:
            return "Valid Lyrics - No alignment written to disk, which is strange as the data was prepared to do it?"
        
        match(self.final_output_type):
            case LyricAlignmentOutput.Automated:
                return "Valid Lyrics - Automated source"
            case LyricAlignmentOutput.Tweaked:
                return "Valid Lyrics - Tweaked source"
            case _:
                return "Valid Lyrics - But unknown source?! This shouldn't happen."
            

    def convert_best_aligment_lyrics_to_dict(self) -> dict:
        """ Converts MatchLyric data-classes into a dict ready for Json conversion for disk-serialization. """

        ready_to_export_lyrics = {
            "schema_version": DeveloperOptions.json_schema_version,
            "lyric_lines": []
        }

        # Get the best matching lyrics
        all_lyrics: list[MatchLyric] = []

        match(self.final_output_type):
            case LyricAlignmentOutput.Automated:
                all_lyrics = self.lyrics_aligned_automated
                ready_to_export_lyrics["lyric_match_percentage"] = self.match_result_automated.match_percentage
            case LyricAlignmentOutput.Tweaked:
                all_lyrics = self.lyrics_aligned_tweaked
                ready_to_export_lyrics["lyric_match_percentage"] = self.match_result_tweaked.match_percentage
            case _:
                logging.warning(f"Attempted to convert aligned lyrics for '{self.filename}' to writable output when no proper source was available?|")
                return {}

        for lyric in all_lyrics:
            # Assemble into sentences again for entry into dict / strings
            
            if lyric.line_index == len(ready_to_export_lyrics["lyric_lines"]):

                lyric_line = {
                    "text": lyric.word_original,    # This may be entire lyric line and not just a word
                    "text": lyric.get_alignment_lyric_with_pre_post_chars(),
                    "time_start": lyric.time_start,
                    "time_end": lyric.time_end,
                    "lyric_words": [{
                        "original": lyric.word_original,
                        "single": lyric.word_single,
                        "word_split_char_pre": lyric.word_split_char_pre,
                        "word_split_char_post": lyric.word_split_char_post,
                        "time_start": lyric.time_start,
                        "time_end": lyric.time_end
                    }]
                }

                ready_to_export_lyrics["lyric_lines"].append(lyric_line)
            else:
                ready_to_export_lyrics["lyric_lines"][lyric.line_index]["text"] += lyric.get_alignment_lyric_with_pre_post_chars()

                # If the time_start of the lyricLine is undefined, we grab the first available lyricWord time_start
                if (ready_to_export_lyrics["lyric_lines"][lyric.line_index]["time_start"] == -1):
                    ready_to_export_lyrics["lyric_lines"][lyric.line_index]["time_start"] = lyric.time_start

                # If the time_end of the lyricWord is undefined, we skip updating the lyricLine's time_end
                if (lyric.time_end != -1):
                    ready_to_export_lyrics["lyric_lines"][lyric.line_index]["time_end"] = lyric.time_end
                
                ready_to_export_lyrics["lyric_lines"][lyric.line_index]["lyric_words"].append({
                    "original": lyric.word_original,
                    "single": lyric.word_single,
                    "word_split_char_pre": lyric.word_split_char_pre,
                    "word_split_char_post": lyric.word_split_char_post,
                    "time_start": lyric.time_start,
                    "time_end": lyric.time_end
                })
            
        return ready_to_export_lyrics