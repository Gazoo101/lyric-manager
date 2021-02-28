# Python
#from typing import NamedTuple
import yaml
from collections import namedtuple
import logging
from pathlib import Path

# 3rd Party

# 1st Party

#from lyric_aligner import LyricAlignerType
#from lyric_fetcher import LyricFetcherType

# Intentionally left as a non-explicit import, i.e. NOT 'from lyric_fetcher import LyricFetcherInterface'
# as this would lead to a circular dependence.
import lyric_fetcher
import lyric_aligner

Settings = namedtuple("Settings",
    [
        'path_to_audio_files',
        'recursive_iteration',
        'overwrite_generated_file',
        'lyric_fetchers',
        'lyric_fetcher_genius_token',
        'keep_fetched_lyrics',
        'lyric_aligner',
        'path_to_NUSAutoLyrixAlignOffline'
    ])

class YamlParser():

    def __init__(self):
        pass

    def parse(self, path_to_yaml_file):

        with open(path_to_yaml_file) as file:
            yaml_contents = yaml.safe_load(file)
 
        lyric_fetcher_types = []

        for fetcher_type in yaml_contents['lyric_fetchers']:
            lyric_fetcher_types.append(self._parse_string_to_enum(lyric_fetcher.LyricFetcherType, fetcher_type))

        lyric_aligner_type = self._parse_string_to_enum(lyric_aligner.LyricAlignerType, yaml_contents['lyric_aligner'])

        parsed_settings = Settings(
            path_to_audio_files=Path(yaml_contents['path_to_audio_files']),
            recursive_iteration=yaml_contents['recursively_parse_audio_file_path'],
            overwrite_generated_file=yaml_contents['overwrite_existing_generated_files'],
            lyric_fetchers=lyric_fetcher_types,
            lyric_fetcher_genius_token=yaml_contents['lyric_fetcher_genius_token'],
            keep_fetched_lyrics=yaml_contents['keep_fetched_lyric_files'],
            lyric_aligner=lyric_aligner_type,
            path_to_NUSAutoLyrixAlignOffline=Path(yaml_contents['path_to_NUSAutoLyrixAlignOffline'])
        )

        return parsed_settings


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
            logging.warn(error_message)
            raise Exception(error_message)
            # self.logger.print_and_log_error(error_message)
            # raise StringToEnumParsingError(error_message)

        return enum_options[input_string.lower()]
