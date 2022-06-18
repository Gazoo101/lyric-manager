# Python
#from typing import NamedTuple
import strictyaml
from collections import namedtuple
import logging
from pathlib import Path
from enum import Enum
from functools import partial
from typing import Union
import sys

# 3rd Party

# 1st Party
from components import StringEnum

#from lyric_aligner import LyricAlignerType
#from lyric_fetcher import LyricFetcherType

# Intentionally left as a non-explicit import, i.e. NOT 'from lyric_fetcher import LyricFetcherInterface'
# as this would lead to a circular dependence.
import lyric_fetcher
import lyric_aligner

# TODO: Replace with dataclass, or even better, consider replacing with just easydict and converting
# some parts as this is getting a bit silly...
# Dataclass might be more reasonable to enable defaults, and why are we allowing for command-line? We'd not
# need it any time soon.
# Settings = namedtuple("Settings",
#     [
#         'path_to_audio_files',
#         'recursive_iteration',
#         'overwrite_generated_file',
#         'file_output_location',
#         'file_output_path',
#         'export_readable_json',
#         'lyric_fetchers',
#         'lyric_fetcher_genius_token',
#         'keep_fetched_lyrics',
#         'lyric_aligner',
#         'path_to_NUSAutoLyrixAlignOffline',
#         'use_preexisting_files'
#     ])

class FileOutputLocation(StringEnum):
    NextToAudioFile = "NextToAudioFile"
    SeparateDirectory = "SeparateDirectory"

class YamlParser():

    def __init__(self):
        self.parsing_funcs = {}

        self.parsing_funcs['lyric_fetchers'] = partial(self._parse_to_enum, lyric_fetcher.LyricFetcherType)
        self.parsing_funcs['lyric_aligner'] = partial(self._parse_to_enum, lyric_aligner.LyricAlignerType)
        self.parsing_funcs['file_output_location'] = partial(self._parse_to_enum, FileOutputLocation)

    def parse(self, path_to_yaml_file:Path):
        """
        
        """
        if path_to_yaml_file.exists() == False:
            error = "No settings.yaml found."
            logging.warning(error)
            raise RuntimeError(error)

        yaml_contents = strictyaml.load(path_to_yaml_file.read_text())
        yaml_contents = yaml_contents.data

        self._apply_parsing_functions_to_dict(yaml_contents)

        # Validate settings.yaml (this should/can partially be done via strictyaml)
        if yaml_contents['data']['file_output_location'] == FileOutputLocation.SeparateDirectory:
            if not yaml_contents['data']['path_to_output_files']:
                logging.error("File output set to 'SeparateDirectory', but no 'path_to_output_files' was provided.")
                sys.exit(1)

        # Insta-convert some paths - perhaps write a parser for this.
        yaml_contents['data']['path_to_output_files'] = Path(yaml_contents['data']['path_to_output_files'])
        yaml_contents['data']['path_to_audio_files_to_process'] = Path(yaml_contents['data']['path_to_audio_files_to_process'])

        return yaml_contents

    def _apply_parsing_functions_to_dict(self, yaml_dict:dict):
        """ Recursively traverses a given dict and applies a set of tranformation functions.

        If a key in the provided dict matches a key in self.parsing_funcs, the function (stored as a value) is applied
        to the value in the given dict. The function output overwrites the value in the given dict.
        """
        for key, value in yaml_dict.items():
            #print(f"key: {key}")
            
            if isinstance(value, dict):
                self._apply_parsing_functions_to_dict(value)
                continue

            if key in self.parsing_funcs:
                yaml_dict[key] = self.parsing_funcs[key](value)




    # def parse(self, path_to_yaml_file):

    #     if path_to_yaml_file.exists() == False:
    #         error = "No settings.yaml found."
    #         logging.warning(error)
    #         raise RuntimeError(error)

    #     yaml_contents = strictyaml.load(path_to_yaml_file.read_text())
    #     yaml_contents = yaml_contents.data

    #     # with open(path_to_yaml_file) as file:
    #     #     yaml_contents = yaml.safe_load(file)
 
    #     lyric_fetcher_types = []

    #     for fetcher_type in yaml_contents['lyric_fetchers']:
    #         lyric_fetcher_types.append(self._parse_string_to_enum(lyric_fetcher.LyricFetcherType, fetcher_type))

    #     if not bool(yaml_contents['lyric_aligner']):
    #         error = "No lyric_aligned selected in settings.yaml."
    #         logging.error(error)
    #         raise RuntimeError(error)

    #     lyric_aligner_type = self._parse_string_to_enum(lyric_aligner.LyricAlignerType, yaml_contents['lyric_aligner'])

    #     file_output_location = self._parse_string_to_enum(FileOutputLocation, yaml_contents['file_output_location'])

    #     path_to_NUSAutoLyrixAlignOffline = None
    #     if yaml_contents['path_to_NUSAutoLyrixAlignOffline'] != 'None':
    #         path_to_NUSAutoLyrixAlignOffline = Path(yaml_contents['path_to_NUSAutoLyrixAlignOffline'])

    #     parsed_settings = Settings(
    #         path_to_audio_files=Path(yaml_contents['path_to_audio_files']),
    #         recursive_iteration=yaml_contents['recursively_parse_audio_file_path'],
    #         overwrite_generated_file=yaml_contents['overwrite_existing_generated_files'],
    #         file_output_location=file_output_location,
    #         file_output_path=Path(yaml_contents['file_output_path']),
    #         export_readable_json=yaml_contents['export_readable_json'],
    #         lyric_fetchers=lyric_fetcher_types,
    #         lyric_fetcher_genius_token=yaml_contents['lyric_fetcher_genius_token'],
    #         keep_fetched_lyrics=yaml_contents['keep_fetched_lyric_files'],
    #         lyric_aligner=lyric_aligner_type,
    #         path_to_NUSAutoLyrixAlignOffline=path_to_NUSAutoLyrixAlignOffline,
    #         use_preexisting_files=yaml_contents['use_preexisting_files']
    #     )

    #     return parsed_settings


    def _parse_to_enum(self, string_enum, input_string: Union[list, str]):
        """ A generic parser which converts a given string into the appropriate StringEnum.

        Args:
            string_enum: An enum object expected to derive from StringEnum.
            input_string: The string provided in the Settings file.
        Returns:
            The specific Enum object that the given string matches in the given derived
            StringEnum object.
        """
        # enum_options = string_enum.as_dict()
        # name_of_enum = string_enum.__name__

        if isinstance(input_string, list):
            return_list = []

            for elem in input_string:
                return_list.append(self._parse_string_to_enum(string_enum, elem))

            return return_list

        return self._parse_string_to_enum(string_enum, input_string)


    def _parse_string_to_enum(self, string_enum, input_string):
        """ A generic parser which converts a given string into the appropriate StringEnum.

        Args:
            string_enum: An enum object expected to derive from StringEnum.
            input_string: The string provided in the Settings file.
        Returns:
            The specific Enum object that the given string matches in the given derived
            StringEnum object.
        """
        enum_options = string_enum.as_dict()
        name_of_enum = string_enum.__name__

        if (input_string.lower() not in enum_options.keys()):
            # We convert .keys() into a list() for prettier print output
            error_message = f'Unable to parse: "{input_string}" into {name_of_enum} enum. Possible options: {list(enum_options.keys())}'
            logging.warning(error_message)
            raise Exception(error_message)
            # self.logger.print_and_log_error(error_message)
            # raise StringToEnumParsingError(error_message)

        return enum_options[input_string.lower()]
