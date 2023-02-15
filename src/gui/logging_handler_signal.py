# Python
import logging

# 3rd Party
from PySide6 import QtCore

# 1st Party

# Inspirational source for this code:
# https://stackoverflow.com/questions/43595995/python-logging-to-pyside-widget-without-delay

class QSignaler(QtCore.QObject):
    """ A simpler Qt Signal class, encapsulating a single signal. """
    log_message = QtCore.Signal(str) # Possibly upgrade to 'unicode' to support UTF-8?


class LoggingHandlerSignal(logging.Handler):
    """Logging handler to emit QtSignal with log record text."""

    def __init__(self, *args, **kwargs):
        super(LoggingHandlerSignal, self).__init__(*args, **kwargs)
        self.emitter = QSignaler()

    def emit(self, record):
        """ Overwritten function triggered via Python's logging module. """
        formatted_message = self.format(record)
        self.emitter.log_message.emit(formatted_message)

        # If the Qt GUI isn't responding in a timely fashion to logging signals, it's possible to expedite this
        # behavior by manually triggering the .processEvents() function: QtGui.qApp.processEvents()
