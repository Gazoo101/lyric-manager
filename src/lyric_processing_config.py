from dataclasses import dataclass, field
from typing import List, Optional
from pathlib import Path
from enum import Enum, auto

from omegaconf import MISSING

from .lyric.fetchers import LyricFetcherType
from .lyric.aligners import LyricAlignerType

class FileOutputLocation(Enum):
    Disabled = auto()
    NextToAudioFile = auto()
    SeparateDirectory = auto()

class AlignedLyricsOutputMode(Enum):
    Readable = auto()
    Compact = auto()

# @dataclass
# class ConfigGeneral():
#     lyric_fetchers: List[LyricFetcherType] = MISSING

#     lyric_fetcher_genius_token: Optional[str] = ""

#     lyric_aligner: LyricAlignerType = LyricAlignerType.Disabled

#     path_to_NUSAutoLyrixAlign_working_directory: Optional[Path] = field(default_factory=Path)

#     path_to_NUSAutoLyrixAlignOffline: Path = field(default_factory=Path)

#     export_readable_json: bool = True


# @dataclass
# class ConfigData():
#     paths_to_audio_files_to_process: List[Path] = field(default_factory=list)

#     folders_to_exclude: Optional[List] = field(default_factory=list)

#     recursively_parse_audio_file_path: bool = False

#     overwrite_existing_generated_files: bool = True

#     # TODO: This name REALLY needs to change, to easily confused with the setting below
#     file_output_location: FileOutputLocation = FileOutputLocation.SeparateDirectory

#     path_to_output_files: Path = field(default_factory=Path)

#     # TODO: Turn this into Enum, as we'll likely want fairly varied behavior for using pre-existing
#     # or getting new files in for various situations.
#     use_preexisting_files: bool = True

#     # In case we download them from some place (like genius)
#     keep_fetched_lyric_files: bool = True


# @dataclass
# class Config():
#     general: ConfigGeneral = field(default_factory=ConfigGeneral)

#     data: ConfigData = field(default_factory=ConfigData)

    
@dataclass
class SettingsLyricFetching():
    sources: List[LyricFetcherType] = MISSING

    genius_token: Optional[str] = ""

@dataclass
class SettingsLyricAlignment():
    method: LyricAlignerType = LyricAlignerType.Disabled

    NUSAutoLyrixAlign_path: Optional[Path] = field(default_factory=Path)

    NUSAutoLyrixAlign_working_directory: Optional[Path] = field(default_factory=Path)

@dataclass
class SettingsDataInput():
    paths_to_process: List[Path] = field(default_factory=list)

    folders_to_exclude: Optional[List] = field(default_factory=list)

    recursively_process_paths: bool = False

    overwrite_existing_generated_files: bool = True



@dataclass
class SettingsDataOutput():
    path_to_working_directory: Path = MISSING

    aligned_lyrics_copy_destination: FileOutputLocation = FileOutputLocation.SeparateDirectory

    path_to_output_aligned_lyrics: Optional[Path] = field(default_factory=Path)

    aligned_lyrics_output_mode: AlignedLyricsOutputMode = AlignedLyricsOutputMode.Readable



@dataclass
class SettingsData():
    input: SettingsDataInput = field(default_factory=SettingsDataInput)

    output: SettingsDataOutput = field(default_factory=SettingsDataOutput)


@dataclass
class Settings():
    lyric_fetching: SettingsLyricFetching = field(default_factory=SettingsLyricFetching)

    lyric_alignment: SettingsLyricAlignment = field(default_factory=SettingsLyricAlignment)

    data: SettingsData = field(default_factory=SettingsData)
    


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
