# Lyric Manager

Lyric Manager's primary function is support automatic song and lyric aligment. Specifically, given an .mp3 file Lyric Manager will query various lyric sources including, but not limited to:

- Local .txt files
- Remote lyric databases

to obtain the songs lyrics. Using the song.mp3 file and song.txt lyric file, Lyric Manager will use these files in conjunction with a lyric aligner. For now, Lyric Manager only utilises NUSAutoLyrixAlign and is optimized for its output. However, the framework is supportive of other alignment tools as needed.

# Usage Examples

Install required python packages using `requirements.txt`.

Rename the provided `settings.yaml-example` file to `settings.yaml`, set the appropriate settings, and execute main.py.

# Limitations

Lyric Manager has a number of known limitations:

- Lyric Manager expects a specific song filenaming convention is expected: "<artist> - <songname>.mp3"
- Lyric Manager only supports a single lyric aligner (for now)
- Lyric Manager only supports fetching lyrics from one lyric database