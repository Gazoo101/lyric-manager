# Python
import sys
import logging
import traceback

# 3rd Party
# The error "version `GLIBC_2.28' not found" will occur on Ubuntu 18.04, as Qt6 requires Ubuntu 20.04
from PySide6 import QtCore


# 1st Party


class WorkerSignals(QtCore.QObject):
    """ Defines a small set of signals to be provided via worker a thread, defined below. """
    finished = QtCore.Signal(object)
    progress = QtCore.Signal(float)
    task_description = QtCore.Signal(str)
    error = QtCore.Signal(tuple)
    # result = QtCore.Signal(object)


# Inspiration: https://www.pythonguis.com/tutorials/multithreading-pyside6-applications-qthreadpool/
class GuiWorker(QtCore.QRunnable):
    """ A simple worker class accepting a single function along with arguments to be passed to it upon execution. """

    def __init__(self, fn, *args, **kwargs):
        super(GuiWorker, self).__init__()

        # Store constructor arguments (re-used for processing)
        self.fn = fn
        self.args = args
        self.kwargs = kwargs

        self.signals = WorkerSignals()

    def set_fn(self, fn, *args, **kwargs):
        self.fn = fn
        self.args = args
        self.kwargs = kwargs

    # At the time of writing, it is unclear to me if this function benefits from being declared a @QtCore.Slot().
    # It depends on whether the function is triggered via a Signal or not, I think.
    @QtCore.Slot()
    def run(self):
        """ Executes self.fn with the provided parameters in self.args and self.kwargs. """
        try:
            logging.info(f"worker executing: {self.kwargs}")
            # result currently remains unused.
            result = self.fn(*self.args, **self.kwargs)
            #result = self.fn(*self.args, **self.kwargs, progress=self.signals.progress)
        except:
            traceback.print_exc()
            exctype, value = sys.exc_info()[:2]
            self.signals.error.emit((exctype, value, traceback.format_exc()))
        # else:
        #     self.signals.result.emit(result)  # Return the result of the processing
        finally:
            self.signals.finished.emit(result)  # Done