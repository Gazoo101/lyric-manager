# Python
from __future__ import annotations

import os
import sys
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import TYPE_CHECKING, Union


# 3rd Party


# 1st Party
from .developer_options import DeveloperOptions
from  src.components import ObjectFactory

from src.components import get_percentage_and_amount_string

from .lyric.dataclasses_and_types import LyricFetcherType
from .lyric.dataclasses_and_types import LyricAlignerType
from .lyric.dataclasses_and_types import LyricValidity
from .lyric.dataclasses_and_types import AudioLyricAlignTask

from .lyric.fetchers import LyricFetcherDisabled
from .lyric.fetchers import LyricFetcherPyPiLyricsGenius
from .lyric.fetchers import LyricFetcherPyPiLyricsExtractor
from .lyric.fetchers import LyricFetcherLocalFile
from .lyric.fetchers import LyricFetcherWebsiteLyricsDotOvh
from .lyric.fetchers import LyricFetcherInterface
from .lyric.fetchers import Lyrics

from .lyric.aligners import LyricAlignerInterface
from .lyric.aligners import LyricAlignerDisabled
from .lyric.aligners import LyricAlignerNUSAutoLyrixAlignOffline
from .lyric.aligners import LyricAlignerNUSAutoLyrixAlignOnline

from .lyric import LyricSanitizer
from .lyric import LyricExpander
from .lyric import LyricMatcher

from src.lyric_processing_config import Settings
from src.lyric_processing_config import FileCopyMode

if TYPE_CHECKING:
    from .lyric.aligners import WordAndTiming
    from .cli import ProgressItemGeneratorCLI
    from .gui import ProgressItemGeneratorGUI

