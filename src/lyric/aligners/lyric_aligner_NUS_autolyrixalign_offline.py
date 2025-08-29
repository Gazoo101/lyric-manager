# Python
import os
import subprocess
import logging
from pathlib import Path
from datetime import datetime

# 3rd Party


# 1st Party
from .lyric_aligner_interface import LyricAlignerInterface
from .lyric_aligner_interface import WordAndTiming

from ...components import FileOperations

from ...developer_options import DeveloperOptions


class LyricAlignerNUSAutoLyrixAlignOffline(LyricAlignerInterface):
    """ Lyric aligner based on the offline version of the NUS Auto Lyrix Align project which can be downloaded here:
    https://github.com/chitralekha18/AutoLyrixAlign

    *** Installation notes:

    Tested to work under Ubuntu 18.04 and 22.04. Download the AutoLyrixAlign package, follow the included readme.txt
    installation instructions. The following additional instructions may be helpful on Ubuntu 22.04
    (and possibly earlier ubuntu versions):

    Singularity 2.5.2 can be downloaded here: https://singularityware.github.io/all-releases

    apt-get build-essential     | To install C compiler
    apt-get python-is-python3   | To give configure/make access to Python (it expects 'Python' to exist)
    apt-get libarchive-dev      | Required to build Singularity 2.5.2

    Inside the Singularity 2.5.2 source, the following file: /src/lib/image/squashfs/mount.c

    Must have ~line 55 altered...

    FROM:   if ( singularity_mount(loop_dev, mount_point, "squashfs", MS_NOSUID|MS_RDONLY|MS_NODEV, "errors=remount-ro") < 0 ) {
    TO:     if ( singularity_mount(loop_dev, mount_point, "squashfs", MS_NOSUID|MS_RDONLY|MS_NODEV, NULL) < 0 ) {

    or else, the image will not mount and the aligner will not run.

    *** Auto Lyrix Align Dev. Notes:

    - May insert "BREATH*" either at mis- or non-aligned words.
    - Handles .mp3 files and .wav
    - A small selection of songs, e.g. "The Young Punx - All These Things Are Gone" cause the pre-processing step to
      lock up.
        - Preliminary investigations indicate that 'scipy.signal.resample()' appears to simply never return, or at least
          not return within a reasonable amount of time.
    """

    def __init__(self, path_aligner_temp_dir: Path, path_to_aligner: Path, path_to_output_dir: Path = None):
        """

        Args:
            path_aligner_temp_dir: A path without spaces for NUSAutoLyrixAlign to align audio with lyrics.
            path_to_aligner:
            path_to_output_dir: If 'None' output files will be placed next to processed files, otherwise
                they'll be place in the path specified in this parameter.
        """

        if " " in str(path_aligner_temp_dir):
            error = "LyricAlignerNUSAutoLyrixAlignOffline cannot function with a temporary path containing spaces."
            logging.fatal(error)
            raise RuntimeError(error)

        super().__init__(".nusalaoffline", path_aligner_temp_dir, path_to_output_dir)
        self.path_aligner = path_to_aligner
        self.path_to_output_dir = path_to_output_dir

        self.aligner_functional = False

        if not path_to_aligner:
            logging.warning("No path to NUSAutoLyrixAlign provided, can only run on cached alignment output files.")
            return

        # Find critical files
        path_to_alignment_script = path_to_aligner / "RunAlignment.sh"
        path_to_singularity_image = path_to_aligner / "kaldi.simg"

        if not path_to_alignment_script.exists() or not path_to_singularity_image.exists():
            logging.warning("NUSAutoLyrixAlign is missing vital files to execute properly, can only run on cached files.")
            return
        
        self.aligner_functional = True


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


    def align_lyrics(self, path_to_audio_file, path_to_lyric_input, use_preexisting=True) -> list[WordAndTiming]:
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
            preexisting_aligned_lyric_file = self._get_cached_aligned_output_file(path_to_audio_file)

            #preexisting_aligned_lyric_file = self.get_corresponding_aligned_lyric_file(path_to_audio_file)
            if preexisting_aligned_lyric_file:
                logging.info(f'Found pre-existing NUSAutoLyrixAlign file: {preexisting_aligned_lyric_file}')
                word_timings = self._convert_to_wordandtiming(preexisting_aligned_lyric_file)
                return word_timings
            
        if not self.aligner_functional:
            logging.info("Missing vital components to execute aligner - skipping alignment.")
            return []


        datetime_before_alignment = datetime.now()
        path_temp_file_lyric_aligned = self._align_lyrics_internal(path_to_audio_file, path_to_lyric_input)
        
        # The most dependable way to ensure that the NUSAutoLyrixAlign process succeeded, is to
        # check if the temporary output file has been updated.
        if path_temp_file_lyric_aligned.exists() == False:
            logging.warning(f"Unable to create aligned lyrics for {path_to_audio_file}")
            return []

        datetime_lyric_aligned = datetime.fromtimestamp(path_temp_file_lyric_aligned.stat().st_ctime)

        if datetime_before_alignment > datetime_lyric_aligned:
            logging.warning('Lyric aligned existed before completion O_o')
            return []
        
        # 'temp_dir/lyric_aligned.txt' --> 'working_directory/artist - song title.lyric_aligned'
        path_to_aligned_lyric_file = self.copy_aligned_lyrics_to_working_directory(path_temp_file_lyric_aligned, path_to_audio_file)
        
        word_timings = self._convert_to_wordandtiming(path_to_aligned_lyric_file)

        return word_timings


    def _align_lyrics_internal(self, path_to_audio_file: Path, path_to_lyric_input: Path):
        """ Copies audio and lyric file to a working directory, performs alignment, returns the path to this file. """
        logging.info(f"Aligment audio: {path_to_audio_file}")
        logging.info(f"Aligment lyric: {path_to_lyric_input}")

        # TODO: Upgrade to handle mp3 to wav conversion as that seems to go side-ways for Singularity...
        # Update, fixing conversion didn't help, it's in the scipy call that things go off the rails...

        path_temp_file_audio: Path = self.path_aligner_temp_dir / "audio.notset"
        path_temp_file_lyric: Path = self.path_aligner_temp_dir / "lyric.txt"

        # Update the temporary file suffix (.notset), to the proper audio file extension, e.g. .mp3 or .wav or .aiff
        path_temp_file_audio = path_temp_file_audio.with_suffix(path_to_audio_file.suffix)

        FileOperations.copy_and_rename(path_to_audio_file, path_temp_file_audio)
        FileOperations.copy_and_rename(path_to_lyric_input, path_temp_file_lyric)

        path_temp_file_lyric_aligned = self.path_aligner_temp_dir / "lyric_aligned.txt"

        match DeveloperOptions.model_execution_application:
            case DeveloperOptions.ModelExecutionApplication.Apptainer:
                arguments_list = ['apptainer', 'exec', 'kaldi.simg', './RunAlignment.sh', f'"{path_temp_file_audio}"', f'"{path_temp_file_lyric}"', f'"{path_temp_file_lyric_aligned}"']
                arguments_string = " ".join(arguments_list)
                # Without Shell, Apptainer appears to not have access to relative paths, so moving the aligned text output from 'AlignedLyricsOutput/alignedoutput.txt' to somewhere else.
                use_shell = True
                
            case DeveloperOptions.ModelExecutionApplication.Singularity:
                arguments_list = ['singularity', 'shell', 'kaldi.simg', '-c', f'"./RunAlignment.sh" "{path_temp_file_audio}" "{path_temp_file_lyric}" "{path_temp_file_lyric_aligned}"']
                arguments_string = " ".join(arguments_list)
                use_shell = False
                

        # logging.info() -- Enter details of audio file (original name here)
        logging.info(f"Processing Audio: {path_to_audio_file.name}")
        logging.info(f"Executing command: {arguments_string}")
        result = subprocess.run(arguments_string,
                                shell=use_shell,
                                cwd=self.path_aligner,
                                check=True)

        if result.returncode != 0:
            logging.warning("Lyric alignment did not complete as expected.")

        return path_temp_file_lyric_aligned

