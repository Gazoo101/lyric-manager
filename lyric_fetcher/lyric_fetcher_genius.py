# Python
import logging
from requests.exceptions import Timeout
from pathlib import Path

# 3rd Party
import lyricsgenius

# 1st Party
from .lyric_fetcher_interface import LyricFetcherInterface
from components import AudioLyricAlignTask

# https://pypi.org/project/lyricsgenius/

class LyricFetcherGenius(LyricFetcherInterface):
    """ Retrieves Lyrics from genius.com via lyricgenius. """

    def __init__(self, token, path_to_output_dir:Path = None):
        super().__init__(".genius", path_to_output_dir)
        self.token = token
        self.genius = lyricsgenius.Genius(self.token)

    def _working_demo(self):

        # genius = lyricsgenius.Genius(self.genius_token)

        #artist = genius.search_artist("Andy Shauf", max_songs=3, sort="title")

        input = "The Go-Go's - Vacation"

        #artist = genius.search_artist("The Go-Go's", max_songs=3, sort="title")
        artist = self.genius.search_artist("The Go-Go's", max_songs=1)
        vacay_song = artist.song("Vacation")

        #vacay_song.lyrics

        with open("Output.txt", "w") as text_file:
            print(vacay_song.lyrics, file=text_file)

        # Lyric parsing ideas - get rid of commas, as they just make clutter
        # Convert abbreviations to their full spelling? e.g. "Nothin'" => "Nothing"

        print(artist.songs)

        horse = 2

    def fetch_lyrics(self, audio_lyric_align_task: AudioLyricAlignTask):

        path_to_cached_lyrics = audio_lyric_align_task.path_to_audio_file

        if self.path_to_output_dir:
            path_to_cached_lyrics = self.path_to_output_dir / audio_lyric_align_task.path_to_audio_file.name

        path_to_cached_lyrics = path_to_cached_lyrics.with_suffix(self.file_extension)

        if path_to_cached_lyrics.exists():
            logging.info(f"Using local copy: {path_to_cached_lyrics}")
            
            with open(path_to_cached_lyrics, 'r') as file:
                file_contents = file.read()
            
            return file_contents

        try:
            genius_artist = self.genius.search_artist(audio_lyric_align_task.artist, max_songs=1)
            genius_song = genius_artist.song(audio_lyric_align_task.song_name)
        except Timeout:
            logging.warn("Timeout error.")
            return None

        # TODO - Figure out what to do if there was no match
        with open(path_to_cached_lyrics, 'w') as file:
            file.write(genius_song.lyrics)

        return genius_song.lyrics
        
        # genius_artist = self.genius.search_artist("The Go-Go's", max_songs=1)
        # genius_song = genius_artist.song("Vacation")