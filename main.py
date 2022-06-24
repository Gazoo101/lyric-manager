# Design considerations / ideas
#
# .elrc format appears to not support if timing is a word ending or a new word starting. - stick with JSON

# Python
#from LyricManager.lyric_aligner.lyric_aligner_interface import LyricAlignerInterface
import sys
import logging
from argparse import ArgumentParser
from pathlib import Path
import os

# 3rd Party


# 1st Party
#from components import FileOps

from lyric_fetcher import LyricFetcherType
from lyric_fetcher import LyricFetcherInterface
from lyric_fetcher import LyricFetcherDisabled
from lyric_fetcher import LyricFetcherLocalFile
from lyric_fetcher import LyricFetcherGenius

from lyric_aligner import LyricAlignerType
from lyric_aligner import LyricAlignerInterface
from lyric_aligner import LyricAlignerDisabled
from lyric_aligner import LyricAlignerNUSAutoLyrixAlignOffline
from lyric_aligner import LyricAlignerNUSAutoLyrixAlignOnline

from lyric_manager import LyricManager

from components import YamlParser

def create_lyric_fetchers(lyric_fetcher_types, genius_token, path_to_output_dir=None):
    all_lyric_fetchers = []

    for type in lyric_fetcher_types:

        if type == LyricFetcherType.Disabled:
            logging.info("Adding Lyric Fetcher - Disabled")
            lyric_fetcher = LyricFetcherDisabled()
        elif type == LyricFetcherType.LocalFile:
            logging.info("Adding Lyric Fetcher - Local File(s)")
            lyric_fetcher = LyricFetcherLocalFile(path_to_output_dir)
        elif type == LyricFetcherType.Genius:
            logging.info("Adding Lyric Fetcher - Genius Database")
            lyric_fetcher = LyricFetcherGenius(genius_token, path_to_output_dir)
        
        all_lyric_fetchers.append(lyric_fetcher)
    
    return all_lyric_fetchers

def create_lyric_aligner(lyric_aligner_type, path_to_NUSAutoLyrixAlignOffline, path_to_output_dir=None):
    lyric_aligner = None

    # We construct a temporary path to manage the lyrics aligner temporary output
    lyric_aligner_temp_path = Path.home() / "LyricManager"

    if lyric_aligner_type == LyricAlignerType.Disabled:
        print("Lyric Aligner: Disabled")
        lyric_aligner = LyricAlignerDisabled(lyric_aligner_temp_path)
    elif lyric_aligner_type == LyricAlignerType.NUSAutoLyrixAlignOffline:
        print("Lyric Aligner: Local File(s)")
        lyric_aligner = LyricAlignerNUSAutoLyrixAlignOffline(lyric_aligner_temp_path, path_to_NUSAutoLyrixAlignOffline, path_to_output_dir)
    elif lyric_aligner_type == LyricAlignerType.NUSAutoLyrixAlignOnline:
        print("Lyric Aligner: Genius Database")
        lyric_aligner = LyricAlignerNUSAutoLyrixAlignOnline(lyric_aligner_temp_path)

    return lyric_aligner


def _command_line_arguments():
    ''' Code developed before the requirements and number of settings grew to an
    arguably unmanagable size. I will rewrite and introduce the command-line argument
    based support if there's enough of a need / want for it.
    '''

    parser = ArgumentParser()
    
    # os.path.abspath allows the user to pass either relative or absolute paths. We'll have to convert the string to a
    # pathlib.Path later though.
    parser.add_argument('-ap', '--audio_path', type=os.path.abspath, default='.', help="Path to audio files", required=True)
    #parser.add_argument('-r', '--recursive', type=bool, default=False, help="Recursively parse folders")
    parser.add_argument('-lf', '--lyric_fetcher', type=LyricFetcherInterface.Type, choices=list(LyricFetcherInterface.Type),
                        default=LyricFetcherInterface.Type.Off)
    parser.add_argument('-gt', '--genius_token', type=str, default="")

    parser.add_argument('-la', '--lyric_aligner', type=LyricAlignerInterface.Type, choices=list(LyricAlignerInterface.Type),
                        default=LyricAlignerInterface.Type.Off)
    #parser.add_argument('-kl', '--keep_lyrics', type=bool, help="Retain non-aligned lyrics in the lyric-aligned JSON.")
    parser.add_argument('-kl', '--keep_lyrics', dest='keep_lyrics', action='store_true', help="Retain non-aligned lyrics in the lyric-aligned JSON.")

    parser.add_argument('-r', '--recursive', dest='recursive', action='store_true')
    parser.add_argument('-d', '--destructive', dest='destructive', action='store_true')
    
    parser.set_defaults(recursive=False, destructive=False)


if __name__ == '__main__':
    path_to_application = Path(__file__).parent

    # .log and .yaml are expected to be in the same folder as the main.py
    path_to_log = path_to_application / "lyric_manager.log"
    path_to_settings = path_to_application / "settings.yaml"

    format_time_level_message = "%(asctime)s [%(levelname)s] %(message)s" # Original
    format_level_file_func_message = "[%(levelname)s][%(filename)s - %(funcName)25s() ] %(message)s"

    logging.basicConfig(
        level=logging.INFO,
        #level=logging.DEBUG,
        format=format_level_file_func_message,
        handlers=[
            logging.FileHandler(path_to_log, mode='w'), # w == Overwrite
            logging.StreamHandler()     # Pass 'sys.stdout' if we'd prefer not to print to std.err
        ]
    )

    logging.info('Lyric Manager v0.5.0')

    yaml_parser = YamlParser()
    parsed_settings = yaml_parser.parse( path_to_settings )

    all_lyric_fetchers = create_lyric_fetchers(
        parsed_settings['general']['lyric_fetchers'],
        parsed_settings['general']['lyric_fetcher_genius_token'],
        parsed_settings['data']['path_to_output_files']
    )

    lyric_aligner = create_lyric_aligner(
        parsed_settings['general']['lyric_aligner'],
        parsed_settings['general']['path_to_NUSAutoLyrixAlignOffline'],
        parsed_settings['data']['path_to_output_files']
    )

    incoming_parameters = sys.argv[1:]

    # # Various command-line debug overwrite tests
    # # incoming_parameters = ['--help']
    # incoming_parameters = ['-lf', 'Genius']
    # incoming_parameters = ['-ap', 'D:/Music/']
    # #incoming_parameters = ['-ap', 'D:/Music/', '-r']
    # incoming_parameters = ['-ap', 'D:/Music/', '-r', '-kl']
    # incoming_parameters = ['-ap', 'D:/Music/', '-lf', 'Genius', '-r', '-kl', '-gt', '']
    # #incoming_parameters = ['-ap', 'D:/Music/', '-r']

    #get_settings_from_yaml("D:/Code/LyricManager/settings.yaml")


    # with open("D:/Code/LyricManager/settings.yaml") as file:
    #     config = yaml.safe_load(file)

    #lyric_fetcher, lyric_aligner, opts = _parse_arguments(incoming_parameters)

    mylm = LyricManager(all_lyric_fetchers, lyric_aligner)

    mylm.fetch_and_align_lyrics(
        parsed_settings['data']['path_to_audio_files_to_process'],
        parsed_settings['data']['recursively_parse_audio_file_path'],
        parsed_settings['data']['keep_fetched_lyric_files'],   # Not currently respected I think...
        export_readable_json=parsed_settings['general']['export_readable_json'],
        use_preexisting_files=parsed_settings['data']['use_preexisting_files'],
        file_output_location=parsed_settings['data']['file_output_location'],
        file_output_path=parsed_settings['data']['path_to_output_files']
    )