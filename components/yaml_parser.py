# Python
import sys
import strictyaml
import logging
from pathlib import Path
from enum import Enum
from enum import auto
from functools import partial
from typing import Union

# 3rd Party

# 1st Party


# Intentionally left as a non-explicit import, i.e. NOT 'from lyric_fetcher import LyricFetcherInterface'
# as this would lead to a circular dependence.
import lyric_fetcher
import lyric_aligner


class FileOutputLocation(Enum):
    NextToAudioFile = auto()
    SeparateDirectory = auto()

class YamlParser():

    def __init__(self):
        self.parsing_funcs = {}

        self.parsing_funcs['lyric_fetchers'] = partial(self._strings_to_enum, lyric_fetcher.LyricFetcherType)
        self.parsing_funcs['lyric_aligner'] = partial(self._strings_to_enum, lyric_aligner.LyricAlignerType)
        self.parsing_funcs['file_output_location'] = partial(self._strings_to_enum, FileOutputLocation)
        self.parsing_funcs['path_to_audio_files_to_process'] = partial(self._strings_to_paths)
        self.parsing_funcs['path_to_output_files'] = partial(self._strings_to_paths)
        self.parsing_funcs['path_to_NUSAutoLyrixAlignOffline'] = partial(self._strings_to_paths)
        self.parsing_funcs['path_to_NUSAutoLyrixAlign_working_directory'] = partial(self._strings_to_paths, check_spaces=True)


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

            # Turn empty entries ('') into None
            if not value:
                yaml_dict[key] = None
                continue

            if key in self.parsing_funcs:
                yaml_dict[key] = self.parsing_funcs[key](value)


    def _strings_to_enum(self, enum_type, input_string: Union[list, str]):
        """ Parses a string (or a list of strings) into the provided the provided Enum object type.
        
        Args:
            enum_type: The Enum object type to convert a string or list of strings into.
            input_string: String or list of strings to convert.
        Returns:
            An Enum object or list of Enum objects depending on the input.
        """
        if isinstance(input_string, list):
            return_list = []

            for elem in input_string:
                return_list.append(self._strings_to_enum(enum_type, elem))

            return return_list

        try:
            enum_object = enum_type[input_string]
        except KeyError as err:
            logging.exception(f"The provided setting type name '{input_string}' was unknown. Note that text-case is sensitive!")
            sys.exit(1)

        return enum_object

    def _strings_to_paths(self, input_string: str, check_spaces: bool = False):
        """ Turns strings into Pathlib.Path objects, handles '~' symboles, resolves relative paths. """
        path = Path(input_string)
        path = path.expanduser()    # '~/' => '/home/user/'
        path = path.resolve()

        if check_spaces:
            if ' ' in str(path):
                raise Exception(f"A given path ('{path}') contained an illegal space character (' ').")

        return path