# Python
import os
from enum import Enum
from pathlib import Path
import json
import logging
#from posix import POSIX_FADV_NOREUSE
import re
from collections import namedtuple

# 3rd Party
from recordtype import recordtype

# 1st Party

# Pure timing
WordAndTiming = namedtuple("WordAndTiming", ["word", "time_start", "time_end"])

# More complete word
Lyric = recordtype('Lyric', [('word', ''), ('line_index', -1), ('time_start', -1.0), ('time_end', -1.0)])

# 2nd iteration which contains 3 variants of word:
# 1. Full original which includes apostrophe's, commas, and ()'s, e.g. "(bring", "one,", "Glancin'", "Jealousy!"
# 2. Single word render friendly which removes commas, ()'s, but keeps short-hand apostrophes, e.g. "bring", "one", "Glancin'"
# 3. Alignment friendly - similar to single word render, except converts slangy words to full, e.g. "Glancing"
LyricV2 = recordtype('Lyric',
    [
        ('word_original', ''),
        ('word_single', ''),
        ('word_alignment', ''),
        ('line_index', -1), 
        ('time_start', -1.0),
        ('time_end', -1.0)
    ]
)

class LyricManager:

    def __init__(self, all_lyric_fetchers, lyric_aligner):
        # The version of aligned lyrics json the LyricManager will export to.
        # A simple, but imperfect, approach to ensure readers of the lyric data
        # won't be surprised or unexpectedly broken.
        self.json_schema_version = "1.0.0"

        self.all_lyric_fetchers = all_lyric_fetchers
        self.lyric_aligner = lyric_aligner

    def _percentage(self, part, whole):
        return 100 * float(part)/float(whole)

    def _get_all_audio(self, path, recursive):

        all_audio_files = []

        if recursive:
            all_files = os.walk(path)

            for dirpath, dirnames, filenames in all_files:
                audio_files_in_dir = [Path(dirpath) / filename for filename in filenames if filename.endswith("mp3")]
                all_audio_files.extend(audio_files_in_dir)
        else:
            all_audio_files = [Path(entry.path) for entry in os.scandir(path) if entry.name.endswith("mp3")]

        return all_audio_files

    def _remove_non_lyrics(self, lyrics):
        ''' Returns a list of sanitized lyric strings.

        Each string in the list represents a single coheasive sung sentence. This is used during
        visualization to cohesively visualize sentances.
        '''
        # Lyrics are provided in a single large string

        # 1. Reformat string into per-line for easier human manipulation
        all_lyric_lines = lyrics.splitlines()

        

        sanitized_lyric_lines = []

        for lyric_line in all_lyric_lines:
            # Removes [<any content, except newlines>]
            #complete_lyric_string = re.sub(r"\[.*\]", '', complete_lyric_string)
            lyric_line = re.sub(r"\[[a-zA-Z0-9 -]*\]", '', lyric_line)

            sanitized_lyric_lines.append(lyric_line)

        # Removes empty lines
        non_empty_lyric_lines = [lyric_line for lyric_line in sanitized_lyric_lines if lyric_line]


        # complete_lyric_string = ' '.join(non_empty_lyric_lines)

        # # Removes [<any content, except newlines>]
        # #complete_lyric_string = re.sub(r"\[.*\]", '', complete_lyric_string)
        # complete_lyric_string = re.sub(r"\[[a-zA-Z0-9 -]*\]", '', complete_lyric_string)

        # # Remove double-spaces
        # complete_lyric_string = ' '.join(complete_lyric_string.split())

        return non_empty_lyric_lines


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
        words_structure = [x.word for x in lyrics_structured_better_display]

        # TODO: Fix case index_offset > display_range
        words_timing[0] = f">{words_timing[0]}<"
        words_structure[index_offset] = f">{words_structure[index_offset]}<"
        words_structure.insert(mismatch_tolerance, "]")
        
        td = " ".join(words_timing)
        sd = " ".join(words_structure)

        print("-- Lyric Matching --")
        print(f"Time aligned:  {td}")
        print(f"Structured:  [ {sd}")


    def _create_lyric_v2(self, word_original, line_index):

        word_single=word_original

        characters_to_remove = [',', '!', '(', ')']

        for char in characters_to_remove:
            word_single = word_single.replace(char, '')

        word_alignment=word_single
        if word_single.lower().endswith("in'"):
            word_alignment = word_alignment[:-1] + "g"
        
        return LyricV2(word_original=word_original, word_single=word_single, word_alignment=word_alignment, line_index=line_index)


    def _convert_lyrics_to_lyrics_v2(self, lyrics):
        '''

        Args:
            lyrics: A list of strings.
        '''
        lyrics_structured_better = []

        for line_index, lyric_line in enumerate(lyrics):

            lyric_line_parts = lyric_line.split(' ')

            for word in lyric_line_parts:

                lyrics_structured_better.append( self._create_lyric_v2(word, line_index) )

        return lyrics_structured_better


    # def _convert_lyric_sentences_to_stuctured_words(self, lyrics_structured):
    #     ''' Converts a list of strings into a list individual words wrapped in recordtype. '''
    #     lyrics_structured_better = []

    #     for line_index, lyric_line in enumerate(lyrics_structured):

    #         lyric_line_parts = lyric_line.split(' ')

    #         for word_index, word in enumerate(lyric_line_parts):

    #             lyrics_structured_better.append( Lyric(word=word, line_index=line_index) )

    #     return lyrics_structured_better


    def _match_aligned_lyrics_with_structured_lyrics(self, lyrics_time_aligned, lyrics_structured, debug_print=False):
        ''' Matches time aligned lyrics with (sentance) structured lyrics.

        Aligned lyrics and structured lyrics rarely match exactly. This function uses a moving
        expanding/contracting window in order to find the best structured lyric, for each aligned
        lyric.

        The algorithm will assume that the time aligned lyrics is the more sparse data, and use
        it for the main for-loop. As the structured lyrics are scanned for a match, a window is
        used within which to do a forward-search. If a match isn't found within the window, the
        time aligned lyric is skipped and the window expands. Every time a match if found, the
        window shrinks.

        '''

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

                # Fix out of range...
                lsb = lyrics_structured[lsb_index + index_offset]

                #print(f"Matching {wat.word.lower()} against {lsb.word.lower()} ")

                # Todo: Improve word-to-word comparisson 
                if wat.word.lower() == lsb.word_alignment.lower():
                    #lsb_mismatch_count = 0
                    lyrics_structured[lsb_index].time_start = wat.time_start
                    lyrics_structured[lsb_index].time_end = wat.time_end

                    

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
        matched_percentage = self._percentage(total_matched, num_time_aligned_lyrics)
        logging.info(f"Successfully matched words: {matched_percentage:.2f}% ({total_matched} / {num_time_aligned_lyrics}) ")

        return lyrics_structured


    
    def _verify_lyrics(self, lyrics_stuctured, lyrics_timing):
        '''

        It's unknown how broken or un-matched lyrics are going to be, so for now,
        let's just verify that every single word has timing.
        
        '''

        lt_iter = iter(lyrics_timing)

        for line_index, lyric_line in enumerate(lyrics_stuctured):

            lyric_line_parts = lyric_line.split(' ')

            for word_index, word in enumerate(lyric_line_parts):

                lyric_timed = next(lt_iter)

                word1 = lyric_timed.word.lower()
                word2 = word.lower()

                if word1 != word2:
                    print(f"Mismatch on Line {line_index}, Word {word_index}: {lyric_line}")
                    print(f"Word from original lyrics: {word2} | Timed Lyric: {word1}")
                    # Lyric doesn't match :/

    
    def _convert_lyric_recordtype_to_dict(self, all_lyrics):
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

        #lyrics_to_return = []

        for lyric in all_lyrics:
            # Assemble into sentences again for entry into dict / strings
            
            if lyric.line_index == len(ready_to_export_lyrics["lyric_lines"]):

                lyric_line = {
                    "text": lyric.word_original,
                    "time_start": lyric.time_start,
                    "time_end": lyric.time_end,
                    "lyric_words": [{
                        "original": lyric.word_original,
                        "single": lyric.word_single,
                        "time_start": lyric.time_start,
                        "time_end": lyric.time_end
                    }]
                }

                ready_to_export_lyrics["lyric_lines"].append(lyric_line)
                #lyrics_to_return.append(lyric_line)
            else:
                ready_to_export_lyrics["lyric_lines"][lyric.line_index]["text"] += " " + lyric.word_original
                ready_to_export_lyrics["lyric_lines"][lyric.line_index]["time_end"] = lyric.time_end
                ready_to_export_lyrics["lyric_lines"][lyric.line_index]["lyric_words"].append({
                    "original": lyric.word_original,
                    "single": lyric.word_single,
                    "time_start": lyric.time_start,
                    "time_end": lyric.time_end
                })
            
        return ready_to_export_lyrics


    def _create_lyrics_json(self, time_aligned_lyrics, lyrics_stuctured):

        #lyrics_structured -> Reveals how lyrics form complete sentences

        #lyrics_timing -> Reveals when each of the word from the lyrics fit together

        # Periods are missing from the timing
        # apostophes appear to be present

        lyrics_structured_aligned = self._match_aligned_lyrics_with_structured_lyrics(time_aligned_lyrics, lyrics_stuctured)

        # recordtype can't be auto-converted to json, so we must turn it into a dict
        lyrics_json = self._convert_lyric_recordtype_to_dict(lyrics_structured_aligned)

        return lyrics_json


    def _string_list_to_string(self, string_list):
        ''' Converts a list of strings into a single string without double spaces. '''
        string = ' '.join(string_list)
        return ' '.join(string.split())


    def fetch_and_align_lyrics(self, path_to_audio, recursive=False, destructive=False, keep_lyrics=False, export_readable_json=False):
        ''' Fetches the things, and writes them down

        '''
        audio_files = self._get_all_audio(path_to_audio, recursive)

        logging.info(f"Found {len(audio_files)} to process.")

        # Filter for existing lyric files here

        # Blur generally ok - skip first
        #audio_files = audio_files[1:]

        json_out_fds = {}

        # To pull out and test one song
        #audio_files = [audio_files[5]]

        for audio_file in audio_files:
            logging.info(f"Processing: {audio_file}")

            lyrics_raw = None

            for lyric_fetcher in self.all_lyric_fetchers:

                lyrics_raw = lyric_fetcher.fetch_lyrics(audio_file)

                if lyrics_raw:
                    break

            if not lyrics_raw:
                logging.warn("Unable to retrieve lyrics.")
                continue

            # Clears non-lyric content like [verse 1] and empty lines
            lyrics_sanitized = self._remove_non_lyrics(lyrics_raw)

            lyrics_v2 = self._convert_lyrics_to_lyrics_v2(lyrics_sanitized)

            lyrics_alignment_ready = []

            for lyric in lyrics_v2:
                lyrics_alignment_ready.append(lyric.word_alignment)

            # ["line 1", "line 2", ... "line n"] -> "line 1 line 2 ... line n"
            complete_lyric_string = self._string_list_to_string(lyrics_alignment_ready)

            lyric_sanitized_file = audio_file.with_suffix(".lyrics_sanitized")

            with open(lyric_sanitized_file, 'wt') as file:
                file.write(complete_lyric_string)

            # TODO: Write intermediate lyric file on-disk for aligner tool to use
            #intermediate_lyric_file = "path"

            # Hard-coded for 'Go-go's vacation' currently
            time_aligned_lyrics = self.lyric_aligner.align_lyrics(audio_file, lyric_sanitized_file, use_preexisting=False)
            #time_aligned_lyrics = self.lyric_aligner.align_lyrics(audio_file, lyric_sanitized_file, use_preexisting=True)

            json_to_write = self._create_lyrics_json(time_aligned_lyrics, lyrics_v2)

            path_to_json_lyrics_file = audio_file.with_suffix(".aligned_lyrics")

            # # horsie2 = 2

            # # lyrics = self.lyric_fetcher.fetch_lyrics("The Go-Go's", "Vacation")

            # json_out_fds["debug_meta_lyrics"] = lyrics

            with open(path_to_json_lyrics_file, 'w') as file:
                if export_readable_json:
                    json.dump(json_to_write, file, indent=4)
                else:
                    json.dump(json_to_write, file)

            logging.info(f"Wrote aligned lyrics file: {path_to_json_lyrics_file}")



            hello = 2