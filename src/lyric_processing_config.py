from dataclasses import dataclass, field
from typing import List, Optional
from pathlib import Path
from enum import Enum, auto

from omegaconf import MISSING

from .lyric.fetchers import LyricFetcherType
from .lyric.aligners import LyricAlignerType

class FileOutputLocation(Enum):
    NextToAudioFile = auto()
    SeparateDirectory = auto()

@dataclass
class ConfigGeneral():
    lyric_fetchers: List[LyricFetcherType] = MISSING

    lyric_fetcher_genius_token: str = ""

    lyric_aligner: LyricAlignerType = LyricAlignerType.Disabled

    path_to_NUSAutoLyrixAlign_working_directory: Path = field(default_factory=Path)

    path_to_NUSAutoLyrixAlignOffline: Path = field(default_factory=Path)

    export_readable_json: bool = True


@dataclass
class ConfigData():
    paths_to_audio_files_to_process: List[Path] = field(default_factory=list)

    folders_to_exclude: Optional[List] = field(default_factory=list)

    recursively_parse_audio_file_path: bool = False

    overwrite_existing_generated_files: bool = True

    # TODO: This name REALLY needs to change, to easily confused with the setting below
    file_output_location: FileOutputLocation = FileOutputLocation.SeparateDirectory

    path_to_output_files: Path = field(default_factory=Path)

    # TODO: Turn this into Enum, as we'll likely want fairly varied behavior for using pre-existing
    # or getting new files in for various situations.
    use_preexisting_files: bool = True

    # In case we download them from some place (like genius)
    keep_fetched_lyric_files: bool = True


@dataclass
class Config():
    general: ConfigGeneral = field(default_factory=ConfigGeneral)

    data: ConfigData = field(default_factory=ConfigData)

    




# paths_to_process:list[Path], 
#             recursive=False, 
#             destructive=False, 
#             keep_lyrics=False, 
#             export_readable_json=False,
#             use_preexisting_files=True,
#             file_output_location=FileOutputLocation.NextToAudioFile,
#             file_output_path:Path=None


# LyricManager Settings File

# general:
#   # Supported lyric fetches:
#   # - LocalFile
#   # - Genius
#   # - LyricsDotOvh (Not fully implemented)
#   # If left empty, LyricManager will assume local files are available?
#   lyric_fetchers:
#     - LocalFile
#     - Genius

#   # Required, if lyric_fetchers includes Genius
#   lyric_fetcher_genius_token: DzW8Y1B5rLbBqvB3vvaH3UBoouG2w6juak1KMBc5Fyg9iL6BRsBQ3OI8RYUJWBYt

#   # Supported lyric aligners:
#   #   - NUSAutoLyrixAlignOffline
#   #   - NUSAutoLyrixAlignOnline (Not fully implemented)
#   #   - Disabled
#   lyric_aligner: Disabled

#   # Required, if lyric_aligner=NUSAutoLyrixAlignOffline
#   path_to_NUSAutoLyrixAlignOffline: None

#   # LyricManager supports two export_readable_json settings:
#   #   - False: Few spaces, few line breaks, no tabs. Intended for low disk space consumtion.
#   #   - True: Indentation, lots of spaces and line breaks. Intended for readability and debugging.
#   export_readable_json: True

# data:
#   # Folder with music for LyricManager to parse
#   path_to_audio_files_to_process: D:\MusicMaster\Prime

#   # Any folders added here will be excluded from processing. Mainly useful for recursive parsing.
#   folders_to_exclude:

#   recursively_parse_audio_file_path: False

#   overwrite_existing_generated_files: True

#   file_output_location: SeparateDirectory
#   path_to_output_files: D:\MusicMaster\LyricsPrime1

#   # TODO: Turn this into Enum, as we'll likely want fairly varied behavior for using pre-existing
#   # or getting new files in for various situations.
#   use_preexisting_files: True

#   # In case we download them from some place (like genius)
#   keep_fetched_lyric_files: True
