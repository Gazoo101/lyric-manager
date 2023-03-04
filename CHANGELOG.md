# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]
### Added

### Changed

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