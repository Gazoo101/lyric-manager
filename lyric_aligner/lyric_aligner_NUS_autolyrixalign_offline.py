# Python
import subprocess
import logging

# 3rd Party

# 1st Party
from .lyric_aligner_interface import LyricAlignerInterface
from .lyric_aligner_interface import WordAndTiming

class LyricAlignerNUSAutoLyrixAlignOffline(LyricAlignerInterface):

    def __init__(self, path_temp_dir):
        super().__init__(path_temp_dir)

    def _convert_to_wordandtiming(self, path_to_aligned_lyrics):

        # Input looks like this:
        # 9.69 10.53 NO
        # 10.53 11.52 MORE
        # 12.03 12.81 CARE
        # 12.81 13.83 FREE
        # 14.31 16.11 LAUGHTER
        # 18.75 20.85 SILENCE

        with open(path_to_aligned_lyrics) as file:
            text_lines = file.readlines()

        timed_words = []

        for line in text_lines:
            line = line.strip()
            line_pieces = line.split(' ')

            temp = WordAndTiming(word=line_pieces[2], time_start=line_pieces[0], time_end=line_pieces[1])
            timed_words.append(temp)

        return timed_words

    def align_lyrics(self, path_to_audio_file, path_to_lyric_input):

        # <audio_file>.mp3   =>   <audio_file>.aligned_lyric
        path_to_temp_file = path_to_audio_file.with_suffix(".lyrics_aligned")

        process = ["singularity", "shell", "kaldi.simg", "-c", f"./RunAlignment.sh {path_to_audio_file} {path_to_lyric_input} {path_to_temp_file}"]

        # TEST AND DEVELOP THIS BIT ON LINUX

        # debug
        #process_executed = process.join(" ")
        #logging.debug(f"Executing command: {process_executed}")

        #subprocess.run(process)
        #
        #f'singularity shell kaldi.simg -c "./RunAlignment.sh <input audio file> <input lyrics file> <output file>"'

        

        word_timings = self._convert_to_wordandtiming(path_to_temp_file)

        return word_timings