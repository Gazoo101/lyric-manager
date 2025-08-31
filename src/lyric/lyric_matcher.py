# Python
import os
import re
import logging


# 3rd Party


# 1st Party
from .dataclasses_and_types.lyric_match import MatchLyric
from .dataclasses_and_types.lyric_match import MatchResult
from ..lyric.aligners import WordAndTiming


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


    def convert_lyrics_string_to_match_lyrics(self, lyrics: list[str]):
        """

        Args:
            lyrics: A list of strings.
        
        Returns:
            A list of Alignment
        """
        all_match_lyrics: list[MatchLyric] = self._split_lyrics_raw_spoken_segments(lyrics)

        for match_lyric in all_match_lyrics:
            word_single, word_alignment_ready = self._create_standalone_and_alignment_ready_word(match_lyric)

            match_lyric.word_single = word_single
            match_lyric.word_alignment = word_alignment_ready


        #self._polish_alignmentlyrics(segmented_alignment_lyrics)

        return all_match_lyrics
    

    def _split_lyrics_raw_spoken_segments(self, lyrics: list[str]):
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


    def match_aligned_lyrics_with_structured_lyrics(self,
        lyrics_time_aligned: list[WordAndTiming],
        lyrics_structured: list[MatchLyric],
        debug_print=False) -> tuple[list[MatchLyric], MatchResult]:
        """ Matches time aligned lyrics with (sentance) structured lyrics.

        Aligned lyrics and structured lyrics rarely match exactly. This function uses a moving
        expanding/contracting window in order to find the best structured lyric, for each aligned
        lyric.

        The algorithm will assume that the time aligned lyrics is the more sparse data, and use
        it for the main for-loop. As the structured lyrics are scanned for a match, a window is
        used within which to do a forward-search. If a match isn't found within the window, the
        time aligned lyric is skipped and the window expands. Every time a match if found, the
        window shrinks.

        Args:
            - TODO:
        Returns:
            List[MatchLyric] - List of structure lyrics now with timing information

        """

        #debug_print = True

        # We'd like to easily iterate through each structured lyric word, so we'll transform the
        # the list of strings (in lyrics_structured) into a long list of recordtypes, each with
        # a start / stop time, and a line

        #lyrics_structured_better = self._convert_lyric_sentences_to_stuctured_words(lyrics_structured)

        # Step 1. Process lyrics_structured to befit the incoming lyrics_timing.
        # E.g. NUSAutoAlignLyrix removes ()'s and appears to perhaps not match "'em" so it should
        # be replaced with 'them' (before processing though)

        # Step 2. For each timed lyric, find the 'best' match

        # Iterate though each timed lyric
        # - Use fuzzy wuzzy to find 'match of word' vs word given in timing
        #   - For now - expect exact match
        #   - If a match is no-go, there should be 2 types of tolerances
        #       1. When holding a timed lyric, how far can we skip through the structured to find a match? (start with 3)
        #       2. Assuming the limit for 1. is hit (e.g. no match within the next 3 words), how many times
        #       can we timed lyrices are we allowed to not match. (start with 3)
        #   - Reset each of these as the work through the lyrics

        # We assumed that timed lyrics may not precisely fit the structured lyrics, specifically:
        # - A structured lyric word may not appear in the timed lyrics
        #   - Either because the input lyrics to align were bunk, or
        #   - because the lyric alignment algorithm failed to properly match the word
        # - Timed lyric may include words that don't match a lyric
        #   - NUSAutoAlignLyrix includes a 'Breath*' word that should either be
        #       - Matched to a proper word the algorithm mistakenly thought was a breath
        #       - Removed as we don't really want to display 'Breath*'...?
         
        # Matching the timed lyrics to structured lyrics is centered around the timed lyrics -
        # i.e. we iterate over the timed lyrics as that is likely the more sparse data
         
        # wat -> word and timing
        lsb_index = 0

        total_unmatched = 0

        # Growing / Shrinking tolerance window works well with BLUR - Boys & Girls
        min_mismatch_tolerance = 3
        current_mismatch_tolerance = min_mismatch_tolerance

        for wat_index, wat in enumerate(lyrics_time_aligned):

            failed_to_match = False

            match_span = min(len(lyrics_structured) - lsb_index, current_mismatch_tolerance)
            for index_offset in range(match_span):

                if debug_print:
                    self._debug_print(lyrics_time_aligned, wat_index, lyrics_structured, lsb_index, index_offset, current_mismatch_tolerance)
                    input("Press Enter to continue...")

                # Fix out of range...
                lsb = lyrics_structured[lsb_index + index_offset]

                #print(f"Matching {wat.word.lower()} against {lsb.word.lower()} ")

                # Todo: Improve word-to-word comparisson 
                if wat.word.lower() == lsb.word_alignment.lower():
                    #lsb_mismatch_count = 0
                    lyrics_structured[lsb_index + index_offset].time_start = wat.time_start
                    lyrics_structured[lsb_index + index_offset].time_end = wat.time_end

                    # If we find a 'later' match, we must move the lsb_index forward by the offset
                    # otherwise, it'll keep falling behind
                    lsb_index += index_offset
                    
                    break
                else:
                    #lsb_mismatch_count += 1
                    horse = 456
                
                if index_offset == match_span-1:
                    failed_to_match = True

                #self._debug_print(lyrics_time_aligned, wat_index, lyrics_structured_better, lsb_index, index_offset, current_mismatch_tolerance)

            if failed_to_match:
                logging.debug(f"Failed to match a word: {wat.word:10} | wat_index: {wat_index:3} | lsb_index: {lsb_index:3}")
                # Given that the timed lyrics are always expected to be more sparse, than
                # the structured ones, if a match fails, it 'should' be ok to move the lsb_index
                # ahead. See how we go re. this change.
                #lsb_index += 1
                current_mismatch_tolerance += 1
                total_unmatched += 1
            else:
                current_mismatch_tolerance = max(min_mismatch_tolerance, current_mismatch_tolerance-1)
                lsb_index += 1

        num_time_aligned_lyrics = len(lyrics_time_aligned)
        total_matched = num_time_aligned_lyrics - total_unmatched

        match_result = MatchResult(num_time_aligned_lyrics, total_matched)

        return lyrics_structured, match_result


    def _debug_print(self, lyrics_timing, wat_index, lyrics_structured_better, lsb_index, index_offset, mismatch_tolerance):
        ''' Prints time aligned and structured lyrics on to console for easy debugging.

        Example:
            -- Lyric Matching --
            Time aligned:  >STREETS< LIKE A JUNGLE SO CALL THE POLICE FOLLOWING THE HERD DOWN
            Structured:  [ >Streets< like a ] jungle So call the police Following the herd Down
        '''
        display_range = 12  # How large a range to 
        os.system('cls')

        lyrics_timing_display = lyrics_timing[wat_index:wat_index+display_range]
        words_timing = [x.word for x in lyrics_timing_display]

        lyrics_structured_better_display = lyrics_structured_better[lsb_index:lsb_index+display_range]
        words_structure = [x.word_alignment for x in lyrics_structured_better_display]

        # TODO: Fix case index_offset > display_range
        words_timing[0] = f">{words_timing[0]}<"
        words_structure[index_offset] = f">{words_structure[index_offset]}<"
        words_structure.insert(mismatch_tolerance, "]")
        
        td = " ".join(words_timing)
        sd = " ".join(words_structure)

        print("-- Lyric Matching --")
        print(f"Time aligned:  {td}")
        print(f"Structured:  [ {sd}")