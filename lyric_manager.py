# Python
import os
from pathlib import Path
import json
import logging

# 3rd Party
from tqdm.contrib.logging import logging_redirect_tqdm
import tqdm

# 1st Party
from components import AlignmentLyricsHandler
from components import FileOutputLocation
from components import AudioLyricAlignTask
from components import LyricSanitizer


class LyricManager:

    def __init__(self, all_lyric_fetchers, lyric_aligner):
        # The version of aligned lyrics json the LyricManager will export to.
        # A simple, but imperfect, approach to ensure readers of the lyric data
        # won't be surprised or unexpectedly broken.

        # MAJOR version when you make incompatible API changes,
        # MINOR version when you add functionality in a backwards compatible manner, and
        # PATCH version when you make backwards compatible bug fixes.
        self.json_schema_version = "2.0.0"

        self.alignment_lyrics_handler = AlignmentLyricsHandler(self.json_schema_version)

        self.all_lyric_fetchers = all_lyric_fetchers
        self.lyric_aligner = lyric_aligner
        self.lyric_sanitizer = LyricSanitizer()

        self.extension_alignment_ready = ".alignment_ready"


    def _percentage(self, part, whole):
        return 100 * float(part)/float(whole)


    def _get_all_audio_files(self, path, recursive):

        all_audio_files = []

        if recursive:
            for dirpath, dirnames, filenames in os.walk(path):
                audio_files_in_dir = [Path(dirpath) / filename for filename in filenames if filename.endswith("mp3")]
                all_audio_files.extend(audio_files_in_dir)
        else:
            all_audio_files = [Path(entry.path) for entry in os.scandir(path) if entry.name.endswith("mp3")]

        # os.walk() apparently returns files in an arbitrary order. For clarity/debugging, we prefer they are sorted
        # by name 
        audio_files_in_dir = sorted(audio_files_in_dir)

        return all_audio_files

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


    def _string_list_to_string(self, string_list):
        ''' Converts a list of strings into a single string without double spaces. '''
        string = ' '.join(string_list)
        return ' '.join(string.split())


    # TODO: Convert to dataclass and implement method chaining
    def fetch_and_align_lyrics(self,
            path_to_audio:Path, 
            recursive=False, 
            destructive=False, 
            keep_lyrics=False, 
            export_readable_json=False,
            use_preexisting_files=True,
            file_output_location=FileOutputLocation.NextToAudioFile,
            file_output_path:Path=None):
        """ Fetches and aligns lyrics using various external modules.

        Args:
            path_to_audio:
            recursive:
            destructive: N/A
            keep_lyrics: N/A
            export_readable_json:
            use_preexisting_files:
            file_output_locations:
            file_output_path:
        """

        # This should probably occur in the LyricManager constructor!
        if file_output_path:
            file_output_path.mkdir(exist_ok=True)


        all_audio_files = self._get_all_audio_files(path_to_audio, recursive)

        logging.info(f"Found {len(all_audio_files)} to process.")

        # Filter for existing lyric files here

        # Blur generally ok - skip first
        #audio_files = audio_files[1:]

        json_out_fds = {}

        # To pull out and test one song
        #audio_files = [audio_files[5]]



        
        # For design purposes we opt to break the loop into per-task loops. Makes the code easier to
        # follow, as well as making it easier to focus on fixing and debugging all issues pertaining
        # to a particular functionality.

        with logging_redirect_tqdm():

            # AudioLyricAlignTask() will throw exceptions in the case of unexpected filenames
            lyric_align_tasks = []
            for path_to_audio_file in all_audio_files:
                try:
                    task = AudioLyricAlignTask(path_to_audio_file)
                    lyric_align_tasks.append(task)
                except IndexError:
                    logging.warning(f"The audio filename: '{path_to_audio_file}' was malformed.")
                except:
                    logging.exception(f"Unable to convert '{path_to_audio_file}' into Task object.")
                    

            # AudioLyticAlign == ala
            lyric_align_tasks_valid = []

            for ala_task in tqdm.tqdm(lyric_align_tasks, desc="Fetching lyrics"):

                for lyric_fetcher in self.all_lyric_fetchers:

                    # Fetcher currently writes previously fetched copies to disk. This should perhaps
                    # be elevated/exposed to this level.
                    ala_task.lyric_text_raw = lyric_fetcher.fetch_lyrics(ala_task)

                    if ala_task.lyric_text_raw:
                        break

                if not ala_task.lyric_text_raw:
                    logging.warning(f"Unable to retrieve lyrics for: {ala_task.path_to_audio_file}")
                    continue

                lyric_align_tasks_valid.append(ala_task)

            for ala_task in tqdm.tqdm(lyric_align_tasks_valid, desc="Sanitizing lyrics"):
                lyrics = ala_task.lyric_text_raw

                # lyricgenius now returns some garbage-data in the lyrics we must clean up
                lyrics = self.lyric_sanitizer.remove_leading_title(ala_task.song_name, lyrics)
                lyrics = self.lyric_sanitizer.remove_embed_at_end(lyrics)

                # Clears non-lyric content like [verse 1] and empty lines
                lyrics = self.lyric_sanitizer.remove_non_lyrics(lyrics)
                lyrics = self.lyric_sanitizer.replace_difficult_characters(lyrics)

                ala_task.lyric_text_sanitized = lyrics

            for ala_task in tqdm.tqdm(lyric_align_tasks_valid, desc="Align lyrics"):

                # Most of this is to make the task of matching timing back to words a lot easier.
                alignment_lyrics = self.alignment_lyrics_handler.convert_lyrics_raw_to_alignmentlyrics(ala_task.lyric_text_sanitized)

                lyrics_alignment_ready = []

                for lyric in alignment_lyrics:
                    lyrics_alignment_ready.append(lyric.word_alignment)

                # ["line 1", "line 2", ... "line n"] -> "line 1 line 2 ... line n"
                complete_lyric_string = self._string_list_to_string(lyrics_alignment_ready)

                path_to_alignment_ready_file = ala_task.path_to_audio_file.with_suffix(self.extension_alignment_ready)

                if file_output_path:
                    path_to_alignment_ready_file = file_output_path / path_to_alignment_ready_file.name

                with open(path_to_alignment_ready_file, 'wt') as file:
                    file.write(complete_lyric_string)

                # TODO: Write intermediate lyric file on-disk for aligner tool to use
                #intermediate_lyric_file = "path"

                # Hard-coded for 'Go-go's vacation' currently
                time_aligned_lyrics = self.lyric_aligner.align_lyrics(
                    ala_task.path_to_audio_file,
                    path_to_alignment_ready_file,
                    use_preexisting=use_preexisting_files
                )
                #time_aligned_lyrics = self.lyric_aligner.align_lyrics(audio_file, lyric_sanitized_file, use_preexisting=True)

                #json_to_write = self._create_lyrics_json(time_aligned_lyrics, alignment_lyrics)

                lyrics_structured_aligned = self._match_aligned_lyrics_with_structured_lyrics(time_aligned_lyrics, alignment_lyrics)

                # recordtype can't be auto-converted to json, so we must turn it into a dict
                #lyrics_json = self._convert_lyric_recordtype_to_dict(lyrics_structured_aligned)
                json_to_write = self.alignment_lyrics_handler.convert_aligmentlyrics_to_dict(lyrics_structured_aligned)

                path_to_json_lyrics_file = ala_task.path_to_audio_file.with_suffix(".aligned_lyrics")

                if file_output_path:
                    path_to_json_lyrics_file = file_output_path / path_to_json_lyrics_file.name

                # # horsie2 = 2

                # # lyrics = self.lyric_fetcher.fetch_lyrics("The Go-Go's", "Vacation")

                # json_out_fds["debug_meta_lyrics"] = lyrics

                with open(path_to_json_lyrics_file, 'w') as file:
                    if export_readable_json:
                        json.dump(json_to_write, file, indent=4)
                    else:
                        json.dump(json_to_write, file)

                logging.info(f"Wrote aligned lyrics file: {path_to_json_lyrics_file}")

