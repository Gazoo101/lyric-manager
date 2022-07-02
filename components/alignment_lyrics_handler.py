# Python
import re
from dataclasses import dataclass
from typing import List

# 3rd Party

# 1st Party


# AlignmentLyric is all data required to properly reassemble the full lyrics once the Aligner as processed the raw text.
@dataclass
class AlignmentLyric:
    word_original: str          = "" # Includes apostrophe's, commas, and ()'s, e.g. "(bring", "one,", "Glancin'", "Jealousy!"
    word_single: str            = "" # Doesn't contain commas, ()'s, but keeps short-hand apostrophes, e.g. "bring", "one", "Glancin'"
    word_alignment: str         = "" # Similar to word_single, except converts slangy words to full, e.g. "Glancing"
    word_split_char_pre: str    = "" # The pre-character that a lyric-word was split on. Most often a space " ", sometimes a hyphen "-"
    word_split_char_post: str   = "" # The pos-character that a lyric-word was split on. Most often a space " ", sometimes a hyphen "-"
    line_index: int             = -1
    time_start: float           = -1.0
    time_end: float             = -1.0


class AlignmentLyricsHandler():
    ''' A class to deal with all the conversions to and from AlignmentLyric struct(s).

    Explain more here!
    '''

    # perhaps not needed?
    def __init__(self, json_schema_version):
        self.json_schema_version = json_schema_version


    def convert_lyrics_raw_to_alignmentlyrics(self, lyrics: List[str]):
        '''

        Args:
            lyrics: A list of strings.
        
        Returns:
            A list of Alignment
        '''
        segmented_alignment_lyrics = self._split_lyrics_raw_spoken_segments(lyrics)

        self._polish_alignmentlyrics(segmented_alignment_lyrics)

        return segmented_alignment_lyrics
    

    def _split_lyrics_raw_spoken_segments(self, lyrics):
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

                        alignment_lyric = AlignmentLyric(
                            word_original=hyphened_word,
                            word_split_char_pre='-', # Add post-dash to all pieces. Remove the last one later.
                            word_split_char_post='-',
                            line_index=line_index
                        )

                        hyphenated_alignment_lyrics.append(alignment_lyric)
                    
                    hyphenated_alignment_lyrics[0].word_split_char_pre = ' '
                    hyphenated_alignment_lyrics[-1].word_split_char_post = ' '

                    spaced_alignment_lyrics.extend(hyphenated_alignment_lyrics)
                    continue

                alignment_lyric = AlignmentLyric(
                    word_original=spaced_word,
                    word_split_char_pre=' ', # Add post-dash to all pieces. Remove the last one later.
                    word_split_char_post=' ',
                    line_index=line_index
                )

                spaced_alignment_lyrics.append(alignment_lyric)

            spaced_alignment_lyrics[0].word_split_char_pre = ''
            spaced_alignment_lyrics[-1].word_split_char_post = ''

            segmented_alignment_lyrics.extend(spaced_alignment_lyrics)
        
        return segmented_alignment_lyrics


    def _polish_alignmentlyrics(self, all_alignment_lyrics):

        for alignment_lyric in all_alignment_lyrics:

            # Copied from above:
            # ('word_original', ''),  # Includes apostrophe's, commas, and ()'s, e.g. "(bring", "one,", "Glancin'", "Jealousy!"
            # ('word_single', ''),    # Doesn't contain commas, ()'s, but keeps short-hand apostrophes, e.g. "bring", "one", "Glancin'"
            # ('word_alignment', ''), # Similar to word_single, except converts slangy words to full, e.g. "Glancing"

            word_single = alignment_lyric.word_original

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

            alignment_lyric.word_single = word_single
            alignment_lyric.word_alignment = word_alignment


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
