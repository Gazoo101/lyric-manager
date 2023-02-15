# Python
from typing import Iterable

# 3rd Party
# The error "version `GLIBC_2.28' not found" will occur on Ubuntu 18.04, as Qt6 requires Ubuntu 20.04
from PySide6 import QtCore

# 1st Party


class ProgressItemGeneratorGUI():
    """ This class serves as one of two loop wrappers to enable both Cli and Gui to share the same code path.

    """

    def __init__(self, signal_progress: QtCore.Signal(float), signal_task_description: QtCore.Signal(str)) -> None:
        self.progress = signal_progress
        self.task_description = signal_task_description

    def __call__(self, elements: Iterable, **kwargs):
        """ Yields a single element and triggers progress signal.
        
        The 'sister-class' ProgressItemGeneratorCLI relies on tqdm to report on progress in a command-line environment.
        We purposefully mirror the types of parameters tqdm expects to allow the calling code to use
        either wrapper seamlessly, e.g. 'desc' is used to set the description field in the GUI progress bar, just like
        it's used in tqdm.
        """
        total = len(elements)
        progress = 0

        task_description = kwargs.get('desc', None)
        if task_description:
            self.task_description.emit(task_description)
        
        if self.progress:
            self.progress.emit(0)
        
        for one_element in elements:
            
            yield one_element

            # TODO: We suspect that this code doesn't trigger once the final element has 'yielded'. This leads to the
            # progress bar never being set to 100%. Consider how to work around this limitation.
            progress += 1

            percentage = (float(progress) / float(total)) * 100
            if self.progress:
                self.progress.emit(percentage)


    def set_description(self, description):
        self.task_description.emit(description)