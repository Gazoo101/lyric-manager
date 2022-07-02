# Python
import re
from dataclasses import dataclass
from typing import List

# 3rd Party


# 1st Party


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


class LyricMatcher():
    """ Matches 'words and associated timing information' produced by the lyric aligner to 'fetched lyrics'.

    *** 'Fetched Lyrics' looks like this:

    Time to settle the score, man it's time to play
    Take a big step back, slap the ball away
    Now it's only a matter of time, everybody knows this game is mine
    Ha! I'm gonna run you down to the ground, no time to get up, no time to make a sound

    Gotta jump slam-dunk and don't let up! Power team! Power up!

    *** Words with timing information looks like this:

    38.37 38.58 TIME
    38.58 38.7 TO
    38.70 39.03 SETTLE
    39.03 39.12 THE
    39.12 39.54 SCORE
    39.54 39.81 MAN
    39.81 39.96 IT'S
    39.96 40.23 TIME
    40.23 40.35 TO
    40.35 40.74 PLAY
    40.74 41.04 TAKE
    41.04 41.1 A

    ***************************************

    'Fetched lyrics' contain:
        - Sentence structure, i.e. not one big blob of text
        - Non-Letter characters
        - Slangy written words - talkin', glancin'

    These elements are removed when passing the data into NUSAutoLyrixAlign. To retain the sentence structure and
    associated non-letter characters, a matching process must be performed to connect the timing information back to
    the 'Fetched lyrics' structured text.
    """

    def __init__(self, json_schema_version):
        self.json_schema_version = json_schema_version


    def convert_lyrics_string_to_match_lyrics(self, lyrics: List[str]):
        '''

        Args:
            lyrics: A list of strings.
        
        Returns:
            A list of Alignment
        '''
        all_match_lyrics:List[MatchLyric] = self._split_lyrics_raw_spoken_segments(lyrics)

        for match_lyric in all_match_lyrics:
            word_single, word_alignment_ready = self._create_standalone_and_alignment_ready_word(match_lyric)

            match_lyric.word_single = word_single
            match_lyric.word_alignment = word_alignment_ready


        #self._polish_alignmentlyrics(segmented_alignment_lyrics)

        return all_match_lyrics
    

    def _split_lyrics_raw_spoken_segments(self, lyrics: List[str]):
        """ Splits raw text lyrics into spoken segments, contained in AlignmentLyrics.

        Spoken segments are split based on spaces and hyphens. This approach was primarily
        chosen because the lyric alignment times these pieces separarately, and therefore
        we're interested in the flexibility of also rendering them separately. 

        Args:
            lyrics: A list of strings.
        """
        segmented_alignment_lyrics = []

        for line_index, lyric_line in enumerate(lyrics):

            # if line_index == 32:
            #     horse = 2

            # The first priority is to split the raw lyrics up into the segments that recieve individual
            # timing and thus will be individually rendered.

            # This splitting algorithm is ok because we only will split rendered segments by 2 types of
            # chars. Spaces ' ' and hyphens '-'. If the number of chars that create segment split
            # increases, this 2x loop stops being tennable.
            spaced_lyric_line_parts = lyric_line.split(' ')
            spaced_alignment_lyrics = []

            for spaced_word in spaced_lyric_line_parts:

                #hyphenate_parts = spaced_word.split('-')
                # Regular .split() will split *all* hyphens, even end of word hyphens, which we don't want to split on.
                hyphenate_parts = re.split(r"(?<=\w)-(?=\w)", spaced_word )
                hyphenated_alignment_lyrics = []

                # Is the word hypenated
                if len(hyphenate_parts) > 1:

                    for hyphened_word in hyphenate_parts:

                        alignment_lyric = MatchLyric(
                            hyphened_word,
                            line_index,
                            word_split_char_pre='-', # Add post-dash to all pieces. Remove the last one later.
                            word_split_char_post='-',
                        )

                        hyphenated_alignment_lyrics.append(alignment_lyric)
                    
                    # Remove the excess start/end hyphen
                    hyphenated_alignment_lyrics[0].word_split_char_pre = ' '
                    hyphenated_alignment_lyrics[-1].word_split_char_post = ' '

                    spaced_alignment_lyrics.extend(hyphenated_alignment_lyrics)
                    continue

                alignment_lyric = MatchLyric(spaced_word, line_index)

                spaced_alignment_lyrics.append(alignment_lyric)

            spaced_alignment_lyrics[0].word_split_char_pre = ''
            spaced_alignment_lyrics[-1].word_split_char_post = ''

            segmented_alignment_lyrics.extend(spaced_alignment_lyrics)
        
        return segmented_alignment_lyrics


    def _create_standalone_and_alignment_ready_word(self, lyric: MatchLyric):
        """ Creates and returns

        reference struct above
        
        """

        # Copied from above:
        # ('word_original', ''),  # Includes apostrophe's, commas, and ()'s, e.g. "(bring", "one,", "Glancin'", "Jealousy!"
        # ('word_single', ''),    # Doesn't contain commas, ()'s, but keeps short-hand apostrophes, e.g. "bring", "one", "Glancin'"
        # ('word_alignment', ''), # Similar to word_single, except converts slangy words to full, e.g. "Glancing"

        word_single = lyric.word_original

        # Hyphens and spaces are handled already.
        characters_to_remove = [',', '!', '(', ')', '"']

        for char in characters_to_remove:
            word_single = word_single.replace(char, '')

        word_alignment = word_single

        # Fixing "in'" => "ing"
        #for a_lyric in all_alignment_lyrics:
        # I think this makes a copy and won't work as intended...
        if word_alignment.lower().endswith("in'"):
            word_alignment = word_alignment[:-1] + "g"

        return word_single, word_alignment



    # def _polish_alignmentlyrics(self, all_alignment_lyrics):

    #     for alignment_lyric in all_alignment_lyrics:

    #         # Copied from above:
    #         # ('word_original', ''),  # Includes apostrophe's, commas, and ()'s, e.g. "(bring", "one,", "Glancin'", "Jealousy!"
    #         # ('word_single', ''),    # Doesn't contain commas, ()'s, but keeps short-hand apostrophes, e.g. "bring", "one", "Glancin'"
    #         # ('word_alignment', ''), # Similar to word_single, except converts slangy words to full, e.g. "Glancing"

    #         word_single = alignment_lyric.word_original

    #         # Hyphens and spaces are handled already.
    #         characters_to_remove = [',', '!', '(', ')', '"']

    #         for char in characters_to_remove:
    #             word_single = word_single.replace(char, '')

    #         word_alignment = word_single

    #         # Fixing "in'" => "ing"
    #         #for a_lyric in all_alignment_lyrics:
    #         # I think this makes a copy and won't work as intended...
    #         if word_alignment.lower().endswith("in'"):
    #             word_alignment = word_alignment[:-1] + "g"

    #         alignment_lyric.word_single = word_single
    #         alignment_lyric.word_alignment = word_alignment


    def convert_aligmentlyrics_to_dict(self, all_lyrics):
        ''' Turning recordtype into python primitives
        '''

        # TODO: Update this text - it's not accurate anymore
        #   {
        #       lyric_full_sentence = "To the hip, the hippy"
        #       time_start = xxx.xxx,
        #       time_end = xxx.xxx,
        #       lyrics = [
        #           {
        #               word = "something",
        #               time_start = xxx.xxx,
        #               time_end = xxx.xxx
        #           },
        #           ...
        #       ]
        #
        #   }
        #
        #

        ready_to_export_lyrics = {
            "schema_version": self.json_schema_version,
            "lyric_lines": []
        }

        for lyric in all_lyrics:
            # Assemble into sentences again for entry into dict / strings
            
            if lyric.line_index == len(ready_to_export_lyrics["lyric_lines"]):

                lyric_line = {
                    "text": lyric.word_original,
                    "text": self._get_alignment_lyric_with_pre_post_chars(lyric),
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
                ready_to_export_lyrics["lyric_lines"][lyric.line_index]["text"] += self._get_alignment_lyric_with_pre_post_chars(lyric) 

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
    

    def _get_alignment_lyric_with_pre_post_chars(self, alignment_lyric):
        return alignment_lyric.word_original + alignment_lyric.word_split_char_post
