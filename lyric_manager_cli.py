# Python
import sys
from pathlib import Path
from argparse import ArgumentParser


# 3rd Party
from omegaconf import OmegaConf, MISSING, SCMode

# 1st Party
from src.lyric_manager_base import LyricManagerBase
from src.lyric_processing_config import Config
from src.cli import ProgressItemGeneratorCLI



class LyricManagerCommandLineInterface(LyricManagerBase):

    def __init__(self, incoming_arguments: list[str]) -> None:
        super().__init__()
        
        parser = self._create_command_lineparser()
        parsed_arguments = parser.parse_args(incoming_arguments)

        config = self._read_config(parsed_arguments.path_to_config_file)

        loop_wrapper = ProgressItemGeneratorCLI()
        self.fetch_and_align_lyrics(config, loop_wrapper)


    def _create_command_lineparser(self):
        parser = ArgumentParser()

        # Immediately convert the single positional argument into an absolute pathlib.Path
        parser.add_argument("path_to_config_file", nargs="?", default="./settings_example.yaml", type=lambda p: Path(p).absolute())

        return parser
    

    def _read_config(self, path_to_config_file: Path):

        omegaconf_lyricmanager_config_schema = OmegaConf.structured(Config)
        lyricmanager_config_from_disk = OmegaConf.load(path_to_config_file)

        validated_config = OmegaConf.merge(omegaconf_lyricmanager_config_schema, lyricmanager_config_from_disk)

        # Turn dict-like structure into dataclass object
        config = OmegaConf.to_container(validated_config, structured_config_mode=SCMode.INSTANTIATE)

        return config


if __name__ == "__main__":

    # Test with an override configuration.
    #sys.argv.append('settings.yaml')

    LyricManagerCommandLineInterface(sys.argv[1:])

