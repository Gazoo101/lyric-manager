# Python
import subprocess
import logging
from pathlib import Path
import os

# 3rd Party

# 1st Party
from .lyric_aligner_interface import LyricAlignerInterface
from .lyric_aligner_interface import WordAndTiming

class LyricAlignerNUSAutoLyrixAlignOffline(LyricAlignerInterface):

    def __init__(self, path_temp_dir, path_to_aligner):
        super().__init__(path_temp_dir)
        self.path_aligner = path_to_aligner

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

        # Hard code to ensure this works with vacation.wav etc.
        path_to_example_folder = Path('/home/lasse/AudioAlignment/NUSAutoLyrixAlign/')
        path_to_audio_file = self.path_aligner / 'example/Vacation.wav'
        path_to_lyric_input = self.path_aligner / 'example/vacation.txt'
        path_to_temp_file = self.path_aligner / 'example/vacation_aligned.txt'

        path_to_kaldi_simg = self.path_aligner / 'kaldi.simg'
        path_to_alignment_script = self.path_aligner / 'RunAlignment.sh'


        process = ['singularity', 'shell', 'kaldi.simg', '-c', f'"./RunAlignment.sh {path_to_audio_file} {path_to_lyric_input} {path_to_temp_file}"']

        process = ['singularity', 'shell', 'kaldi.simg', '-c', f'"./RunAlignment.sh example/Vacation.wav example/vacation.txt example/vacation_aligned.txt"']

        # worx
        process = ['singularity', 'shell', 'kaldi.simg', '-c', f'"./RunAlignment.sh"']

        process = ['singularity', 'shell', 'kaldi.simg', '-c', f'"./RunAlignment.sh" {path_to_audio_file} {path_to_lyric_input} {path_to_temp_file}']


        # This worked:
        # singularity shell kaldi.simg -c "./RunAlignment.sh example/Vacation.wav example/vacation.txt example/vacation_aligned.txt"
        # singularity shell kaldi.simg -c "./RunAlignment.sh example/Vacation.wav example/vacation.txt example/vacation_aligned.txt"

        # Step 1: Run that

        # TEST AND DEVELOP THIS BIT ON LINUX

        # debug
        process_executed = " ".join(process)
        print(process_executed)
        logging.debug(f"Executing command: {process_executed}")

        #os.chdir(self.path_aligner)

        #test = os.getcwd()

        subprocess.run(process, cwd=self.path_aligner)
        #
        #f'singularity shell kaldi.simg -c "./RunAlignment.sh <input audio file> <input lyrics file> <output file>"'

        

        word_timings = self._convert_to_wordandtiming(path_to_temp_file)

        return word_timings