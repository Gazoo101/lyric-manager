# Design considerations / ideas
#
# .elrc format appears to not support if timing is a word ending or a new word starting. - stick with JSON

# Python
#from LyricManager.lyric_aligner.lyric_aligner_interface import LyricAlignerInterface
import sys
import logging
from argparse import ArgumentParser
from pathlib import Path

from yaml import parse

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


def lyric_fetcher_aligner_from_enum_to_class(
    lyric_fetcher_types,
    lyric_aligner_type,
    genius_token,
    path_to_NUSAutoLyrixAlignOffline):

    all_lyric_fetchers = []
    lyric_aligner = None

    for type in lyric_fetcher_types:

        if type == LyricFetcherType.Disabled:
            print("Lyric Fetcher: Disabled")
            lyric_fetcher = LyricFetcherDisabled()
        elif type == LyricFetcherType.LocalFile:
            print("Lyric Fetcher: Local File(s)")
            lyric_fetcher = LyricFetcherLocalFile()
        elif type == LyricFetcherType.Genius:
            print("Lyric Fetcher: Genius Database")
            lyric_fetcher = LyricFetcherGenius(genius_token)
        
        all_lyric_fetchers.append(lyric_fetcher)

    
    # We construct a temporary path to manage the lyrics aligner temporary output
    lyric_aligner_temp_path = Path.home() / "LyricManager"

    if lyric_aligner_type == LyricAlignerType.Disabled:
        print("Lyric Aligner: Disabled")
        lyric_aligner = LyricAlignerDisabled(lyric_aligner_temp_path)
    elif lyric_aligner_type == LyricAlignerType.NUSAutoLyrixAlignOffline:
        print("Lyric Aligner: Local File(s)")
        lyric_aligner = LyricAlignerNUSAutoLyrixAlignOffline(lyric_aligner_temp_path, path_to_NUSAutoLyrixAlignOffline)
    elif lyric_aligner_type == LyricAlignerType.NUSAutoLyrixAlignOnline:
        print("Lyric Aligner: Genius Database")
        lyric_aligner = LyricAlignerNUSAutoLyrixAlignOnline(lyric_aligner_temp_path)

    return all_lyric_fetchers, lyric_aligner

# def _parse_arguments(input_arguments):

#     opts = parser.parse_args(incoming_parameters)

#     if opts.audio_path.exists() == False:
#         raise Exception("Provided audio path doesn't exist.")

#     lyric_fetcher = None
#     lyric_aligner = None

#     if opts.lyric_fetcher == LyricFetcherInterface.Type.Disabled:
#         print("Lyric Fetcher: Disabled")
#         lyric_fetcher = LyricFetcherDisabled()
#     elif opts.lyric_fetcher == LyricFetcherInterface.Type.LocalFile:
#         print("Lyric Fetcher: Local File(s)")
#         lyric_fetcher = LyricFetcherLocalFile()
#     elif opts.lyric_fetcher == LyricFetcherInterface.Type.Genius:
#         print("Lyric Fetcher: Genius Database")
#         lyric_fetcher = LyricFetcherGenius(opts.genius_token)

#     if opts.lyric_aligner == LyricAlignerInterface.Type.Disabled:
#         print("Lyric Aligner: Disabled")
#         lyric_aligner = LyricAlignerDisabled()
#     elif opts.lyric_aligner == LyricAlignerInterface.Type.NUSAutoLyrixAlignOffline:
#         print("Lyric Aligner: Local File(s)")
#         lyric_aligner = LyricAlignerNUSAutoLyrixAlignOffline()
#     elif opts.lyric_aligner == LyricAlignerInterface.Type.NUSAutoLyrixAlignOnline:
#         print("Lyric Aligner: Genius Database")
#         lyric_aligner = LyricAlignerNUSAutoLyrixAlignOnline()

#     return lyric_fetcher, lyric_aligner, opts

#     parser = argparse.ArgumentParser(description='Lyric Manager')

#     parser.add_argument('-lf','--lyric_fetcher', type=LyricFetcher.Type, choices=list(LyricFetcher.Type), help='Lyric Fetcher Type')

#     thingy = parser.parse_args(input_arguments)

#     return parser.parse_args(input_arguments)

def _command_line_arguments():
    ''' Code developed before the requirements and number of settings grew to an
    arguably unmanagable size. I will rewrite and introduce the command-line argument
    based support if there's enough of a need / want for it.
    '''

    parser = ArgumentParser()
    parser.add_argument('-ap', '--audio_path', type=Path, help="Path to audio files", required=True)
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

    logging.basicConfig(
        level=logging.INFO,
        #level=logging.DEBUG,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler(path_to_log),
            logging.StreamHandler()     # Pass 'sys.stdout' if we'd prefer not to print to std.err
        ]
    )

    logging.info('Lyric Manager v1.2.1')

    yaml_parser = YamlParser()
    parsed_settings = yaml_parser.parse( path_to_settings )

    all_lyric_fetchers, lyric_aligner = lyric_fetcher_aligner_from_enum_to_class(
        parsed_settings.lyric_fetchers,
        parsed_settings.lyric_aligner,
        parsed_settings.lyric_fetcher_genius_token,
        parsed_settings.path_to_NUSAutoLyrixAlignOffline)

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

    path_to_audio = parsed_settings.path_to_audio_files
    recursive = parsed_settings.recursive_iteration
    keep_files = parsed_settings.keep_fetched_lyrics
    overwrite_generated_files = parsed_settings.overwrite_generated_file
    export_readable_json = parsed_settings.export_readable_json
    use_preexisting_files = parsed_settings.use_preexisting_files

    mylm.fetch_and_align_lyrics(
        path_to_audio,
        recursive,
        keep_files,
        export_readable_json=export_readable_json,
        use_preexisting_files=use_preexisting_files
        )