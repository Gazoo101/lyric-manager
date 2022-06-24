# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]
### Added
- Proper path check to NUSAutoLyrixAligner

### Changed
- Removed 'None' which turns into a string from settings_example.yaml

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