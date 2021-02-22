# Python
import logging

# 3rd Party
import lyricsgenius

# 1st Party
from .lyric_fetcher_interface import LyricFetcherInterface

# https://pypi.org/project/lyricsgenius/

class LyricFetcherGenius(LyricFetcherInterface):

    def __init__(self, token):
        super().__init__(".genius")
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

    def fetch_lyrics(self, path_to_song):

        path_to_local_copy = path_to_song.with_suffix(self.file_extension)

        if path_to_local_copy.exists():
            logging.info(f"Using local copy: {path_to_local_copy}")
            
            with open(path_to_local_copy, 'r') as file:
                file_contents = file.read()
            
            return file_contents

        # TODO: Split path_to_song into <name> - <song>
        
        filename = path_to_song.stem
        parts = filename.split(" - ")

        artist = parts[0].strip()
        song_name = parts[1].strip()
        
        genius_artist = self.genius.search_artist(artist, max_songs=1)
        genius_song = genius_artist.song(song_name)

        # TODO - Figure out what to do if there was no match
        with open(path_to_local_copy, 'w') as file:
            file.write(genius_song.lyrics)

        return genius_song.lyrics
        
        # genius_artist = self.genius.search_artist("The Go-Go's", max_songs=1)
        # genius_song = genius_artist.song("Vacation")