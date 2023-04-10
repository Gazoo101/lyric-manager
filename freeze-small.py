"""
A cx_Freeze-based packaging/freezing script for LyricManager.

Execute this build script be either:
    - Running freeze-lyricmanager.bat (in the right Python Venv)
    - Executing 'Python freeze.py build' (in the right Python Venv)

Python 3.8+ is required as it (apparently) handles packaging/freezing libraries in a different (better) manner.
See this discussion with cx_Freeze maintainer: https://github.com/marcelotduarte/cx_Freeze/issues/1498

"""
# Python
import shutil
import platform
from pathlib import Path
from datetime import datetime

# 3rd Party
from cx_Freeze import Executable, setup


# 1st Party
# According to this post: https://stackoverflow.com/questions/27496021/cx-freeze-including-my-own-modules
# Setup-tools / cx-Freeze apparently discovers local modules by having the sys.path modified.
from src.developer_options import DeveloperOptions

# Default string by cx_freeze: exe.win-amd64-3.11

def create_build_path(application_name: str) -> str:
    """ Generates a path containing the application version number and datetime of the "build".

    Output Examples:
        - build\\v0.5---2023-03-16_07_54_16\\<application_name>-v0.5-Windows
        - build\\v0.5---2023-04-22_10_11_09\\<application_name>-v0.5-Windows
        - build\\v0.7---2023-04-22_10_11_09\\<application_name>-v0.7-Linux
                  ^                           ^
                  |                          Release folder, automatically zipped for distribution.
                 Dev. folder to track version/time of build
    """
    #machine_architecture = platform.machine() # AMD64
    operating_system = platform.system()

    now = datetime.now()
    timestamp_folder_name = now.strftime("%Y-%m-%d_%H_%M_%S")

    execution_folder = f"{application_name}-v{DeveloperOptions.version}-{operating_system}"

    build_path = Path("./build/") / f"v{DeveloperOptions.version}---{timestamp_folder_name}" / execution_folder

    return str(build_path)


# The base primarily determines whether a command-line window will be shown during execution or not.
base = None
# While LyricManager is under heavy development, we want the command-line window to show
# if sys.platform == "win32":
#     base = "Win32GUI"

build_path = create_build_path("LyricManager")

build_exe_options = {
    # Circular import failures (previously caused by svspy importing sklearn) can be resolved by explicitly
    # adding parts of the packages triggering the circular imports, as shown below.
    # Consider explicitly including one or more of these if circular import error occurs.
    # "packages": [
    #     "scipy.optimize",
    #     "scipy.integrate"
    # ],
    # exclude packages that are not really needed
    "excludes": [
        "tkinter",
        "unittest", # Including svspy triggers this package to be required
        #"email", # Needed by .genius?
        "xml",
        #"pydoc", # it was needed by svspy?
        "PySide6.QtNetwork"
    ],
    # *Substantially* reduces the size of the created frozen package.
    "zip_include_packages": ["PySide6"],
    "include_files": [
        ("resources/lyric_manager_window_main.ui", "resources/lyric_manager_window_main.ui"),
        ("resources/lyric_manager_window_settings.ui", "resources/lyric_manager_window_settings.ui")
    ],
    "build_exe": str(build_path)
}

executables = [Executable(
    "lyric_manager_gui.py",
    base=base,
    icon="resources/icons/lyric_manager.ico"
)]

setup(
    name="LyricManager",
    version=DeveloperOptions.version,
    description="A lyric management tool.",
    options={"build_exe": build_exe_options},
    executables=executables,
)

# Zip for distribution...
shutil.make_archive(build_path, 'zip', build_path)

print('AGAGAGAA ')