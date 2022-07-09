# Python
import os
import json
import logging
from pathlib import Path
from datetime import datetime

# 3rd Party
from tqdm.contrib.logging import logging_redirect_tqdm
import tqdm

# 1st Party
from components import LyricMatcher
from components import FileOutputLocation
from components import AudioLyricAlignTask
from components import LyricValidity
from components import percentage
from lyric_aligner import WordAndTiming
from lyric_fetcher import LyricFetcherInterface
from components.lyric_matcher import MatchResult



class LyricManager:
    """ Facilitates a multi-step process to turn an audio file and lyric text, into a .json file with lyric timing info.

    The process is broken down into the following steps:
        - Fetch     - Acquiring lyrics from local .txt file or alternate source.
        - Validate  - Check if lyrics appear to match song. Typically only needed for alternate sources of lyrics.
        - Sanitize  - Clean up fetched and validated lyrics, removing non-lyric data (e.g [Chorus])
        - Pre-alignment process - Create intermediate data allowing for time aligned lyrics to be more easily matched
            to the sanitized (and more structured) lyrics.
        - Alignment - Determines start and end time for each word in the songs lyrics.
        - Post-alignment match - Matches the time-aligned words to the structured and validated lyrics using the
            created intermediate data.

    TODO: Expand on details as to which classes assist in which part of the process.
    """

    def __init__(self, all_lyric_fetchers, lyric_aligner):

        self.all_lyric_fetchers = all_lyric_fetchers
        self.lyric_aligner = lyric_aligner

        # The version of aligned lyrics json the LyricManager will export to.
        # A simple, but imperfect, approach to ensure readers of the lyric data
        # won't be surprised or unexpectedly broken.

        # MAJOR version when you make incompatible API changes,
        # MINOR version when you add functionality in a backwards compatible manner, and
        # PATCH version when you make backwards compatible bug fixes.
        self.json_schema_version = "2.0.0"

        self.lyric_matcher = LyricMatcher(self.json_schema_version)

        self.extension_alignment_ready = ".alignment_ready"

        self.recognized_audio_filename_extensions = ["mp3", "wav", "aiff"]

    def _valid_audio_extension(self, filename: str):
        for extension in self.recognized_audio_filename_extensions:
            if filename.endswith(extension):
                return True
        
        return False


    def _get_audio_files_found_in_paths(self, all_paths: list[Path], recursive: bool):

        all_audio_files = []

        for path in all_paths:

            audio_files_in_path = []

            if recursive:
                for dirpath, dirnames, filenames in os.walk(path):
                    audio_files_in_dir = [Path(dirpath) / filename for filename in filenames if self._valid_audio_extension(filename)]
                    audio_files_in_path.extend(audio_files_in_dir)
            else:
                audio_files_in_path = [Path(entry.path) for entry in os.scandir(path) if entry.name.endswith("mp3")]

            # os.walk() apparently returns files in an arbitrary order. For clarity/debugging, we prefer they are sorted
            # by name 
            audio_files_in_path = sorted(audio_files_in_path)

            all_audio_files.extend(audio_files_in_path)

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


    def _create_audio_lyric_align_tasks_from_paths(self, paths_to_audio_files: list):
        """ Turns a list of paths to audio files into AudioLyricAlignTask objects """
        lyric_align_tasks = []

        for path_to_audio_file in paths_to_audio_files:
            try:
                # If the audio filename cannot be properly decomposed into Artist - Song, the constructor will throw
                task = AudioLyricAlignTask(path_to_audio_file)
                lyric_align_tasks.append(task)
            except IndexError:
                logging.warning(f"The audio filename: '{path_to_audio_file}' was malformed.")
            except:
                logging.exception(f"Unable to convert '{path_to_audio_file}' into Task object.")

        return lyric_align_tasks


    def _fetch_and_sanitize_lyrics(self, lyric_align_task: AudioLyricAlignTask):
        """ For a given AudioLyricAlignTask, fetches lyrics using available sources in self.all_lyric_fetchers.
        
        The order of the lyric fetches matters as function will accept the first valid source available.
        """
        lyric_fetcher: LyricFetcherInterface
        lyric_text_raw: str
        lyric_validity: LyricValidity
        for lyric_fetcher in self.all_lyric_fetchers:

            # Fetcher currently writes previously fetched copies to disk. This should perhaps
            # be elevated/exposed to this level.
            lyric_text_raw, lyric_validity = lyric_fetcher.fetch_lyrics(lyric_align_task)

            # Source of lyrics found
            if lyric_text_raw:
                break

        if not lyric_text_raw:
            logging.warning(f"No lyric source found for: {lyric_align_task.path_to_audio_file}")
            return lyric_align_task
        
        lyric_align_task.lyric_text_raw = lyric_text_raw
        lyric_align_task.lyric_validity = lyric_validity

        if lyric_validity is not LyricValidity.Valid:
            logging.warning(f"Non-valid lyrics found for: {lyric_align_task.path_to_audio_file}. Will not sanitize.")
            return lyric_align_task

        lyric_align_task.lyric_text_sanitized = lyric_fetcher.sanitize_raw_lyrics(lyric_align_task)

        return lyric_align_task

    
    def _align_lyrics(self, lyric_align_task: AudioLyricAlignTask, file_output_path: Path, use_preexisting_files: bool):
        """A class for a user

        Args:
            - lyric_align_task -- The AudioLyricAlignTask to align, relies primarily on the .lyric_text_sanitized property.
            - file_output_path -- Folder into which the output should be produced.
            - use_preexisting_files -- ??? Not sure this is even currently respected.
        Returns:
            The same AudioLyricAlignTask object. Should probably be changed to return True/False for success.
        """

        # Most of this is to make the task of matching timing back to words a lot easier.
        alignment_lyrics = self.lyric_matcher.convert_lyrics_string_to_match_lyrics(lyric_align_task.lyric_text_sanitized)

        lyrics_alignment_ready = []

        for lyric in alignment_lyrics:
            lyrics_alignment_ready.append(lyric.word_alignment)

        # ["line 1", "line 2", ... "line n"] -> "line 1 line 2 ... line n"
        complete_lyric_string = self._string_list_to_string(lyrics_alignment_ready)

        path_to_alignment_ready_file = lyric_align_task.path_to_audio_file.with_suffix(self.extension_alignment_ready)

        if file_output_path:
            path_to_alignment_ready_file = file_output_path / path_to_alignment_ready_file.name

        with open(path_to_alignment_ready_file, 'wt') as file:
            file.write(complete_lyric_string)

        # TODO: Write intermediate lyric file on-disk for aligner tool to use
        #intermediate_lyric_file = "path"

        time_aligned_lyrics: list[WordAndTiming] = self.lyric_aligner.align_lyrics(
            lyric_align_task.path_to_audio_file,
            path_to_alignment_ready_file,
            use_preexisting=use_preexisting_files
        )

        lyrics_structured_aligned, match_result = self.lyric_matcher.match_aligned_lyrics_with_structured_lyrics(time_aligned_lyrics, alignment_lyrics)
        logging.info(f"Successfully matched words: {match_result.get_string()})")

        lyric_align_task.match_result = match_result

        # For later Json output, we must convert the dataclasses to Python-native dicts
        lyric_align_task.lyrics_aligned = self.lyric_matcher.convert_aligmentlyrics_to_dict(lyrics_structured_aligned)

        return lyric_align_task


    def _write_aligned_lyrics_to_disk(self,
        lyric_align_task: AudioLyricAlignTask,
        file_output_path: Path,
        export_readable_json: bool):
        """ TODO """
        
        path_to_json_lyrics_file = lyric_align_task.path_to_audio_file.with_suffix(".aligned_lyrics")

        if file_output_path:
            path_to_json_lyrics_file = file_output_path / path_to_json_lyrics_file.name

        # # lyrics = self.lyric_fetcher.fetch_lyrics("The Go-Go's", "Vacation")

        # json_out_fds["debug_meta_lyrics"] = lyrics

        with open(path_to_json_lyrics_file, 'w') as file:
            if export_readable_json:
                json.dump(lyric_align_task.lyrics_aligned, file, indent=4)
            else:
                json.dump(lyric_align_task.lyrics_aligned, file)

        logging.info(f"Wrote aligned lyrics file: {path_to_json_lyrics_file}")

    def _print_lyric_validity(self, lyric_align_tasks: list[AudioLyricAlignTask]):
        logging.info("**********************************************************************")
        logging.info("************************* Lyric Validity *****************************")
        for task in lyric_align_tasks:
            logging.info(f"{task.song_name[0:50] : <50} | {task.lyric_validity}")

    # TODO: Convert to dataclass and implement method chaining
    def fetch_and_align_lyrics(self,
            paths_to_process:list[Path], 
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

        paths_to_process_valid = []
        for path in paths_to_process:
            if not path.exists():
                logging.info(f"Provided path to process '{path}' not found. Skipping it.")

            paths_to_process_valid.append(path)


        all_audio_files = self._get_audio_files_found_in_paths(paths_to_process, recursive)

        logging.info(f"Found {len(all_audio_files)} to process.")

        tasks = self._create_audio_lyric_align_tasks_from_paths(all_audio_files)



        # Design commentary:
        # Tasks are deliberately encapsulated into multiple functionally independent loops, as opposed to undertaking
        # all activities per-song in one giant loop. Because:
        #   - The code is easier to maintain - different types of functionality breaks differently.
        #   - Debugging can be more easily focused on one single failing functionality
        #   - Further encapsulation is simpler.

        tasks_with_lyrics = []
        tasks_with_lyrics_valid = []

        with logging_redirect_tqdm():
            for task in tqdm.tqdm(tasks, desc="Fetching, validating, and sanitizing lyrics"):
                task_with_lyrics = self._fetch_and_sanitize_lyrics(task)
                tasks_with_lyrics.append(task_with_lyrics)

            # Report on lyric validity
            self._print_lyric_validity(tasks_with_lyrics)

            # For now we only keep (probably) valid lyrics
            tasks_with_lyrics_valid = [task for task in tasks_with_lyrics if task.lyric_validity == LyricValidity.Valid]

            # Move to end
            #self._print_aligned_lyrics_report(tasks_with_lyrics, tasks_with_lyrics_valid)

            # Because lyric alignment is fairly time-consuming (~0.5 minute processing per 1 minute audio), we write the
            # results to disk in the same loop to ensure nothing is lost in case of unexpected errors.
            for task in tqdm.tqdm(tasks_with_lyrics_valid, desc="Align lyrics"):
                lyric_align_task = self._align_lyrics(task, file_output_path, use_preexisting_files)

                self._write_aligned_lyrics_to_disk(lyric_align_task, file_output_path, export_readable_json)

            self._print_aligned_lyrics_report(tasks_with_lyrics, tasks_with_lyrics_valid)


    def _print_aligned_lyrics_report(self, all_tasks: list[AudioLyricAlignTask], tasks_valid: list[AudioLyricAlignTask]):

        
        # ____ Put together report text
        amount_tasks_total = len(all_tasks)
        amount_tasks_valid = len(tasks_valid)

        percent_valid = percentage(amount_tasks_valid, amount_tasks_total)


        lines_to_write = []
        lines_to_write.append("****** End of Work Report ******")
        lines_to_write.append(f"****** Valid tasks ({amount_tasks_valid}) ******")

        for task in tasks_valid:
            lines_to_write.append(f"{task.song_name[0:50] : <50} | {task.match_result.get_string()}")

        lines_to_write.append("")
        lines_to_write.append(f"****** All tasks - Valid {percent_valid :.2f}% ({amount_tasks_valid} / {amount_tasks_total}) ******")

        for task in all_tasks:
            lines_to_write.append(f"{task.song_name[0:50] : <50} | {task.lyric_validity}")

        text_to_write = "\n".join(lines_to_write)

        # ____ Write report text to disk

        path_to_this_file = Path(__file__).parent
        path_to_reports_folder = path_to_this_file / "reports"
        Path.mkdir(path_to_reports_folder, exist_ok=True)

        now = datetime.now()
        report_filename = now.strftime("%Y-%m-%d_%H:%M:%S Alignment Report.txt")
        report_file = path_to_reports_folder / report_filename

        report_file.write_text(text_to_write)
            
        end = 2