# Python
import os
import sys
import logging
from pathlib import Path
from typing import Optional, List

# 3rd Party
from PySide6 import QtCore, QtWidgets, QtGui
from PySide6.QtWidgets import QMainWindow, QListWidget, QPlainTextEdit, QListWidgetItem, QAbstractItemView
from PySide6.QtWidgets import QRadioButton, QTableWidget, QProgressBar, QPushButton, QCheckBox
from PySide6.QtUiTools import QUiLoader
from PySide6.QtCore import QFile, QDir, qDebug, QSettings

# 1st Party
from src.developer_options import DeveloperOptions

from src.gui import QListWidgetDragAndDrop
from src.gui import LoggingHandlerSignal

from src.lyric_manager_base import LyricManagerBase
from src.lyric_processing_config import Settings
from src.lyric.dataclasses_and_types import LyricFetcherType
from src.lyric.dataclasses_and_types import LyricAlignerType

def bind_class_property_to_qt_widget_property(objectName, propertyName):
    """ Binds a Python class property to a given Qt widget property.

    Two-way binding is a commonly used pattern. PySide6 provides support for this, but is rather boiler-plate heavy:
    https://doc.qt.io/qtforpython/PySide6/QtCore/Property.html

    Unfortunately, because property() uses Descriptors (https://docs.python.org/3/howto/descriptor.html) it acts on the
    class, *not* the instance. Hence, its use *must* occur with a class property, *not* instance property. E.g.

    class MyApplication(...):

        # Ok
        path_to_asset = bind_class_property_to_qt_widget_property("lineEditPathToAsset", "text")

        def __init__(self):
            # Not Ok
            self.path_to_asset = bind_class_property_to_qt_widget_property("lineEditPathToAsset", "text")

    Inspired by:
    https://wiki.python.org/moin/PyQt/Binding%20widget%20properties%20to%20Python%20variables
    https://stackoverflow.com/questions/69529864/binding-widget-properties-to-python-variables
    """

    def getter(self):
        return self.widget_main_window.findChild(QtCore.QObject, objectName).property(propertyName)
        
    def setter(self, value):
        self.widget_main_window.findChild(QtCore.QObject, objectName).setProperty(propertyName, value)
    
    return property(getter, setter)


