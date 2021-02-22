# Python
import os
from enum import Enum
from pathlib import Path
import json
import logging
import re
from collections import namedtuple

# 3rd Party
import lyricsgenius

# 1st Party

WordAndTiming = namedtuple("WordAndTiming", ["word", "time_start", "time_end"])

class LyricManager:

    def __init__(self, all_lyric_fetchers, lyric_aligner):
        print("initied")

        self.all_lyric_fetchers = all_lyric_fetchers
        self.lyric_aligner = lyric_aligner

    def _get_all_audio(self, path, recursive):

        all_audio_files = []

        if recursive:
            all_files = os.walk(path)

            for dirpath, dirnames, filenames in all_files:
                audio_files_in_dir = [Path(dirpath) / filename for filename in filenames if filename.endswith("mp3")]
                all_audio_files.extend(audio_files_in_dir)
        else:
            all_audio_files = [Path(entry.path) for entry in os.scandir(path) if entry.name.endswith("mp3")]

        return all_audio_files

    def _sanitize_lyrics(self, lyrics):
        ''' Returns a list of sanitized lyric strings.

        Each string in the list represents a single coheasive sung sentence. This is used during
        visualization to cohesively visualize sentances.
        '''
        # Lyrics are provided in a single large string

        # 1. Reformat string into per-line for easier human manipulation
        all_lyric_lines = lyrics.splitlines()

        

        sanitized_lyric_lines = []

        for lyric_line in all_lyric_lines:
            # Removes [<any content, except newlines>]
            #complete_lyric_string = re.sub(r"\[.*\]", '', complete_lyric_string)
            lyric_line = re.sub(r"\[[a-zA-Z0-9 -]*\]", '', lyric_line)

            sanitized_lyric_lines.append(lyric_line)

        # Removes empty lines
        non_empty_lyric_lines = [lyric_line for lyric_line in sanitized_lyric_lines if lyric_line]


        # complete_lyric_string = ' '.join(non_empty_lyric_lines)

        # # Removes [<any content, except newlines>]
        # #complete_lyric_string = re.sub(r"\[.*\]", '', complete_lyric_string)
        # complete_lyric_string = re.sub(r"\[[a-zA-Z0-9 -]*\]", '', complete_lyric_string)

        # # Remove double-spaces
        # complete_lyric_string = ' '.join(complete_lyric_string.split())

        return non_empty_lyric_lines

    
    def _verify_lyrics(self, lyrics_stuctured, lyrics_timing):
        '''

        It's unknown how broken or un-matched lyrics are going to be, so for now,
        let's just verify that every single word has timing.
        
        '''

        lt_iter = iter(lyrics_timing)

        for line_index, lyric_line in enumerate(lyrics_stuctured):

            lyric_line_parts = lyric_line.split(' ')

            for word_index, word in enumerate(lyric_line_parts):

                lyric_timed = next(lt_iter)

                word1 = lyric_timed.word.lower()
                word2 = word.lower()

                if word1 != word2:
                    print(f"Mismatch on Line {line_index}, Word {word_index}: {lyric_line}")
                    print(f"Word from original lyrics: {word2} | Timed Lyric: {word1}")
                    # Lyric doesn't match :/
                    hello = 2
                    

                hello = 2

            hello = 2
        
        hello = 2


    def _create_lyrics_json(self, lyrics_stuctured, lyrics_timing):

        #lyrics_structured -> Reveals how lyrics form complete sentences

        #lyrics_timing -> Reveals when each of the word from the lyrics fit together

        # Periods are missing from the timing
        # apostophes appear to be present

        self._verify_lyrics(lyrics_stuctured, lyrics_timing)

        hello = 2



    def fetch_and_align_lyrics(self, path_to_audio, recursive=False, destructive=False, keep_lyrics=False):
        ''' Fetches the things, and writes them down

        '''
        audio_files = self._get_all_audio(path_to_audio, recursive)

        # Filter for existing lyric files here

        #self.lyric_fetcher.

        json_out_fds = {}

        for audio_file in audio_files:
            logging.warn(f"Processing: {audio_file}")

            lyrics = None

            for lyric_fetcher in self.all_lyric_fetchers:

                lyrics = lyric_fetcher.fetch_lyrics(audio_file)

                if lyrics:
                    break

            if lyrics is None:
                logging.warn("Unable to retrieve lyrics.")
                continue

            lyrics_sanitized = self._sanitize_lyrics(lyrics)

            # Turn list of strings into single string without double spaces
            complete_lyric_string = ' '.join(lyrics_sanitized)
            complete_lyric_string = ' '.join(complete_lyric_string.split())

            lyric_sanitized_file = audio_file.with_suffix(".lyrics_sanitized")

            with open(lyric_sanitized_file, 'wt') as file:
                file.write(complete_lyric_string)

            # TODO: Write intermediate lyric file on-disk for aligner tool to use

            intermediate_lyric_file = "path"

            # Hard-coded for 'Go-go's vacation' currently
            aligned_lyrics = self.lyric_aligner.align_lyrics(audio_file, lyric_sanitized_file)

            #aligned_lyrics = self._parse_aligned_lyrics(path_to_synchronized_lyrics)

            json_to_write = self._create_lyrics_json(lyrics_sanitized, aligned_lyrics)

            path_to_json_lyrics_file = audio_file.with_suffix(".a_good_extension")

            # horsie2 = 2

            # lyrics = self.lyric_fetcher.fetch_lyrics("The Go-Go's", "Vacation")

            json_out_fds["debug_meta_lyrics"] = lyrics

            with open(path_to_json_lyrics_file, 'w') as file:
                json.dump(json_out_fds, file)




        hello = 2