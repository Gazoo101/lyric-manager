# Python
from typing import Iterable

# 3rd Party
import tqdm
from tqdm.contrib.logging import logging_redirect_tqdm # Move into Cli

# 1st Party



class ProgressItemGeneratorCLI():
    """ This class serves as one of two loop wrappers to enable both Cli and Gui to share the same code path.

    LyricManagerBase implements the lyric management code run by both the Command-Line Interface, and the Graphical
    User-interface. This class, and the sister-class ProgressItemGeneratorGUI, allow the same code
    path to be used to manage lyrics, regardless of User Interface.
    """

    def __call__(self, elements: Iterable, **kwargs):
        """ Yields a single element and triggers progress printing via tqdm.
        
        In order to make it possible to change the description of the progress bar during execution, this class must
        retain a reference to it for use in set_description(). Unfortunately, it leads to some slightly smelly code
        that sets the reference of the progress_bar as part of this call.
        """

        with logging_redirect_tqdm():
            # Retain a reference so its decription can be updated.
            self.progress_bar_current = tqdm.tqdm(elements, **kwargs)

            for one_element in self.progress_bar_current:
                yield one_element


    def set_description(self, description):
        if self.progress_bar_current:
            self.progress_bar_current.set_description(description)