class LyricManagerGraphicUserInterface(LyricManagerBase, QtCore.QObject):
    """ LyricManager's graphical user interface implementation.

    LyricManager's two interface implementations (Command-line- and Graphical User Interface) each implement settings
    handling differently, due to their differing modes of operation.

    LyricManagerCommandLineInterface operates in a 'one-shot' fashion without an event loop. On-disk settings are parsed
    via .yaml files that are turned into dataclass objects via OmegaConf. Every single setting is managed via the
    incoming .yaml file.

    LyricManagerGraphicUserInterface operates in a persistent manner, via an event loop. Settings are managed via the
    Qt Gui which in-turn relies on QSettings to store any persistent settings on-disk, such as working directory or
    window spawn position and size.
    """

    # TODO: Consider whether we should just directly access the widgets in the code. This is a bit obscure...
    recursively_parse_folders_to_process = \
        bind_class_property_to_qt_widget_property("checkBox_recursively_parse_folders_to_process", "checked")
    
    overwrite_existing_generated_files = \
        bind_class_property_to_qt_widget_property("checkBox_overwrite_existing_generated_files", "checked")

    
    def _get_checkbox_settings_value_or_default(self, q_settings_name: str, widget_q_checkbox_name):
        """ Helps set default via checkbox default"""

        # This allows for a default setting to pervade
        widget_q_checkbox: QCheckBox = self.widget_main_window.findChild(QCheckBox, widget_q_checkbox_name)
        check_state = self.q_settings.value(q_settings_name, widget_q_checkbox.checkState())
        widget_q_checkbox.setCheckState(check_state)


    def _set_checkbox_settings_value(self, q_settings_name: str, widget_q_checkbox_name):
        widget_q_checkbox: QCheckBox = self.widget_main_window.findChild(QCheckBox, widget_q_checkbox_name)
        self.q_settings.setValue(q_settings_name, widget_q_checkbox.checkState())


    def __init__(self, parent: Optional[QtCore.QObject] = ...) -> None:
        # As we wish to use LyricManagerBase as the focal point for the application, yet we still need the application
        # path, we must manually assemble this here:
        path_to_application_qt_ini_file = Path(sys.argv[0]).parent / "LyricManagerGui.ini"

        self.q_settings = QSettings(str(path_to_application_qt_ini_file), QSettings.IniFormat)
        work_directory = self.q_settings.value("WorkingDirectory", "./WorkingDirectory")
        reports_directory = self.q_settings.value("ReportsDirectory", "./Reports")

        LyricManagerBase.__init__(self, work_directory, reports_directory)
        QtCore.QObject.__init__(self)



        # A bool primarily used to avoid accessing deleted objects during shut-down in self.eventFilter()
        self.is_running = True

        # LyricManager won't need a lot of 
        # Given the small number of expected threads, we leverage the application thread pool, as opposed to
        # instantiating a new one.
        self.thread_pool = QtCore.QThreadPool.globalInstance()
        logging.info(f"Multithreading with maximum {self.thread_pool.maxThreadCount()} threads")

        # We instantiate a raw config object to bind various Gui properties to, to see if that works.
        # For more complicated things, this might not work as easily...
        #self.test_config = Config() # no - undo...

        self._setup_ui("./resources/lyric_manager_v2.ui")

        q_rect_geometry = self.q_settings.value("windowGeometry", self.widget_main_window.geometry())
        self.widget_main_window.setGeometry(q_rect_geometry)

        fetcher_types = self.q_settings.value("Processing/FetcherTypes", [LyricFetcherType.LocalFile])
        aligner_type = self.q_settings.value("Processing/AlignerType", LyricAlignerType.Disabled)
        folders_to_process = self.q_settings.value("Processing/FoldersToProcess", list())

        self._get_checkbox_settings_value_or_default("Processing/RecursivelyParseFolders", "checkBox_recursively_parse_folders_to_process")
        self._get_checkbox_settings_value_or_default("Processing/OverwriteExisting", "checkBox_overwrite_existing_generated_files")

        self._set_selected_lyric_fetcher_types(fetcher_types)
        self._set_selected_lyric_aligner_type(aligner_type)
        self.widget_local_data_sources.add_paths(folders_to_process)

        self.widget_main_window.setWindowTitle(f"LyricManager v. {DeveloperOptions.version}")

        # Causes Qt to trigger this classes eventFilter() to handle incoming events. It's primarily used to respond
        # to key presses, such as Esc to quit.
        self.widget_main_window.installEventFilter(self)

        # To funnel logging calls (e.g. info() warn()) into the Gui, we add a handler which uses Qt's Signal/Slot system
        # to pass these logging messages to a QPlainTextEdit widget.
        # At the time of writing, it is my undestanding that because the signal is 'connected' here, in the main
        # thread, the execution of the 'slot code' will also occur in the 'main thead'. Preliminary testing confirms
        # this behavior. Caution is recommended, as the exact behavior of the threads, event loop, and signal/slots
        # is unclear.
        signal_logger = LoggingHandlerSignal()
        signal_logger.setFormatter(logging.Formatter(self.logging_format, self.logging_format_time))
        signal_logger.emitter.log_message.connect(self.widget_log.appendPlainText)
        logging.getLogger().addHandler(signal_logger)


        logging.info("LyricManager Gui loaded.")


    def _setup_ui(self, path_to_ui_file : str):
        """ Loads a Qt .ui interface via the path provided, and sets up static/dynamic widget behavior.
        
        The order of work is grouped into 3 categories:
            1. Static Gui Elements
            2. Dynamic Gui Elements
            3. Slots/Signals

        Args:
            path_to_ui_file: Path to the .ui file to be loaded.
        """
        ### Static GUI Behavior
        form = QFile(path_to_ui_file)
        form.open(QFile.ReadOnly)

        slicks = form.readAll()

        with open(path_to_ui_file,"r") as f:
            string = f.read()

        qDebug("helpsors")

        # checkBox_recursively_parse_folders_to_process
        # checkBox_overwrite_existing_generated_files
        

        self.widget_main_window : QMainWindow = QUiLoader().load(path_to_ui_file)
        #self.widget_main_window : QMainWindow = QUiLoader().load(form)

        self.widget_log: QPlainTextEdit = self.widget_main_window.findChild(QPlainTextEdit, "plainTextEdit_log")

        self.widget_lyric_sources: QListWidget = self.widget_main_window.findChild(QListWidget, "listWidget_lyricSources")
        self.widget_lyric_aligners: QListWidget = self.widget_main_window.findChild(QListWidget, "listWidget_lyricAligners")

        self.widget_lyric_aligners.setSelectionBehavior( QAbstractItemView.SelectItems )
        self.widget_lyric_aligners.setSelectionMode( QAbstractItemView.SingleSelection )

        for key, fetcher in self.factory_lyric_fetcher.builders.items():
            self._add_fetcher(key.name)

        for key, aligner in self.factory_lyric_aligner.builders.items():
            self._add_aligner(key.name)

        # things = self.widget_lyric_aligners.count()
        # #ttt = self.widget_lyric_aligners.itemAt(0)
        # ttt = self.widget_lyric_aligners.itemAt(40,30)
        # ttt1 = self.widget_lyric_aligners.item(0)
        # ttt2 = self.widget_lyric_aligners.item(1)
        # ttt3 = self.widget_lyric_aligners.item(2)

        # aggagag = self.widget_lyric_aligners.itemWidget(ttt1)

        # dasds = ttt2.name()
        # contents = ttt3.text()

        # ttt4 = self.widget_lyric_aligners.item(3)
        # ttt5 = self.widget_lyric_aligners.item(4)

        #self.widget_lyric_aligners.item(0).setChecked( True )

        self.widget_progress_bar_overall: QProgressBar = self.widget_main_window.findChild(QProgressBar, "progressBar_overall")
        self.widget_progress_bar_overall.setValue(0)
        self.widget_progress_bar_overall.setFormat("- Ready -")

        self._setup_widget_processed_table()

        widget_start_processing = self.widget_main_window.findChild(QPushButton, "pushButton_start_processing")
        widget_start_processing.clicked.connect(self.start_process)

        ### Dynamic GUI Behavior
        self.widget_local_data_sources = self._setup_widget_local_data_sources()

        #self.checkbawks: QCheckBox = self.widget_main_window.findChild(QCheckBox, "checkBox_recursively_parse_folders_to_process")

        #self.checkbawks.value()

        horse = 2
        

        # Set 'Delete' key to remove executable entries if the widget is active
        QtGui.QShortcut(QtGui.QKeySequence("Delete"), self.widget_local_data_sources, self.widget_local_data_sources.remove_selected_items, context=QtCore.Qt.WidgetShortcut)


        ### Slots and signals


    def start_process(self):

        selected_fetcher_types = self._get_selected_lyric_fetcher_types()
        selected_aligner_type = self._get_selected_lyric_aligner_type()
        paths_to_process = self.widget_local_data_sources.get_checked_paths()
        
        config = Settings()

        # xplain that we package gui things into the config file hea!
        config.data.recursively_parse_audio_file_path = self.recursively_parse_folders_to_process
        config.data.overwrite_existing_generated_files = self.overwrite_existing_generated_files

        self.fetch_and_align_lyrics(config)

    def _add_fetcher(self, text: str):
        item = QListWidgetItem(text)
    
        item.setFlags(QtCore.Qt.ItemIsUserCheckable | QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable )
        item.setCheckState(QtCore.Qt.Checked)

        self.widget_lyric_sources.addItem(item)


    def _add_aligner(self, text: str):
        #item = QListWidgetItem(text)

        item = QListWidgetItem(self.widget_lyric_aligners)  # Without this 'parent instantiation' we get nothing in Qt O_o

        radio_button = QRadioButton(text)
    
        #item.setFlags(QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable )

        #self.widget_lyric_aligners.addItem(item)
        self.widget_lyric_aligners.setItemWidget(item, radio_button)

        # TODO: Figure out how to actually get the pointer to this radio button once the list construction is complete
        radio_button.setChecked( True )


    def _setup_widget_processed_table(self):

        # Sources:
        # https://stackoverflow.com/questions/54285057/how-to-include-a-column-of-progress-bars-within-a-qtableview
        # add / remove all rows:
        # https://stackoverflow.com/questions/6957943/how-to-add-new-row-to-existing-qtablewidget

        self.widget_songs_processed: QTableWidget = self.widget_main_window.findChild(QTableWidget, "tableWidget_songs_processed")

        self.widget_songs_processed.insertRow( self.widget_songs_processed.rowCount() )

        progress_bar = QProgressBar()
        progress_bar.setValue(26)
        progress_bar.setAlignment(QtCore.Qt.AlignmentFlag.AlignHCenter)
        

        self.widget_songs_processed.setCellWidget(0,2, progress_bar)






    def show(self):
        """ A pass-through function for QMainWindow.show(). """
        self.widget_main_window.show()

    
    def _setup_widget_local_data_sources(self):
        """ Replaces a specfic QListWidget, with a QListWidgetDragAndDrop, set via QtDesigner in a .ui file.

        This allows us to still rely on QtDesigner to define the position and layout of the QListWidgetDragAndDrop.
        """
        # QListWidget to replace
        widget_list_folders_placeholder: QListWidget = self.widget_main_window.findChild(QListWidget, "listWidget_localDataSources")

        widget_list_local_data_sources = QListWidgetDragAndDrop()
        widget_list_local_data_sources.placeholder_text = "Drag and drop data source folders here..."

        # We need the layout containing the placeholder widget to replace it.
        layout = widget_list_folders_placeholder.parent().layout()
        layout.replaceWidget(widget_list_folders_placeholder, widget_list_local_data_sources)

        # TODO: Confirm if calling deleteLater() is necessary...
        widget_list_folders_placeholder.deleteLater()

        return widget_list_local_data_sources
    

    def eventFilter(self, origin: QtCore.QObject, event: QtCore.QEvent):
        """ An event filter triggered via a QObject recieving all event intended for the QObject.

        The function must be named .eventFilter() as per Qt's API.

        Args:
            origin: The QObject from which the event originated.
            event: The QEvent object for the event itself.
        Returns:
            A bool which informs Qt whether to filter this event out, i.e. not handle it further (True), or continue
            handling it in the remaining event pipeline (False).
        """
        if origin is self.widget_main_window:
            if event.type() == QtCore.QEvent.KeyPress:

                # Special case for .close() - If we're closing the application, we should avoid calling super() as the
                # application itself will soon cease to exist.
                if event.key() == QtCore.Qt.Key_Escape:
                    # Expected to pretty much immediately trigger the QtCore.QEvent.Close case below.
                    self.widget_main_window.close() 

                self.key_press_event(event)
            elif event.type() == QtCore.QEvent.Close:
                
                # Although .saveGeometry() and .restoreGeometry() appear to be the preferred approach to saving and
                # restoring window position and size, it appears have issues working across multiple screens.
                # Unfortunately the two functions automatically convert the QRect object to/from byte-code, so the
                # problem isn't easily further diagnosed. Hence, we instead load/save the raw Geometry Rect object.
                #flux = self.widget_main_window.saveGeometry()

                window_geometry = self.widget_main_window.geometry()

                self.q_settings.setValue("WindowGeometry", window_geometry)
                self.q_settings.setValue("WorkingDirectory", "./WorkingDirectory")

                # Save processing-related settings...
                selected_fetcher_types = self._get_selected_lyric_fetcher_types()
                selected_aligner_type = self._get_selected_lyric_aligner_type()
                #paths_to_process = self.widget_local_data_sources.get_checked_paths()
                paths_to_process = self.widget_local_data_sources.get_paths()

                self.q_settings.setValue("Processing/FetcherTypes", selected_fetcher_types)
                self.q_settings.setValue("Processing/AlignerType", selected_aligner_type)
                self.q_settings.setValue("Processing/FoldersToProcess", paths_to_process)

                self._set_checkbox_settings_value("Processing/RecursivelyParseFolders", "checkBox_recursively_parse_folders_to_process")
                self._set_checkbox_settings_value("Processing/OverwriteExisting", "checkBox_overwrite_existing_generated_files")

                self.is_running = False

        if self.is_running:
            return super(LyricManagerGraphicUserInterface, self).eventFilter(origin, event)
        
        # If the application has ceased running, we always return False to motivate the handling the event by the
        # rest of the Qt pipeline.
        return False
    
    def key_press_event(self, event):
        """ Placeholder for future key event handling. """
        pass


    def _get_selected_lyric_aligner_type(self):
        """ Returns the selected lyric aligner. """

        # Not ideal for performance reasons
        for index in range(self.widget_lyric_aligners.count()):
            item = self.widget_lyric_aligners.item(index)
            widget_radio_button: QRadioButton = self.widget_lyric_aligners.itemWidget(item)

            if widget_radio_button.isChecked():
                text = widget_radio_button.text()
                return LyricAlignerType[text]
        
        # Technically, QRadioButton should prevent the code from ever reaching this point
        return LyricAlignerType.Disabled


    def _set_selected_lyric_aligner_type(self, lyric_aligner_type: LyricAlignerType):
        """ blrup """

        # Not ideal for performance reasons
        for index in range(self.widget_lyric_aligners.count()):
            item = self.widget_lyric_aligners.item(index)
            widget_radio_button: QRadioButton = self.widget_lyric_aligners.itemWidget(item)

            text = widget_radio_button.text()
            aligner_type = LyricAlignerType[text]

            if aligner_type == lyric_aligner_type:
                widget_radio_button.setChecked(True)
        
        # Technically, QRadioButton should prevent the code from ever reaching this point
        return LyricAlignerType.Disabled


    def _get_selected_lyric_fetcher_types(self) -> List[LyricFetcherType]:
        """ Returns a list of all selected lyric fetchers. """
        fetchers = []

        model = self.widget_lyric_sources.model()
        for index in range(model.rowCount()):

            tt = model.index(index)
            item = model.itemData(tt)

            # At the time of writing, it's not exactly clear how to "properly" index into the derived QListWidget's
            # Model. These hard-coded index numbers (0 and 10) are suboptimal.
            item_name = item[0]
            item_checked = (item[10] == QtCore.Qt.Checked.value)

            # Skip any items that aren't checked.
            if not item_checked:
                continue

            fetchers.append(LyricFetcherType[item_name])

        return fetchers
    

    def _set_selected_lyric_fetcher_types(self, fetcher_types: List[LyricFetcherType]):
        """ Checks any lyric fetcher types provided in the list.
        
        TODO: Iterating over the widget items isn't ideal, we should probably be iterating over the underlying model,
        but it wasn't easy finding any code/examples as for how to do this with PySide6.
        """

        for index in range(self.widget_lyric_sources.count()):
            item = self.widget_lyric_sources.item(index)

            text = item.text()
            item_fetcher_type = LyricFetcherType[text]

            state_to_set = QtCore.Qt.Unchecked
            if item_fetcher_type in fetcher_types:
                state_to_set = QtCore.Qt.Checked
            
            item.setCheckState(state_to_set)


def main():
    try:
        QtCore.QCoreApplication.setAttribute(QtCore.Qt.AA_ShareOpenGLContexts)      # Suppresses a Qt Error
        qt_application = QtWidgets.QApplication(sys.argv)
        application = LyricManagerGraphicUserInterface()
        application.show()

        application.execution_mode()

        return_value = qt_application.exec()
        sys.exit(return_value)
    except BaseException as e:
        logging.critical(sys.exc_info())
        logging.exception(f"Uncaught Exception: {e}")
        raise e

    #sys.exit(qt_application.exec())

if __name__ == '__main__':
    main()    