class LyricManagerBase:
    def __init__(self, working_directory: str, reports_directory: str) -> None:
        """
        Args:
            working_directory: Either a default or user-defined path to LyricManager's working directory.
            reports_directory: Either a default or user-defined path to LyricManager's report directory.
        """
        # Preferred over __file__, as that has been known to cause issues with Py2Exe
        self.path_to_application = Path(sys.argv[0]).parent

        self.path_to_working_directory = self.path_to_application / working_directory
        self.path_to_working_directory.mkdir(exist_ok=True)

        self.path_to_reports = self.path_to_application / reports_directory
        self.path_to_reports.mkdir(exist_ok=True)

        self._init_logger(self.path_to_application)

        # LyricManager expects to have the current working directory set to its base execution
        os.chdir(self.path_to_application)
        logging.info(f"Current working directory: {os.getcwd()}")
        
        self.factory_lyric_fetcher = self._create_factory_lyric_fetcher()
        self.factory_lyric_aligner = self._create_factory_lyric_aligners()

        self.lyric_sanitizer = LyricSanitizer()
        self.lyric_expander = LyricExpander()

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


    def _create_factory_lyric_fetcher(self):
        factory = ObjectFactory()
        factory.register_builder(LyricFetcherType.Disabled, LyricFetcherDisabled)
        factory.register_builder(LyricFetcherType.Pypi_LyricsGenius, LyricFetcherPyPiLyricsGenius)
        factory.register_builder(LyricFetcherType.Pypi_LyricsExtractor, LyricFetcherPyPiLyricsExtractor)
        factory.register_builder(LyricFetcherType.LocalFile, LyricFetcherLocalFile)
        factory.register_builder(LyricFetcherType.Website_LyricsDotOvh, LyricFetcherWebsiteLyricsDotOvh)
        return factory


    def _create_factory_lyric_aligners(self):
        factory = ObjectFactory()
        factory.register_builder(LyricAlignerType.Disabled, LyricAlignerDisabled)
        factory.register_builder(LyricAlignerType.NUSAutoLyrixAlignOffline, LyricAlignerNUSAutoLyrixAlignOffline)
        factory.register_builder(LyricAlignerType.NUSAutoLyrixAlignOnline, LyricAlignerNUSAutoLyrixAlignOnline)
        return factory
    

    def _create_lyric_fetcher(self, type: LyricFetcherType, settings: Settings):
        """ Returns a lyric fetcher matching the provided type.

        In order to cleanly encapsulate the LyricFetcher from the configuration code, we must build this intermediary
        code handling parameter passing.
        """
        lyric_fetcher_parameters = {
            "path_to_working_dir": self.path_to_working_directory
        }

        if type == LyricFetcherType.Pypi_LyricsGenius:
            if settings.lyric_fetching.genius_token is None:
                logging.warning("Pypi_LyricsGenius source requires genius token to be defined.")
                logging.warning("LyricFetcher Pypi_LyricsGenius could not be instanitated.")
                return None

            lyric_fetcher_parameters["token"] = settings.lyric_fetching.genius_token
        elif type == LyricFetcherType.Pypi_LyricsExtractor:
            if settings.lyric_fetching.google_custom_search_api_key is None or \
               settings.lyric_fetching.google_custom_search_engine_id is None:
                logging.warning("PyPi_LyricsExtractor source requires api key and engine id to be defined.")
                logging.warning("LyricFetcher Pypi_LyricsExtractor could not be instanitated.")
                return None

            lyric_fetcher_parameters["google_custom_search_api_key"] = settings.lyric_fetching.google_custom_search_api_key
            lyric_fetcher_parameters["google_custom_search_engine_id"] = settings.lyric_fetching.google_custom_search_engine_id
        
        return self.factory_lyric_fetcher.create(type, **lyric_fetcher_parameters)


    def _create_lyric_aligner(self, type: LyricAlignerType, settings: Settings):

        lyric_aligner_parameters = {
            "path_temp_dir": self.path_to_working_directory, # improve this
        }

        if type == LyricAlignerType.NUSAutoLyrixAlignOffline:
            lyric_aligner_parameters["path_to_aligner"] = settings.lyric_alignment.NUSAutoLyrixAlign_path
            lyric_aligner_parameters["path_to_output_dir"] = settings.lyric_alignment.NUSAutoLyrixAlign_working_directory
            
            # think about this...
            #raise Exception("This has yet to be fixed - the outputdir doesn't exist and NUSAutoLyrix align likely needs 2 dirs.")

        return self.factory_lyric_aligner.create(type, **lyric_aligner_parameters)


    def _init_logger(self, path_to_application: Path):
        # Configures Pythons 'root' logger
        path_to_log = path_to_application / 'lyric_manager.log'
        
        # Debugging oriented logging output, including module and function name. Too verbose for standard usage.
        #self.logging_format = "%(asctime)s [%(levelname)s] %(module)s - %(funcName)s: %(message)s"
        self.logging_format = "%(asctime)s [%(levelname)s] %(message)s"

        self.logging_format_time = "%Y-%m-%d %H:%M" # Also used in Gui lyric manager

        logging.basicConfig(
            level=logging.INFO,
            #level=logging.DEBUG,
            format=self.logging_format,
            datefmt=self.logging_format_time,
            handlers=[
                logging.FileHandler(path_to_log),
                logging.StreamHandler()     # Pass 'sys.stdout' if we'd prefer not to print to std.err
            ]
        )
        logging.info(f"LyricManager {DeveloperOptions.version}")


    def execution_mode(self):
        if DeveloperOptions.execution_mode == DeveloperOptions.ExecutionMode.ReleaseInternal:
            # Standard execution mode just proceeds as normal
            pass
        elif DeveloperOptions.execution_mode == DeveloperOptions.ExecutionMode.ReleaseExternal:
            pass
        elif DeveloperOptions.execution_mode == DeveloperOptions.ExecutionMode.LyricParsing:
            pass


    
    def fetch_and_align_lyrics(self,
        settings: Settings,
        loop_wrapper: Union[ProgressItemGeneratorCLI, ProgressItemGeneratorGUI]) -> list[AudioLyricAlignTask]:
        """ Fetches and aligns lyrics using selected fetchers and aligner as defined by the settings parameter.

        Args:
            settings: Settings object containing all settings required to fully execute fetching and aligning of lyrics
            loop_wrapper: Encapsulates communicating progress either via command-line or graphical user-interface while
                the fetching and alignment code is executed.
        Returns:
            A list of AudioLyricAlignTask objects, either completed or failed.
        """

        # Construct fetchers and aligners.
        lyric_fetchers = []
        for lyric_fetcher_type in settings.lyric_fetching.sources:

            # Instantiation of lyric fetchers may fail if various API tokens are missing.
            lyric_fetcher = self._create_lyric_fetcher(lyric_fetcher_type, settings)
            if lyric_fetcher:
                lyric_fetchers.append(lyric_fetcher)

        lyric_aligner = self._create_lyric_aligner(settings.lyric_alignment.method, settings)


        paths_to_process_valid = []
        for path in settings.data.input.paths_to_process:
            if not path.exists():
                logging.info(f"Provided path to process '{path}' not found. Skipping it.")
                continue

            paths_to_process_valid.append(path)

        all_audio_files = self._get_audio_files_found_in_paths(paths_to_process_valid, settings.data.input.recursively_process_paths)

        logging.info(f"Found {len(all_audio_files)} audio files to process.")

        tasks = self._create_audio_lyric_align_tasks_from_paths(all_audio_files)

        # Design commentary:
        # Tasks are deliberately encapsulated into multiple functionally independent loops, as opposed to undertaking
        # all activities per-song in one giant loop. Because:
        #   - The code is easier to maintain - different types of functionality breaks differently.
        #   - Debugging can be more easily focused on one single failing functionality
        #   - Further encapsulation is simpler.

        tasks_with_lyrics: list[AudioLyricAlignTask] = []
        tasks_with_lyrics_valid: list[AudioLyricAlignTask] = []

        for task in loop_wrapper(tasks, desc="Fetching, validating, and sanitizing lyrics"):
            task_with_lyrics = self._fetch_and_sanitize_lyrics(lyric_fetchers, task)
            tasks_with_lyrics.append(task_with_lyrics)


        # For now we only keep (probably) valid lyrics
        tasks_with_lyrics_valid = [task for task in tasks_with_lyrics if task.lyric_validity == LyricValidity.Valid]


        # Because lyric alignment is fairly time-consuming (~0.5 minute processing per 1 minute audio), we write the
        # results to disk in the same loop to ensure nothing is lost in case of unexpected errors.
        for task in loop_wrapper(tasks_with_lyrics_valid, desc="Align lyrics"):

            lyric_align_task = self._align_lyrics(task, lyric_aligner, self.path_to_working_directory)

            self._write_aligned_lyrics_to_disk(lyric_align_task, self.path_to_working_directory, settings.data.output.aligned_lyrics_output_mode)

        self._create_aligned_lyrics_report(tasks_with_lyrics, tasks_with_lyrics_valid)

        return tasks_with_lyrics


    def _get_audio_files_found_in_paths(self, all_paths: list[Path], recursive: bool) -> list[Path]:
        """ Returns all files with an .mp3 extension in the paths provided, potentially scanning in sub-folders. """
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
    

    def _create_audio_lyric_align_tasks_from_paths(self, paths_to_audio_files: list) -> list[AudioLyricAlignTask]:
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
    

    def _fetch_and_sanitize_lyrics(self, lyric_fetchers, lyric_align_task: AudioLyricAlignTask):
        """ For a given AudioLyricAlignTask, fetches lyrics using available sources in self.all_lyric_fetchers.
        
        The order of the lyric fetches matters as function will accept the first valid source available.
        """
        lyric_fetcher: LyricFetcherInterface
        lyric_source = None
        for lyric_fetcher in lyric_fetchers:

            # Fetcher currently writes previously fetched copies to disk. This should perhaps
            # be elevated/exposed to this level.
            lyrics: Lyrics = lyric_fetcher.fetch_lyrics(lyric_align_task)
            lyric_source = lyric_fetcher.type

            # Source of lyrics found
            if lyrics.validity is LyricValidity.Valid:
                break

        if lyrics.validity is not LyricValidity.Valid:
            logging.warning(f"No valid lyric source found for: {lyric_align_task.path_to_audio_file}")
            # Add additional info here for what *was* found...
            return lyric_align_task
        
        lyric_align_task.lyric_text_raw = lyrics.raw
        lyric_align_task.lyric_text_sanitized = lyrics.sanitized
        lyric_align_task.lyric_validity = lyrics.validity
        lyric_align_task.lyric_source = lyric_source

        # if lyric_validity is not LyricValidity.Valid:
        #     logging.warning(f"Non-valid lyrics found for: {lyric_align_task.path_to_audio_file}. Will not sanitize.")
        #     return lyric_align_task

        # We must detect multipliers before sanitizing the lyrics...
        lyric_align_task.detected_multiplier = self.lyric_sanitizer.contains_multipliers(lyric_align_task.lyric_text_raw)

        lyric_align_task.lyric_text_expanded = self.lyric_expander.expand_lyrics(lyric_align_task.path_to_audio_file.stem, lyric_align_task.lyric_text_sanitized)

        # Separate full lyric string into a list of strings
        lyric_text_expanded_split = lyric_align_task.lyric_text_expanded.splitlines()

        # Remove empty lines
        lyric_text_expanded_split = [lyric_line for lyric_line in lyric_text_expanded_split if lyric_line]
        lyric_align_task.lyric_lines_expanded = lyric_text_expanded_split

        return lyric_align_task
    

    def _align_lyrics(self, lyric_align_task: AudioLyricAlignTask, lyric_aligner: LyricAlignerInterface, file_output_path: Path):
        """ A class for a user

        Args:
            - lyric_align_task -- The AudioLyricAlignTask to align, relies primarily on the .lyric_text_sanitized property.
            - file_output_path -- Folder into which the output should be produced.
            - use_preexisting_files -- ??? Not sure this is even currently respected.
        Returns:
            The same AudioLyricAlignTask object. Should probably be changed to return True/False for success.
        """

        # Most of this is to make the task of matching timing back to words a lot easier.
        alignment_lyrics = self.lyric_matcher.convert_lyrics_string_to_match_lyrics(lyric_align_task.lyric_lines_expanded)

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

        time_aligned_lyrics: list[WordAndTiming] = lyric_aligner.align_lyrics(
            lyric_align_task.path_to_audio_file,
            path_to_alignment_ready_file,
            use_preexisting=True
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


    def _string_list_to_string(self, string_list):
        ''' Converts a list of strings into a single string without double spaces. '''
        string = ' '.join(string_list)
        return ' '.join(string.split())
    

    def _create_aligned_lyrics_report(self, all_tasks: list[AudioLyricAlignTask], tasks_valid: list[AudioLyricAlignTask]):
        """ Creates a text with a lyric alignment report into the /reports folder. """

        # Three-Step aligned lyrics report creation:
        # 1. Calculate all the metrics that go into the report.
        # 2. Format all the text to go into the report.
        # 3. Write the report to a file

        # _________________________________ ____ _ _ _
        # ___ Step 1: Calculate all metrics
        amount_tasks_total = len(all_tasks)
        amount_tasks_valid = len(tasks_valid)

        stat_valid_out_of_total = get_percentage_and_amount_string(amount_tasks_valid, amount_tasks_total)

        songs_match_rate_100 = [task for task in tasks_valid if task.match_result.match_percentage == 100.0]
        songs_match_rate_90 = [task for task in tasks_valid if task.match_result.match_percentage >= 90.0]

        amount_songs_match_rate_100 = len(songs_match_rate_100)
        amount_songs_match_rate_90 = len(songs_match_rate_90)

        stat_match_rate_100_out_of_valid = get_percentage_and_amount_string(amount_songs_match_rate_100, amount_tasks_valid)
        stat_match_rate_90_out_of_valid = get_percentage_and_amount_string(amount_songs_match_rate_90, amount_tasks_valid)

        # Sources



        # _________________________________ ____ _ _ _
        # ___ Step 2: Format the report text
        lines_to_write = []
        lines_to_write.append("============------------ Executive Summary ------------============")
        lines_to_write.append(f"* Songs with validated lyrics       {stat_valid_out_of_total:>30}")
        lines_to_write.append(f"* Songs with 100% matched lyrics    {stat_match_rate_100_out_of_valid:>30}")
        lines_to_write.append(f"* Songs with >90% matched lyrics    {stat_match_rate_90_out_of_valid:>30}")

        lines_to_write.append("")
        lines_to_write.append("============------------ - - - - - - - - - ------------============")
        lines_to_write.append("")

        lines_to_write.append("")
        lines_to_write.append(f"============------------ Songs with validated Lyrics {stat_valid_out_of_total} ------------============")

        for task in tasks_valid:
            lines_to_write.append(f"{task.path_to_audio_file.stem[0:80] : <80} | {task.match_result.get_string()}")

        lines_to_write.append("")
        lines_to_write.append(f"============------------ All songs ( {amount_tasks_total} ) ------------============")

        for task in all_tasks:
            lines_to_write.append(f"{task.path_to_audio_file.stem[0:80] : <80} | {task.lyric_validity} | Mult: {task.detected_multiplier}")

        text_to_write = "\n".join(lines_to_write)


        # _________________________________ ____ _ _ _
        # ___ Step 3: Write the report to a file
        #Path.mkdir(self.path_to_reports, exist_ok=True)

        now = datetime.now()
        report_filename = now.strftime("%Y-%m-%d_%H.%M.%S Alignment Report.txt")
        report_file = self.path_to_reports / report_filename

        report_file.write_text(text_to_write)
            
        end = 2