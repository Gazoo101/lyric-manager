# Python
import sys
from pathlib import Path
from argparse import ArgumentParser

# 3rd Party
from omegaconf import OmegaConf, SCMode

# 1st Party
from src.lyric_manager_base import LyricManagerBase
from src.lyric_processing_config import Settings
from src.cli import ProgressItemGeneratorCLI
from src.developer_options import DeveloperOptions

class LyricManagerCommandLineInterface(LyricManagerBase):
    """ LyricManager's command-line interface implementation.

    LyricManager's two interface implementations (Command-line- and Graphical User Interface) each implement settings
    handling differently, due to their differing modes of operation.

    LyricManagerCommandLineInterface operates in a 'one-shot' fashion without an event loop. On-disk settings are parsed
    via .yaml files that are turned into dataclass objects via OmegaConf. Every single setting is managed via the
    incoming .yaml file.

    LyricManagerGraphicUserInterface operates in a persistent manner, via an event loop. Settings are managed via the
    Qt Gui which in-turn relies on QSettings to store any persistent settings on-disk, such as working directory or
    window spawn position and size.
    """

    def __init__(self, incoming_arguments: list[str]) -> None:
        parser = self._create_command_lineparser()
        parsed_arguments = parser.parse_args(incoming_arguments)

        settings: Settings = self._read_settings(parsed_arguments.path_to_settings_file)

        super().__init__(settings.data.output.path_to_working_directory, settings.data.output.path_to_reports)

        loop_wrapper = ProgressItemGeneratorCLI()
        self.fetch_and_align_lyrics(settings, loop_wrapper)


    def _create_command_lineparser(self):
        parser = ArgumentParser()

        # Immediately convert the single positional argument into an absolute pathlib.Path
        parser.add_argument("path_to_settings_file", nargs="?", default="./settings_example.yaml", type=lambda p: Path(p).absolute())
        parser.add_argument('--version', action='version', version=f'LyricManager {DeveloperOptions.version}')

        return parser
    

    def _read_settings(self, path_to_settings_file: Path):

        omegaconf_lyricmanager_settings_schema = OmegaConf.structured(Settings)
        lyricmanager_settings_from_disk = OmegaConf.load(path_to_settings_file)

        validated_settings = OmegaConf.merge(omegaconf_lyricmanager_settings_schema, lyricmanager_settings_from_disk)

        # Turn dict-like structure into dataclass object
        settings = OmegaConf.to_container(validated_settings, structured_config_mode=SCMode.INSTANTIATE)

        return settings


if __name__ == "__main__":

    incoming_parameters = sys.argv[1:]

    # Debug/Test overrides
    # incoming_parameters = ["-h"]
    # incoming_parameters = ["--version"]
    #incoming_parameters = ["settings.yaml"]
    #incoming_parameters = ["settings-scenario1.yaml"]
    #incoming_parameters = ["settings-scenario2.yaml"]
    incoming_parameters = ["settings-scenario3-street-hoops.yaml"]
    #incoming_parameters = ["settings-Scenario-LocalLyricsWithExpansion.yaml"]
    #incoming_parameters = ["settings-genius-all-songs.yaml"]

    LyricManagerCommandLineInterface(incoming_parameters)

