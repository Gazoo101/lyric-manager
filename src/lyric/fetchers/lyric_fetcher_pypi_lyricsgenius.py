# Python
from __future__ import annotations
import os
import logging
import contextlib
import time
import random
import re
from dataclasses import dataclass
from pathlib import Path
from datetime import datetime
from typing import DefaultDict, Tuple, TYPE_CHECKING
from collections import defaultdict

# 3rd Party
import jsons
import lyricsgenius
from requests.exceptions import Timeout


# 1st Party
from .lyric_fetcher_interface import LyricFetcherInterface
from ..dataclasses_and_types import LyricFetcherType
from ..dataclasses_and_types import LyricValidity
from ...components import text_simplifier

if TYPE_CHECKING:
    from ..dataclasses_and_types import AudioLyricAlignTask

# FetchErrors is a @dataclass so we can construct defaultdict(FetchErrors) which can be serialized using jsons.
# defaultdict(defaultdict(Enum)) cannot be serialized in using jsons.
@dataclass
class FetchErrors():
    time_out : int = 0
    not_found : int = 0

    def get_total_error_amount(self):
        return self.time_out + self.not_found


class LyricFetcherPyPiLyricsGenius(LyricFetcherInterface):
    """ Retrieves Lyrics from genius.com via lyricgenius.
    
    Uses https://pypi.org/project/lyricsgenius/
    
    """

    def __init__(self, token, path_to_working_dir:Path = None):
        super().__init__(LyricFetcherType.Pypi_LyricsGenius, ".genius", path_to_working_dir)
        self.token = token
        self.genius = lyricsgenius.Genius(self.token)

        # In an effort to not overload Genius' servers, we insert some self-rate limiting
        self.rate_limit = True
        self.rate_limit = False
        self.timestamp_recent_fetch = datetime.now()

        self.random_wait_lower = 3.0 # seconds
        self.random_wait_upper = 10.0 # seconds

        self.path_to_fetch_history = path_to_working_dir / "genius_fetch_history.lm"
        self.fetch_history = self._init_fetch_history()


    def _init_fetch_history(self):
        fetch_history = defaultdict(FetchErrors)

        if self.path_to_fetch_history.exists():
            file_content = self.path_to_fetch_history.read_text()
            fetch_history = jsons.loads(file_content, DefaultDict[str, FetchErrors])

        return fetch_history


    def _save_fetch_history(self):
        fetch_history_serialized = jsons.dumps(self.fetch_history)
        self.path_to_fetch_history.write_text(fetch_history_serialized)


    def _text_simplify(self, text: str):
        text = text.replace("’", "'")
        text = text.replace("D.J.", "dj")
        text = text.replace('(', '').replace(')', '')
        text = text.replace('+', '\+')
        return text


    def _validate_lyrics(self, audio_lyric_align_task: AudioLyricAlignTask, lyrics: str):
        """ Attempts to determine whether the lyrics found are legit or not. """

        # _____________________________________
        # _______ Step 1: Early Return

        # Valid lyrics tend to always start with some combination of "<Song Title> Lyrics", so our validation will
        # be guided by this fact.
        index_of_first_instance_of_lyric = lyrics.find("Lyrics")

        # Error cases, which - until now, appear to never trigger.
        if index_of_first_instance_of_lyric == -1:
            return LyricValidity.Invalid_NoLyricStringFound
        elif index_of_first_instance_of_lyric > len(audio_lyric_align_task.song_name) + 100:
            return LyricValidity.Invalid_LyricStringFoundTooFarIntoString

        # Heuristically determined invalid lengths
        number_of_chars_in_lyrics = len(lyrics)
        number_of_chars_too_many = 13000
        number_of_chars_too_few = 70 # Like Herbie Hancock - Rock It :/ should update this

        if number_of_chars_in_lyrics >= number_of_chars_too_many:
            return LyricValidity.Invalid_TooManyChars

        if number_of_chars_in_lyrics <= number_of_chars_too_few:
            return LyricValidity.Invalid_TooFewChars
        

        # _____________________________________
        # _______ Step 2: Lyrics *seem* ok. Do they match the song?

        lyrics_beginning = lyrics[0:index_of_first_instance_of_lyric]

        # Hard-coded simplifications to make life easier
        lyrics_beginning = self._text_simplify(lyrics_beginning)
        song_name = self._text_simplify(audio_lyric_align_task.song_name)
    
        # Match case-insensitive song-name with zero or multiple spaces
        reg_exp_start = f"(?i){song_name}\s*"

        result = re.match(reg_exp_start, lyrics_beginning)

        # If the name is a perfect match - we're fairly certain the lyrics are good.
        if result:
            return LyricValidity.Valid

        # Song name variation can be pretty high - So this code attempts to catch some of it, by seeing if at least
        # 50% of the song title appears to match

        # Example
        # For song name: Blue Monday ('88)
        # But lyric source: Blue Monday '88 (7" Version)
        if text_simplifier.percentage_song_name_match(song_name, lyrics_beginning) > 0.5:
            return LyricValidity.Valid

        # If we get here, the lyrics are possibly ok, but they're likely for a different song...
        return LyricValidity.WrongSong


    def _fetch_lyrics_raw(self, audio_lyric_align_task: AudioLyricAlignTask) -> Tuple[str, LyricValidity]:

        ####
        # Fetch pre-cached version
        path_to_cached_lyrics = audio_lyric_align_task.path_to_audio_file

        if self.path_to_working_dir:
            path_to_cached_lyrics = self.path_to_working_dir / audio_lyric_align_task.path_to_audio_file.name

        path_to_cached_lyrics = path_to_cached_lyrics.with_suffix(self.file_extension)

        if path_to_cached_lyrics.exists():
            logging.info(f"Using local copy: {path_to_cached_lyrics}")
            
            with open(path_to_cached_lyrics, 'r', encoding='utf-8') as file:
                file_contents = file.read()

            lyric_validity = self._validate_lyrics(audio_lyric_align_task, file_contents)
            
            return file_contents, lyric_validity

        ####
        # Fetch fresh version
        if self.fetch_history[audio_lyric_align_task.filename].not_found >= 1:
            return None, LyricValidity.NotSet

        if self.rate_limit:
            time_since_last_fetch = datetime.now() - self.timestamp_recent_fetch
            if time_since_last_fetch.total_seconds() < self.random_wait_lower:
                random_wait = random.uniform(self.random_wait_lower, self.random_wait_upper)
                logging.info(f"Forcing rate-limit wait of {random_wait} second(s).")
                time.sleep(random_wait)

            self.timestamp_recent_fetch = datetime.now()

        try:
            # Silence geniuslibrary - breaks output.
            with open(os.devnull, "w") as f, contextlib.redirect_stdout(f):
                genius_song = self.genius.search_song(audio_lyric_align_task.song_name, audio_lyric_align_task.artist)

            # genius_artist = self.genius.search_artist(audio_lyric_align_task.artist, max_songs=1)
            # genius_song = genius_artist.song(audio_lyric_align_task.song_name)
        except Timeout:
            logging.warning("Timeout error.")
            self.fetch_history[audio_lyric_align_task.filename].time_out += 1
            self._save_fetch_history()
            return None, LyricValidity.NotSet

        if not genius_song:
            logging.warning(f"Song '{audio_lyric_align_task.song_name}' was not found.")
            self.fetch_history[audio_lyric_align_task.filename].not_found += 1
            self._save_fetch_history()
            return None, LyricValidity.NotSet

        # Utf-8 required, as some lyrics sneak in awful non-ascii chars which break file-writing.
        with open(path_to_cached_lyrics, 'w', encoding="utf-8") as file:
            file.write(genius_song.lyrics)      # If there are UTF-8 chars - non unicode, we're effed'

        lyric_validity = self._validate_lyrics(audio_lyric_align_task, genius_song.lyrics)

        return genius_song.lyrics, lyric_validity


    """ See LyricFetcherInterface.sanitize_raw_lyrics() for description. """
    def sanitize_raw_lyrics(self, audio_lyric_align_task:AudioLyricAlignTask) -> str:
        lyrics = audio_lyric_align_task.lyric_text_raw

        # lyricgenius now returns some garbage-data in the lyrics we must clean up
        # TODO: Delegate this clean up to the relevant fetcher, i.e. genius should clean genius garbage
        # other db, should clean other db garbage
        lyrics = self.lyric_sanitizer.remove_leading_title(audio_lyric_align_task.song_name, lyrics)
        lyrics = self.lyric_sanitizer.remove_embed_at_end(lyrics)

        # Clears non-lyric content like [verse 1] and empty lines
        lyrics = self.lyric_sanitizer.remove_non_lyrics(lyrics)
        # TODO: ALSO SPLITS string, this isn't clear and should be 'separated out' or unified somehow with the
        # local file handler/sanitizer.

        lyrics = self.lyric_sanitizer.replace_difficult_characters(lyrics)

        return lyrics