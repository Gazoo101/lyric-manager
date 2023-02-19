from dataclasses import dataclass, field
from typing import List, Optional
from pathlib import Path
from enum import Enum, auto

from omegaconf import MISSING

from .lyric.fetchers import LyricFetcherType
from .lyric.aligners import LyricAlignerType

class FileCopyMode(Enum):
    Disabled = auto()
    NextToAudioFile = auto()
    SeparateDirectory = auto()

class AlignedLyricsOutputMode(Enum):
    Readable = auto()
    Compact = auto()


    
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



@dataclass
class SettingsDataOutput():
    path_to_working_directory: Path = MISSING

    path_to_reports: Path = MISSING

    aligned_lyrics_file_copy_mode: FileCopyMode = FileCopyMode.SeparateDirectory

    path_to_output_aligned_lyrics: Optional[Path] = field(default_factory=Path)

    aligned_lyrics_output_mode: AlignedLyricsOutputMode = AlignedLyricsOutputMode.Readable

    overwrite_existing_generated_files: bool = True



@dataclass
class SettingsData():
    input: SettingsDataInput = field(default_factory=SettingsDataInput)

    output: SettingsDataOutput = field(default_factory=SettingsDataOutput)


@dataclass
class Settings():
    lyric_fetching: SettingsLyricFetching = field(default_factory=SettingsLyricFetching)

    lyric_alignment: SettingsLyricAlignment = field(default_factory=SettingsLyricAlignment)

    data: SettingsData = field(default_factory=SettingsData)
    