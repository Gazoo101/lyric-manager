"""
A cx_Freeze-based packaging/freezing script for LyricManager.

Execute this build script be either:
    - Running freeze-lyricmanager.bat (in the right Python Venv)
    - Executing 'Python freeze.py build' (in the right Python Venv)

Python 3.8+ is required as it (apparently) handles packaging/freezing libraries in a different (better) manner.
See this discussion with cx_Freeze maintainer: https://github.com/marcelotduarte/cx_Freeze/issues/1498

"""
# Python
import sys
import os

# 3rd Party
from cx_Freeze import Executable, setup


# 1st Party
# According to this post: https://stackoverflow.com/questions/27496021/cx-freeze-including-my-own-modules
# Setup-tools / cx-Freeze apparently discovers local modules by having the sys.path modified.
from src.developer_options import DeveloperOptions


# The base primarily determines whether a command-line window will be shown during execution or not.
base = None
# While LyricManager is under heavy development, we want the command-line window to show
# if sys.platform == "win32":
#     base = "Win32GUI"

options = {
    "build_exe": {
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
            ("resources/lyric_manager_v3.ui", "resources/lyric_manager_v3.ui")
        ]
    }
}

executables = [Executable(
    "lyric_manager_gui.py",
    base=base
    #icon="resources/nameofanicon.ico"
)]

setup(
    name="LyricManager",
    version=DeveloperOptions.version,
    description="A lyric management tool.",
    options=options,
    executables=executables,
)