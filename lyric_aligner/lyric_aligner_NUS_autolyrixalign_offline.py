# Python
import subprocess
import logging
from pathlib import Path
from datetime import datetime

# 3rd Party

# 1st Party
from .lyric_aligner_interface import LyricAlignerInterface
from .lyric_aligner_interface import WordAndTiming
import components


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

        if not path_to_aligner:
            raise Exception("No path to NUSAutoLyrixAlign provided. No alignment can take place.")

        # Find one or two critical files
        path_to_alignment_script = path_to_aligner / "RunAlignment.sh"
        path_to_singularity_image = path_to_aligner / "kaldi.simg"

        if not path_to_alignment_script.exists() or not path_to_singularity_image.exists():
            raise Exception("NUSAutoLyrixAlign is missing vital files to execute properly.")

        # Test these things:
        # song = "/home/lasse/Workspace/audio_to_align/50 Cent - In da Club.mp3"
        # lyrics = "/home/lasse/Workspace/lyric-manager/working_directory/50 Cent - In da Club.alignment_ready"
        # self._align_lyrics_internal(song, lyrics)

        # Works...
        # song = "/home/lasse/Workspace/audio_to_align/Street Hoop OST/612 - Street Hoop - BODY’S POWER.mp3"
        # lyrics = "/home/lasse/Workspace/lyric-manager/working_directory/612 - Street Hoop - BODY’S POWER.alignment_ready"
        # self._align_lyrics_internal(song, lyrics)

        # song = "/home/lasse/Workspace/audio_to_align/Street Hoop OST/212 - Street Hoop - FUNKY HEAT.mp3"
        # lyrics = "/home/lasse/Workspace/lyric-manager/working_directory/212 - Street Hoop - FUNKY HEAT.alignment_ready"
        # self._align_lyrics_internal(song, lyrics)

        #song = "/home/lasse/Workspace/audio_to_align_failure_cases/The Young Punx - All These Things Are Gone.mp3"

        #"The Young Punx - All These Things Are Gone.mp3"

        horse = 2



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


        datetime_before_alignment = datetime.now()
        path_temp_file_lyric_aligned = self._align_lyrics_internal(path_to_audio_file, path_to_lyric_input)
        
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


    def _align_lyrics_internal(self, path_to_audio_file: Path, path_to_lyric_input: Path):
        """ Copies audio and lyric file to a working directory, performs alignment, returns the path to this file. """
        logging.info(f"Aligment audio: {path_to_audio_file}")
        logging.info(f"Aligment lyric: {path_to_lyric_input}")

        # TODO: Upgrade to handle mp3 to wav conversion as that seems to go side-ways for Singularity...
        # Update, fixing conversion didn't help, it's in the scipy call that things go off the rails...

        path_temp_file_audio: Path = self.path_temp_dir / "audio.notset"
        path_temp_file_lyric: Path = self.path_temp_dir / "lyric.txt"

        # Update the temporary file suffix (.notset), to the proper audio file extension, e.g. .mp3 or .wav or .aiff
        path_temp_file_audio = path_temp_file_audio.with_suffix(path_to_audio_file.suffix)

        components.FileOperations.copy_and_rename(path_to_audio_file, path_temp_file_audio)
        components.FileOperations.copy_and_rename(path_to_lyric_input, path_temp_file_lyric)

        path_temp_file_lyric_aligned = self.path_temp_dir / "lyric_aligned.txt"

        process = ['singularity', 'shell', 'kaldi.simg', '-c', f'"./RunAlignment.sh" "{path_temp_file_audio}" "{path_temp_file_lyric}" "{path_temp_file_lyric_aligned}"']

        process_executed = " ".join(process)

        # logging.info() -- Enter details of audio file (original name here)
        logging.info(f"Processing Audio: {path_to_audio_file.name}")
        logging.info(f"Executing command: {process_executed}")
        subprocess.run(process, cwd=self.path_aligner)

        return path_temp_file_lyric_aligned

