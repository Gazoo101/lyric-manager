# Lyric Manager

Lyric Manager's primary function is support automatic song and lyric aligment. Specifically, given an .mp3 file Lyric Manager will query various lyric sources including, but not limited to:

- Local .txt files
- Remote lyric databases

to obtain the songs lyrics. Using the song.mp3 file and song.txt lyric file, Lyric Manager will use these files in conjunction with a lyric aligner. For now, Lyric Manager only utilises NUSAutoLyrixAlign and is optimized for its output. However, the framework is supportive of other alignment tools as needed.

# Output

Lyric Manager generates a series of intermediate files, and one final output with the extension `.aligned_lyrics` containing JSON, which looks something like this:

```json
{
    "schema_version": "2.0.0",      // Commentary inserted for clarity (not present in actual output!)
    "lyric_lines": [
        {
            "text": "Oxy-toxins flowing",
            "time_start": 107.82,
            "time_end": 110.43,
            "lyric_words": [
                {
                    "original": "Oxy",
                    "single": "Oxy",
                    "word_split_char_pre": "",
                    "word_split_char_post": "-",
                    "time_start": 107.82,
                    "time_end": 108.57
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
                    "original": "flowing",
                    "single": "flowing",
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

# Limitations

Lyric Manager has a number of known limitations:

- Lyric Manager expects a specific song filenaming convention is expected: "<artist> - <songname>.mp3"
- Lyric Manager only supports a single lyric aligner (for now)
- Lyric Manager only supports fetching lyrics from one lyric database