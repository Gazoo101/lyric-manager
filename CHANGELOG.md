# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]
### Added


### Changed


### Removed

## [1.1.0]
### Added
- The ability to suppement lyric-aligned output with a manually tweaked one, e.g. the suffix '.nusalaoffline-manual' will
override the '.nusalaoffline' aligned data, *if* the match percentage is equal or higher.
- 'lyric match percentage' is now written to the json output, updating the schema version to 2.1.0. This is useful as
better matched lyrics are expected to work well in more timing sensitive visuals.

### Changed
- Fixed WorkingDirectory being overwritten every time the GUI was started. Downside is that his entry is stored in Qt-
like data, i.e. /my/selected/path/ gets turned into @Variant(\0\0\0\x7f\0\0\0\x18PySide::PyObjectWrapper\0\0\0\0S\x80\x4\x95H\0\0\0\0\0\0\0\x8c\apathlib\x94\x8c\vWindowsPath\x94\x93\x94\x8c\x3\x44:\\\x94\x8c\x4\x43ode\x94\x8c\x19lyric-manager-working-dir\x94\x87\x94R\x94.)
- Re-factored some of the processing internals to be better encapsulated and offer cleaner support of the both automated
and tweaked aligned lyric data.

## [1.0.1]
### Added
- Added 'Clear Output' button.

### Changed
- Disabled aligner fixed.
- Alignment ready data is now properly added to the Lyric Align Task object being passed around (for debug purposes).

### Removed
- NUSAutoLyrixAlignOnline from the GUI as an option, as it's currently not implemented.

## [1.0]
### Added
- A separate GUI Settings Window which now supports most of LyricManager's settings
- GUI now supports specifying LyricAlignment location and working directory
- Widgets for remaining configuration added:
    - Determining audio artist and song title
    - Aligned Lyrics Formatting
    - Aligned Lyrics File Copy Mode
- Icons added to GUI tool-buttons.
- Proper error handling for when bad API key is handed to the LyricExtractor Lyric fetcher.
- Added .qrc and resources.py files
- Enum-based QCheckBox and QRadioBox to encapsulate and represent various LyricManager settings.

### Changed
- Better encapsulated widgets selecting lyric aligner(s) and lyric fetcher(s)
- Re-factored NUSAutoLyrixAlignOffline Aligner to properly copy temporary files and manage working directory
- Notes are now added to processing table hinting at issues/progress with processed files.
- Paths to individual audio files, as well as folders, is now supported.
- Fixed bug where LyricManager would occasionally only recognize .mp3 files, and not other valid types of audio files.
- Reduced superfluous error messages.
- Fixed bug related to NUSAutoLyrixAlign working directory not being saved properly
- Fixed line-edit widgets delivering strings as opposed to Path objects further on to the alignment pipeline
- Fixed crash if unable to query the current release of LyricManager on Github.
- Fixed AlignedLyricsFormatting Enum not being properly used in LyricManagerBase.
- Suppressed eyed3 logging output, apart from errors.
- Renamed .ui files to be more informative.

### Removed
- Listed limitation of a single online lyrics source. LyricManager now supports 2 online lyric sources.
- LyricFetcher.Disabled from Enum as its existence un-necessarily complicates GUI code. Value 'None' used when
  the LyricFetcher source has yet to be set for a task.

## [0.7]
### Added
- Github version check to inform users when a new release occurs.
- Multiple previously CLI-only settings now exposed in GUI (note they're not all currently functional)
- Support for getting artist and song name/title from mp3 tags, as opposed to from filename
- Icon for the application

### Changed
- Changed GUI to give more space to 'folders to process' list and encapsulate settings in tabbed pages.
- NUSAutoLyrixAligner made more tolerant to missing paths/files to allow for use of previously cached output.
- Fixed broken local filename lyric fetcher
- Application exit procedure from generating an exception when application closes in a 'normal' fashion

### Removed


## [0.5]
### Added
- 2 GUI splitters added to allow user to determine how to distribute the GUI layout.
- Added GUI settings entries for lyric fetchers that rely on external sources
- About dialogue box

### Changed
- Updated freezing to lead to a significantly reduced distribution size, i.e from 450 mb down to 80 mb
- Fixed PyPi_Genius fetcher being overly sensitive to tokens being empty strings
- Re-factored most of the fetcher code to be more unified and simpler
- Re-factored many internals for more consistent naming.
- Genius fetching garbage removal to be simpler and up-to-date with the current garbage being left in lyric data.
- Many other changes

### Removed
- Website_LyricsDotOvh from fetcher types as the source isn't working properly at all.

## [0.4]
- Pre-release version.

## [0.1] - 2023-02-15 - Version Reset
- This version is broken, but the changes are so massive, that the commit was made so as to track progess a bit better.

### Added
- Proper path check to NUSAutoLyrixAligner
- Tons of type-hinting
- Supports parsing multiple audio folders
- Support for more extensions .wav and .aiff (previously just .mp3)
- Added Gui and Cli

### Changed
- Switched from strictyaml to OmegaConf
- Updated and improved settings-example.yaml 
- Added tqdm to requirements.txt
- LyricManager / main.py re-factored for clarity and encapsulation
- Re-factored LyricAlignerNUSAutoLyrixAlignOffline for better encapsulation, clarity and instructions for proper
installation/use of external AudoLyrixAlign software
- Fixed out-dated and incorrectly type hinted entries in AudioLyricAlignTask
- YamlParser now converts paths into Pathlib.Path objects via function-based parsing
- Fixed yaml parser bug causing empty entries from getting turned into Path's pointing to the LyricManager cwd
- Removed 'None' which turns into a string from settings_example.yaml
- Added '' to None conversion in Enum conversion code
- Removed Genius as a 'default on' lyric source, as it'd necessitate a token, and the default behaviour should be as
uncomplicated as possible.
- .gitignore now ignores fetch_history.genius, output*/ folders, and reports folder

### Removed

## [0.5.0] - 2022-06-24
### Added
- Separate LyricState Enum

### Changed
- Refactored LyricManager - Functionally separate tasks are now much more encapsulated
- Attached lyric validity to AudioLyricAlignTask
- main.py version correlates with CHANGELOG
- Cleaned up lost of vestigial code

### Removed


## [0.0.5] - 2022-06-22
### Added
- Lyric validation in Genius fetcher. First draft, likely has numerous false positives and false negatives.

### Changed
- Cleaned up yaml parser
- Fixed various breaking changes in the code due to base class changes.
- All Enums are now pure Python Enums
- Partial re-factor to 
- requirements.txt now includes jsons
- Suppressed text output from lyricsgenius to not break tqdm progress-bar

### Removed
- StringEnum

## [0.0.4] - 2022-06-19
### Added
- A CHANGELOG.md

### Changed
- Genius lyric fetcher now supports UTF-8 characters as that shit sneaks into some pages.
- Settings.yaml is more diligent in checking conflicting settings
- Incoming Settings.yaml values are all converted in one place
- Minor bug-fixes mostly related to unused/unresolved variables
- General polish

### Removed
- Nothing