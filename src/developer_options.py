# Python
from enum import Enum, auto

# 3rd Party


# 1st Party


class DeveloperOptions():
    """ Developer options for LyricManager """


    """ Major options """
    version = 0.4

    class ExecutionMode(Enum):
        # Standard internal release. Should override all debugging related options.
        ReleaseInternal = auto()

        ReleaseExternal = auto()

        LyricParsing = auto()

    # LyricManager offers various execution modes to allow for faster iterative development for a select set of code
    # paths:
    #
    # ExecutionMode.ReleaseInternal: TBD
    # ExecutionMode.ReleaseExternal: TBD

    execution_mode = ExecutionMode.ReleaseInternal


    @classmethod
    def is_release(cls):
        return cls.execution_mode == cls.ExecutionMode.ReleaseExternal

    # The Qt Gui uses multi-threading to allow the interface to remain responsive while performing computationally
    # intensive work. Settings this flag to false forces LyricManager to be single-threaded, significantly easing debugging
    # and developing new code.
    gui_multithreading_enabled      = True
    #gui_multithreading_enabled      = False

    @classmethod
    def is_multithreading_enabled(cls):
        return cls.is_release() or cls.gui_multithreading_enabled


    """ Minor options """
