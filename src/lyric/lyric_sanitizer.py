# Python
import re
from typing import List

# 3rd Party


# 1st Party



class LyricSanitizer():
    """ LyricSanitizer is responsible for cleaning up raw lyrics to make them easier to align.

    An ever growing number of exceptional cases has compelled the creation of this class.
    
    
    """
    def __init__(self) -> None:
        reg_exp_find_lyric_multiplications = r"[(\[]\d+x[)\]]"
        self.re_comp_find_lyric_multiplications = re.compile(reg_exp_find_lyric_multiplications)


    def remove_leading_title(self, song_name:str, lyrics:str):
        """ Removes the leading '<song name> Lyrics' text piece. """

        # We employ 2 strategies to remove this pesky leading title.
        #   1. Find a '[' char in the first line and remove everything prior to it.
        #   2. Match the "<song name> Lyrics" to the start of the lyrics - this can fail due to ` and ' in names

        # Strategy 1
        length_of_song_name_and_lyrics_word = len(song_name) + 7 + 10

        lyrics_start = lyrics[:length_of_song_name_and_lyrics_word]

        pos_of_bracket_start = lyrics_start.find("[")

        if pos_of_bracket_start != -1:
            return lyrics[pos_of_bracket_start:]

        # else - Strategy 2

        # Case-insensitive matching using re, as 'lyrics' can end up being very lengthy, so we don't want to call .lower()
        # on it.
        if bool(re.match(f"{song_name} Lyrics", lyrics, re.I)):
            length_to_chop = len(song_name) + 7
            return lyrics[length_to_chop:]
        
        return lyrics


    def remove_embed_at_end(self, lyrics:str):
        sanitized = re.sub(r"\d*Embed$", '', lyrics)
        return sanitized


    def remove_non_lyrics_v2(self, all_lyric_lines: List[str]):
        """ Returns a list of sanitized lyric strings.

        Each string in the list represents a single coheasive sung sentence. This is used during
        visualization to cohesively visualize sentances.
        """
        # Lyrics are provided in a single large string

        sanitized_lyric_lines = []

        for lyric_line in all_lyric_lines:
            # Removes [<any content, except newlines>]
            #complete_lyric_string = re.sub(r"\[.*\]", '', complete_lyric_string)
            #lyric_line = re.sub(r"\[[a-zA-Z0-9 -]*\]", '', lyric_line) # Didn't catch &, or . and the like
            lyric_line = re.sub(r"\[(.*?)\]", '', lyric_line)

            lyric_line = lyric_line.strip()

            sanitized_lyric_lines.append(lyric_line)

        # Remove empty lines
        non_empty_lyric_lines = [lyric_line for lyric_line in sanitized_lyric_lines if lyric_line]


        # complete_lyric_string = ' '.join(non_empty_lyric_lines)

        # # Removes [<any content, except newlines>]
        # #complete_lyric_string = re.sub(r"\[.*\]", '', complete_lyric_string)
        # complete_lyric_string = re.sub(r"\[[a-zA-Z0-9 -]*\]", '', complete_lyric_string)

        # # Remove double-spaces
        # complete_lyric_string = ' '.join(complete_lyric_string.split())

        return non_empty_lyric_lines


    #
    # TO BE DEPRECATED!
    def remove_non_lyrics(self, lyrics:str):
        """ Returns a list of sanitized lyric strings.

        Each string in the list represents a single coheasive sung sentence. This is used during
        visualization to cohesively visualize sentances.
        """
        # Lyrics are provided in a single large string

        # 1. Reformat string into per-line for easier human manipulation
        all_lyric_lines = lyrics.splitlines()

        sanitized_lyric_lines = []

        for lyric_line in all_lyric_lines:
            # Removes [<any content, except newlines>]
            #complete_lyric_string = re.sub(r"\[.*\]", '', complete_lyric_string)
            #lyric_line = re.sub(r"\[[a-zA-Z0-9 -]*\]", '', lyric_line) # Didn't catch &, or . and the like
            lyric_line = re.sub(r"\[(.*?)\]", '', lyric_line)

            lyric_line = lyric_line.strip()

            sanitized_lyric_lines.append(lyric_line)

        # Remove empty lines
        non_empty_lyric_lines = [lyric_line for lyric_line in sanitized_lyric_lines if lyric_line]


        # complete_lyric_string = ' '.join(non_empty_lyric_lines)

        # # Removes [<any content, except newlines>]
        # #complete_lyric_string = re.sub(r"\[.*\]", '', complete_lyric_string)
        # complete_lyric_string = re.sub(r"\[[a-zA-Z0-9 -]*\]", '', complete_lyric_string)

        # # Remove double-spaces
        # complete_lyric_string = ' '.join(complete_lyric_string.split())

        return non_empty_lyric_lines

    
    def replace_difficult_characters(self, lyrics):
        """ Replaces characters that cause issues in the lyric rendering pipeline.

        Rather than supporting every possible character, it's initially far simpler, to replace
        the difficult ones and add support for more and more in the future

        """
        lyrics_cleaned = []

        # Recorded instance of "white's" being recognized, but "white’s" *not* being recognized
        # Recorded instance of "I'm" being recognized, but not "Ims", "I'ms"

        for lyric in lyrics:
            lyrics_cleaned.append(lyric.replace("’", "'")) # Annoying almost-apostrophe

        return lyrics_cleaned


    # Should be extracted out into another object...
    def contains_multipliers(self, lyrics: str):
        """ Tries to locate instances of (4x) or [10x] etc. """

        if self.re_comp_find_lyric_multiplications.search(lyrics):
            return True
        
        return False