# Python
from __future__ import annotations
import os
import logging
import contextlib
import time
import random
import re
from pathlib import Path
from datetime import datetime
from typing import TYPE_CHECKING
from difflib import SequenceMatcher

# 3rd Party
import lyricsgenius
from lyricsgenius.song import Song
from requests.exceptions import Timeout


# 1st Party
from .lyric_fetcher_base import LyricFetcherBase
from ..dataclasses_and_types import LyricPayload
from ..dataclasses_and_types import LyricFetcherType
from ..dataclasses_and_types import LyricValidity
from ...components import text_simplifier

if TYPE_CHECKING:
    from ..dataclasses_and_types import LyricAlignTask


class LyricFetcherPyPiLyricsGenius(LyricFetcherBase):
    """ Retrieves Lyrics from genius.com via lyricgenius.
    
    PyPi Link: https://pypi.org/project/lyricsgenius/
    """

    def __init__(self, token, path_to_working_dir:Path = None):
        super().__init__(LyricFetcherType.Pypi_LyricsGenius, ".genius", path_to_working_dir)
        self.token = token

        # lyricgenius throws a TypeError if the provided token is bad. This exception is expected to be caught
        # externally.
        self.genius = lyricsgenius.Genius(self.token)

        self.sequence_matcher = SequenceMatcher()

        # In an effort to not overload Genius' servers, we insert some self-rate limiting
        self.rate_limit = True
        self.rate_limit = False
        self.timestamp_recent_fetch = datetime.now()

        self.random_wait_lower = 3.0 # seconds
        self.random_wait_upper = 10.0 # seconds


    def _get_lyric_text_raw_from_source(self, source: Song) -> str:
        """ Each fetcher will have a somewhat different source, so we must implement this - rewrite this code description. """
        return source.lyrics


    def _text_simplify(self, text: str):
        text = text.replace("’", "'")
        text = text.replace("D.J.", "dj")
        text = text.replace('(', '').replace(')', '')
        text = text.replace('+', '\+')
        return text
    
    def _is_artist_and_song_name_similar(self, lyric_align_task:LyricAlignTask, raw_source: Song) -> bool:
        """ Determines whether the task artist and song name matches the sources artist and song name.

        Pypi's lyricgenius will often return a completely unrelated lyric result related to the request. Checking the
        similarity of the artist and song name is a good approach to filter out early inaccurate results.
        """

        # The comparison should be case-invariant
        task_artist = lyric_align_task.artist.lower()
        source_artist = raw_source.artist.lower()

        task_song_name = lyric_align_task.song_name.lower()
        source_song_name = raw_source.title.lower()

        self.sequence_matcher.set_seqs(task_artist, source_artist)
        ratio_artist = self.sequence_matcher.ratio()

        self.sequence_matcher.set_seqs(task_song_name, source_song_name)
        ratio_song_name = self.sequence_matcher.ratio()

        # Debug output
        logging.debug(f"Artist: Task '{task_artist}' vs. source '{source_artist}' - Ratio {ratio_artist}")
        logging.debug(f"Song name: Task '{task_song_name}' vs. source '{source_song_name}' - Ratio {ratio_song_name}")

        similarity_threshold = 0.5

        if ratio_artist > similarity_threshold and ratio_song_name > similarity_threshold:
            logging.debug("Similarity: Accepted!")
            return True
        
        logging.debug("Similarity: Failed!")
        return False



    def _validate_lyrics(self, lyric_align_task:LyricAlignTask, raw_source: Song) -> LyricValidity:
        """ Attempts to determine whether the lyrics found are legit or not. """
        lyrics = raw_source.lyrics

        if not self._is_artist_and_song_name_similar(lyric_align_task, raw_source):
            # Most likely incorrect lyrics
            return LyricValidity.WrongSong

        # Valid lyrics tend to always start with some combination of "<Song Title> Lyrics", so our validation will
        # be guided by this fact.
        index_of_first_instance_of_lyric = lyrics.find("Lyrics")

        # Error cases, which - until now, appear to never trigger.
        if index_of_first_instance_of_lyric == -1:
            return LyricValidity.Invalid_NoLyricStringFound
        elif index_of_first_instance_of_lyric > len(lyric_align_task.song_name) + 100:
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
        song_name = self._text_simplify(lyric_align_task.song_name)
    
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


    def _fetch_lyrics_payload(self, lyric_align_task: LyricAlignTask) -> LyricPayload:
        lyrics = LyricPayload()


        if self.fetch_history[lyric_align_task.filename].get_total_error_amount() >= 1:
            lyrics.validity = LyricValidity.Skipped_Due_To_Fetch_Errors
            logging.info(f"Skipping {lyric_align_task.filename} due to previous fetch errors.")
            return lyrics


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
                genius_song = self.genius.search_song(lyric_align_task.song_name, lyric_align_task.artist)

            # genius_artist = self.genius.search_artist(lyric_align_task.artist, max_songs=1)
            # genius_song = genius_artist.song(lyric_align_task.song_name)
        except Timeout:
            logging.warning("Timeout error.")
            self.fetch_history[lyric_align_task.filename].time_out += 1
            self._save_fetch_history()
            return lyrics

        if not genius_song:
            logging.warning(f"Song '{lyric_align_task.song_name}' was not found.")
            self.fetch_history[lyric_align_task.filename].not_found += 1
            self._save_fetch_history()
            return lyrics


        lyrics.source = genius_song
        lyrics.validity = self._validate_lyrics(lyric_align_task, genius_song)

        return lyrics


    """ See LyricFetcherInterface._sanitize_lyrics_raw() for description. """
    def _sanitize_lyrics_raw(self, lyric_align_task:LyricAlignTask, raw_source: Song) -> str:
        """ Returns sanitized lyrics containing (ideally) no garbage text.
        
        Note, the Pypi package lyricsgenius likely does not exclusively access official Genius API end-points. Hence,
        not only may the lyric data contain some garbage information that requires sanatizing, worse still, this
        garbage data may change over time.

        Time of confirmed proper sanitization: 04-03-2023
        
        """
        lyrics = self._get_lyric_text_raw_from_source(raw_source)

        # Remove lead-in garbage data
        # It appears we can just use the genius-sourced title to remove the leading 'garbage data'
        lead_in_garbage = f"{raw_source.title} Lyrics"
        lyrics = lyrics[len(lead_in_garbage):]

        #lyrics = self.lyric_sanitizer.remove_leading_title(lyric_align_task.song_name, lyrics)

        # Remove lead-out garbage data
        # Examples:
        # <lyrics>2Embed
        # <lyrics>40Embed
        # <lyrics>19Embed
        # <lyrics>5Embed
        # <lyrics>You might also likeEmbed
        # <lyrics>You might also like82Embed'

        # First we remove the '<numeric value>Embed' portion
        lyrics = self.lyric_sanitizer.remove_embed_at_end(lyrics)

        # Hard-code detect this new piece of garbage data. Hopefully, no lyrics will ever end with this line :/
        occasional_garbage_ending = "You might also like"
        if lyrics.endswith(occasional_garbage_ending):
            lyrics = lyrics[:-len(occasional_garbage_ending)]

        lyrics = lyrics.splitlines()

        # Clears non-lyric content like [verse 1] and empty lines
        lyrics = self.lyric_sanitizer.remove_non_lyrics(lyrics)

        lyrics = self.lyric_sanitizer.replace_difficult_characters(lyrics)

        lyrics = '/n'.join(lyrics)

        return lyrics