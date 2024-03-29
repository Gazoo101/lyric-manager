# Python
import re
import logging

# 3rd Party


# 1st Party
from .dataclasses_and_types import LyricAlignTask

class LyricExpander():
    """ When/If this class starts doing more than expansion (other logic), rename it to LyricLogic """

    def __init__(self) -> None:
        # compile the thing...

        # Explain: {}
        brackets_re = r"\{([^|]*?)\|(\d+)\}"

        self.compiled = re.compile(brackets_re)


    def expand_lyrics(self, filename: str, lyrics: str):
        """
        
        Input is one long connected text string...
        
        """

        # Re-connect all data
        #lyrics_expanded = "\n".join(audio_lyric_align_task.lyric_text_sanitized) # no longer reconnect
        lyrics_expanded = lyrics

        match = self.compiled.search(lyrics_expanded)

        while match:

            # Python's indexing with .groups() and .group() is very unorthodox. E.g. len(.groups()) will yield
            # 2, but the indexing goes all the way up to .group(2) where .group(0) is neither of the groups, but
            # instead the full match.
            num_groups = len(match.groups())
            if num_groups != 2:
                logging.warning(f"'{filename}' contained group mismatch.")
                logging.warning(f"Mixmatch: {match.group(0)}")
                continue

            full_match_start = match.start(0)
            full_match_end = match.end(0)

            text_to_repeat = match.group(1)
            repetitions = int(match.group(2))

            # Craft expanded string - We insert a \n to handle things 'sticking together'
            match_expanded = (text_to_repeat + "\n") * repetitions

            # Insert expanded text
            text_up_to_match = lyrics_expanded[:full_match_start]
            text_after_match = lyrics_expanded[full_match_end:]
            lyric_expanded_partial = text_up_to_match + match_expanded + text_after_match

            # Apply update and repeat
            lyrics_expanded = lyric_expanded_partial
            match = self.compiled.search(lyrics_expanded)

        return lyrics_expanded
