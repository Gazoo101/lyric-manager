<div align="center">

<div id="user-content-toc">
  <ul>
    <summary><h1 style="display: inline-block;">Lyric Manager</h1></summary>
  </ul>
</div>
	
:speech_balloon::musical_note: **Lyric Manager is an open source, music lyric manager to align lyrics to your song collection!**

---

![Screenshot](./docs/images/Capture.png)

</div>

# :sparkles: Features

- Two interface flavors
  - Graphical-User Interface
  - Command-Line Interface
- Supports fetching lyrics from three sources
  - Local text file
  - Pypi lyricsgenius genius db
  - Pypi lyric_extractor using GCS
- Supports one aligner
  - NUSLyrixAutoAlign

# Introduction

Lyric Manager's primary function is support automatic song and lyric aligment. Specifically, given an .mp3 file Lyric Manager will query various lyric sources including, but not limited to:

- Local .txt files
- Remote lyric databases

to obtain the songs lyrics. Using the song.mp3 file and song.txt lyric file, Lyric Manager will use these files in conjunction with a lyric aligner. For now, Lyric Manager only utilises NUSAutoLyrixAlign and is optimized for its output. However, the framework is supportive of other alignment tools as needed.

# Requirements

- Python 3.7+ (due to its reliance on dataclass)
- Ubuntu 20.04 for Gui (due to reliance on Qt6)

# Input / Output

Lyric Manager uses the following input/output files, for a given `song.mp3`:

Input / Output | filename | Description
-------------- | -------- | -------------
Input | `song.mp3` | The audio to which the lyrics should be aligned. Provided by you.
Input | `song.txt` | Text file containing lyrics for `song.mp3`, provided by you. Set `LocalFile` in `lyric_fetchers` in `settings.yaml` to use this source.
Output | `song.genius` | If `lyric_fetchers` in `settings.yaml` includes `Genius` Lyric Manager will attempt to retrieve lyrics from the Genius database and generate this intermediate file.
Output | `song.lyrics_sanitized` | A sanitized version of the `song.txt` or `song.genius` removing non-lyric text and converting the lyrics to be more paletable for NUSAutoLyrixAlign.
Output | `song.nusalaoffline` | The alignment data generated by the offline version of NUSAutoLyrixAlign.
Output | `song.aligned_lyrics` | Contains JSON data with timing data and supporting rendering information as detailed below.

Example contents of `song.aligned_lyrics`:

```json5
{
    // Commentary inserted for clarity (not present in actual output!)
    "schema_version": "2.0.0", // A schema version to better track improvements / breakage
    "lyric_lines": [
        // lyric_lines typically contains multiple entries, one per line in the original lyric text.
        // Lyric Manager retains the lyric format structure (i.e. which words are in which lines)
        // from the original lyrics.
        // This example includes just a single entry.
        {
            "text": "Oxy-toxins flowing,", // Text of lyric line
            "time_start": 107.82,         // Start time of full lyric line in seconds (from beginning of .mp3 file)
            "time_end": 110.43,           // End time of full lyric line in seconds (from beginning of .mp3 file)
            "lyric_words": [
                {
                    "original": "Oxy",              // Original text of single lyric word
                    "single": "Oxy",                // Modified text, expected to be more presentable as single word (see example below)
                    "word_split_char_pre": "",      // Character (if present) which is part of pre-split
                    "word_split_char_post": "-",    // Character (if present) which is part of post-split
                    "time_start": 107.82,           // Start time of word in seconds (from beginning of .mp3 file)
                    "time_end": 108.57              // End time of word in seconds (from beginning of .mp3 file)
                },
                {
                    "original": "toxins",
                    "single": "toxins",
                    "word_split_char_pre": "-",
                    "word_split_char_post": " ",
                    "time_start": 108.57,
                    "time_end": 109.8
                },
                {
                    "original": "flowing,",         // Original text of single lyric word - note the presence of the "," character
                    "single": "flowing",            // More presentable 'single word version' without the "," character
                    "word_split_char_pre": " ",
                    "word_split_char_post": "",
                    "time_start": 109.8,
                    "time_end": 110.43
                }
            ]
        }
	]
}
```

# Usage Example

Install required python packages using `requirements.txt`.

Rename the provided `settings.yaml-example` file to `settings.yaml`, set the appropriate settings, and execute main.py.

# Project Files Layout

```
lyric-manager/
│
├── data/
│   ├── fetch_history.genius    - Record of time-out's or bad requests.
│   ├── lyric_manager.log       - Log output, generated at run-time.
│   ├── settings-example.yaml   - Settings example to copy and rename to settings.yaml
│   └── settings.yaml           - Your specific settings to run Lyric Manager.
│
├── lyric-manager/
│   └── lyric-manager source files
│
├── output/
│   ├── alignment_related/
│   │   └── Various files generated throughout the lyric alignment process
│   ├── reports/
│   │   ├── 2022-07-10_15:14:01 Alignment Report.txt    - Results of alignment process executed at this date/time
│   │   ├── ...
│   │   └── 2022-07-10_15:14:01 Alignment Report.txt    - Results of alignment process executed at this date/time
```

# Limitations

Lyric Manager has a number of known limitations:

- Lyric Manager expects a specific song filenaming convention is expected: "<artist> - <songname>.mp3" (or other audio extension)
- Lyric Manager only supports a single lyric aligner (for now), i.e. NUSAutoLyrixAlign offline (found here: https://github.com/chitralekha18/AutoLyrixAlign)
    - In the meantime, you can use the online version of NUSAutoLyrixAlign (found here: https://autolyrixalign.hltnus.org/) and rename the output (for Audacity - selected in their online tool) to be the offline extension, e.g. `song.nusalaoffline`
- Lyric Manager only supports fetching lyrics from one lyric database or a manually provided file


# FAQ

I'm getting the error "version `GLIBC_2.28' not found"!

This will occur on Ubuntu 18.04, as Qt6 requires Ubuntu 20.04.
