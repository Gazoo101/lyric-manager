# Python
from dataclasses import dataclass


# 3rd Party


# 1st Party
from ...components.miscellaneous import percentage
from ...components.miscellaneous import get_percentage_and_amount_string



@dataclass
class MatchLyric:
    """ Houses matching data to re-connect a time-aligned word back to the originally structured lyrics. """
    word_original: str                # Includes apostrophe's, commas, and ()'s, e.g. "(bring", "one,", "Glancin'", "Jealousy!"

    # Hyphenated or other-wise split words get separated and passed in as individual words to the alignment neural
    # network. line_index helps reconnect these split pieces to the original word.
    line_index: int

    # Same as word_original, except it doesn't contain commas, ()'s, but keeps short-hand apostrophes, e.g. "bring", "one", "Glancin'"
    word_single: str            = ""

    word_alignment: str         = ""  # Similar to word_single, except converts slangy words to full, e.g. "Glancing"
    word_split_char_pre: str    = " " # The pre-character that a lyric-word was split on. Most often a space " ", sometimes a hyphen "-"
    word_split_char_post: str   = " " # The pos-character that a lyric-word was split on. Most often a space " ", sometimes a hyphen "-"
    time_start: float           = -1.0
    time_end: float             = -1.0

    # Actually only appends the post - perhaps this is a bug?
    def get_alignment_lyric_with_pre_post_chars(self):
        return self.word_original + self.word_split_char_post


@dataclass
class MatchResult:
    words_total: int          = 0
    words_matched: int        = 0
    match_percentage: float   = -1.0

    def __post_init__(self):
        self.match_percentage = percentage(self.words_matched, self.words_total)

    def get_string(self):
        return get_percentage_and_amount_string(self.words_matched, self.words_total)
