# Python
import subprocess
import logging
from pathlib import Path
import os
from datetime import datetime

# 3rd Party

# 1st Party
from .lyric_aligner_interface import LyricAlignerInterface
from .lyric_aligner_interface import WordAndTiming
import components
#from components import FileOps
#from components import FileOperations

class LyricAlignerNUSAutoLyrixAlignOffline(LyricAlignerInterface):
    '''
        https://github.com/chitralekha18/AutoLyrixAlign

        - Inserts "BREATH*" in-between lyrics
        - Appears to handle .mp3 as well as .wav...?

    '''

    def __init__(self, path_temp_dir: Path, path_to_aligner: Path, path_to_output_dir: Path = None):
        """

        Args:
            path_temp_dir:
            path_to_aligner:
            path_to_output_dir: If 'None' output files will be placed next to processed files, otherwise
                they'll be place in the path specified in this parameter.
        """

        if " " in str(path_temp_dir):
            error = "LyricAlignerNUSAutoLyrixAlignOffline cannot function with a temporary path containing spaces."
            logging.fatal(error)
            raise RuntimeError(error)

        super().__init__(".nusalaoffline", path_temp_dir, path_to_output_dir)
        self.path_aligner = path_to_aligner
        self.path_to_output_dir = path_to_output_dir

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

            temp = WordAndTiming(word=line_pieces[2], time_start=float(line_pieces[0]), time_end=float(line_pieces[1]))
            timed_words.append(temp)

        return timed_words


    def align_lyrics(self, path_to_audio_file, path_to_lyric_input, use_preexisting=True):
        """ TODO: 1-line explanation

        Copies audio and lyric files to a temporary location in order to then
        execute NUSAutoLyrixAlign, create an aligned lyric text and then copy this
        back.

        NUSAutoLyrixAlign executes via Singularity, and it would appear it doesn't
        handle spaces in path's well. Therefore we eliminate all spaces in the
        temporary pathing.

        Args:
            path_to_audio_file:
            path_to_lyric_input:
            use_preexisting: If a pre-existing alignment file is present, this will be re-used.
        Returns:

        """
        # Check if the saved raw version exists
        if use_preexisting:
            preexisting_aligned_lyric_file = self.get_corresponding_aligned_lyric_file(path_to_audio_file)
            if preexisting_aligned_lyric_file.exists():
                logging.info(f'Found pre-existing NUSAutoLyrixAlign file: {preexisting_aligned_lyric_file}')
                word_timings = self._convert_to_wordandtiming(preexisting_aligned_lyric_file)
                return word_timings

        if not self.path_aligner:
            logging.info('No path provided to NUSAutoLyrixAlign, skipping alignment.')

            if not use_preexisting:
                logging.warning("Without an aligner or access to a pre-existing alignment file, there's little reason to continue")
                raise RuntimeError("No song aligner provided and pre-existing alignment files disallowed.")

            return []

        # TODO: Support raw .wav if there's enough call for it.
        if path_to_audio_file.suffix != ".mp3":
            logging.info("Lyric aligner given non .mp3 file, skipping.")
            return []

        path_temp_file_audio = self.path_temp_dir / "audio.mp3"
        path_temp_file_lyric = self.path_temp_dir / "lyric.txt"

        components.FileOperations.copy_and_rename(path_to_audio_file, path_temp_file_audio)
        components.FileOperations.copy_and_rename(path_to_lyric_input, path_temp_file_lyric)

        path_temp_file_lyric_aligned = self.path_temp_dir / "lyric_aligned.txt"

        process = ['singularity', 'shell', 'kaldi.simg', '-c', f'"./RunAlignment.sh" "{path_temp_file_audio}" "{path_temp_file_lyric}" "{path_temp_file_lyric_aligned}"']

        process_executed = " ".join(process)
        print(process_executed)
        logging.debug(f"Executing command: {process_executed}")

        #os.chdir(self.path_aligner)

        #test = os.getcwd()

        # Actual execution
        datetime_before_alignment = datetime.now()
        subprocess.run(process, cwd=self.path_aligner)
        
        # The most dependable way to ensure that the NUSAutoLyrixAlign process succeeded, is to
        # check if the temporary output file has been updated.
        if path_temp_file_lyric_aligned.exists() == False:
            logging.warning(f"Unable to create lyrics for {path_to_audio_file}")
            return []

        datetime_lyric_aligned = datetime.fromtimestamp(path_temp_file_lyric_aligned.stat().st_ctime)

        if datetime_before_alignment > datetime_lyric_aligned:
            logging.warning('Lyric aligned existed before completion O_o')
            return []

        # While we're building this tool, we'll maintain copies of the aligned lyrics in order
        # to repeat the 'aligned lyrics' => 'json lyrics' code
        path_to_aligned_lyric_file = self.copy_aligned_lyrics_output(path_to_audio_file, path_temp_file_lyric_aligned)
        
        word_timings = self._convert_to_wordandtiming(path_to_aligned_lyric_file)

        return word_timings


    def align_lyrics_part_working(self, path_to_audio_file, path_to_lyric_input):

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

        #subprocess.run(process, cwd=self.path_aligner)

        #
        #f'singularity shell kaldi.simg -c "./RunAlignment.sh <input audio file> <input lyrics file> <output file>"'

        

        word_timings = self._convert_to_wordandtiming(path_to_temp_file)

        return word_timings