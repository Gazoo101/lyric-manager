# Python
import os
import sys
import logging
import webbrowser
from enum import Enum
from pathlib import Path
from typing import Optional, List
from functools import partial

# 3rd Party
from PySide6 import QtCore, QtWidgets, QtGui
from PySide6.QtWidgets import QMainWindow, QListWidget, QPlainTextEdit, QListWidgetItem, QAbstractItemView, QSplitter
from PySide6.QtWidgets import QRadioButton, QTableWidget, QTableWidgetItem, QProgressBar, QPushButton, QCheckBox 
from PySide6.QtWidgets import QMessageBox, QMenuBar, QComboBox, QFileDialog, QLineEdit, QWidget, QToolButton, QApplication
from PySide6.QtUiTools import QUiLoader
from PySide6.QtCore import QFile, QDir, qDebug, QSettings
from PySide6.QtGui import QAction, QIcon

# 1st Party
import resources.resources
from src.developer_options import DeveloperOptions

from src.components.audio_artist_and_song_name_source import AudioArtistAndSongNameSource
from src.components.github_repository_version_check import GithubRepositoryVersionCheck

from src.gui import GuiWorker
from src.gui import LoggingHandlerSignal
from src.gui import ProgressItemGeneratorGUI
from src.gui import QListWidgetDragAndDrop
from src.gui import ComboBoxEnum
from src.gui import WidgetQCheckBoxWithEnum
from src.gui import WidgetQRadioButtonWithEnum

from src.gui import bind_property_window_main
from src.gui import bind_property_window_settings

from src.lyric_manager_base import LyricManagerBase
from src.lyric_processing_config import Settings
from src.lyric_processing_config import FileCopyMode
from src.lyric.dataclasses_and_types import LyricFetcherType
from src.lyric.dataclasses_and_types import LyricAlignerType
from src.lyric.dataclasses_and_types import LyricAlignTask


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
        bind_property_window_main("checkBox_recursively_parse_folders_to_process", "checked")
    
    overwrite_existing_generated_files = \
        bind_property_window_settings("checkBox_overwrite_existing_generated_files", "checked")
    
    gui_genius_token = bind_property_window_settings("lineEdit_genius_token", "text")
    gui_google_custom_search_api_key = bind_property_window_settings("lineEdit_google_custom_search_api_key", "text")
    gui_google_custom_search_engine_id = bind_property_window_settings("lineEdit_google_custom_search_engine_id", "text")

    gui_path_to_NUSLyrixAutoAlign = bind_property_window_settings("lineEdit_path_to_NUSAutoLyrixAlign", "text")
    gui_path_to_NUSLyrixAutoAlign_working_directory = bind_property_window_settings("lineEdit_path_to_NUSAutoLyrixAlign_working_directory", "text")

    gui_path_to_aligned_lyrics_copy = bind_property_window_settings("lineEdit_path_to_aligned_lyrics_copy", "text")

    
    def _load_and_set_checkbox_from_q_settings_or_default(self, q_settings_name: str, widget_q_checkbox_name):
        """ Load and set state of a named checkbox in either the main or settings window from QSettings. """
        widget_q_checkbox: QCheckBox
        widget_q_checkbox = self.widget_window_main.findChild(QCheckBox, widget_q_checkbox_name)
        if not widget_q_checkbox:
            widget_q_checkbox = self.widget_window_settings.findChild(QCheckBox, widget_q_checkbox_name)

        # Using .checkState() here allows LyricManager to utilize the default state defined via QtDesigner
        check_state = self.q_settings.value(q_settings_name, widget_q_checkbox.checkState())
        widget_q_checkbox.setCheckState(check_state)


    def _save_checkbox_to_q_settings(self, q_settings_name: str, widget_q_checkbox_name):
        """ Saves the state of a named checkbox in either the main or settings window to QSettings. """
        widget_q_checkbox: QCheckBox
        widget_q_checkbox = self.widget_window_main.findChild(QCheckBox, widget_q_checkbox_name)
        if not widget_q_checkbox:
            widget_q_checkbox = self.widget_window_settings.findChild(QCheckBox, widget_q_checkbox_name)
        
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

        #self._setup_ui("./resources/lyric_manager_v4.ui")
        self._setup_ui_v2("./resources/lyric_manager_window_main.ui", "./resources/lyric_manager_window_settings.ui")
        self._load_ui_settings()
        
        self.widget_window_main.setWindowTitle(f"LyricManager v. {DeveloperOptions.version}")

        # Causes Qt to trigger this classes eventFilter() to handle incoming events. It's primarily used to respond
        # to key presses, such as Esc to quit.
        self.widget_window_main.installEventFilter(self)
        self.widget_window_settings.installEventFilter(self)

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

        if DeveloperOptions.automatically_start_processing():
            self.start_processing()


    def _create_combo_box_enum(self, widget_name: str, enum_value: Enum, settings_name: str) -> ComboBoxEnum:
        """ Creates a ComboBoxEnum which is a wrapper class tying a QComboBox to a custom Enum. """
        q_widget: QComboBox = self.widget_window_main.findChild(QComboBox, widget_name)
        if q_widget:
            return ComboBoxEnum(q_widget, type(enum_value), enum_value, settings_name, self.q_settings)
        
        return None


    def _setup_ui_v2(self, path_to_ui_window_main: str, path_to_ui_window_settings: str):
        """ Loads a Qt .ui interface via the path provided, and sets up static/dynamic widget behavior.
        
        The order of work is grouped into 3 categories:
            1. Static Gui Elements
            2. Dynamic Gui Elements
            3. Slots/Signals

        Args:
            path_to_ui_file: Path to the .ui file to be loaded.
        """
        self.widget_window_main : QMainWindow = QUiLoader().load(path_to_ui_window_main)
        self.widget_window_settings : QWidget = QUiLoader().load(path_to_ui_window_settings)

        # We instantiate this Settings object purely to access the default values it contains.
        settings = Settings()

        ###
        # Static GUI - Main Window
        placeholder_lyric_fetcher: QCheckBox = self.widget_window_main.findChild(QCheckBox, "checkBox_lyric_fetcher_placeholder")
        placeholder_lyric_aligner: QRadioButton = self.widget_window_main.findChild(QRadioButton, "radioButton_lyric_aligner_placeholder")

        self.lyric_fetchers = WidgetQCheckBoxWithEnum(placeholder_lyric_fetcher, LyricFetcherType, [LyricFetcherType.LocalFile], "Processing/FetcherTypes", self.q_settings )
        self.lyric_aligners = WidgetQRadioButtonWithEnum(placeholder_lyric_aligner, LyricAlignerType.NUSAutoLyrixAlignOffline, "Processing/AlignerType", self.q_settings )

        self.widget_splitter_horizontal: QSplitter = self.widget_window_main.findChild(QSplitter, "splitter_horizontal")
        self.widget_splitter_vertical: QSplitter = self.widget_window_main.findChild(QSplitter, "splitter_vertical")

        widget_button_settings: QToolButton = self.widget_window_main.findChild(QToolButton, "toolButton_settings")
        widget_button_start_processing: QPushButton = self.widget_window_main.findChild(QPushButton, "pushButton_start_processing")

        self.widget_progress_bar_overall: QProgressBar = self.widget_window_main.findChild(QProgressBar, "progressBar_overall")
        self.widget_progress_bar_overall.setValue(0)
        self.widget_progress_bar_overall.setFormat("- Ready -")

        self.widget_songs_processed: QTableWidget = self.widget_window_main.findChild(QTableWidget, "tableWidget_songs_processed")
        self.widget_log: QPlainTextEdit = self.widget_window_main.findChild(QPlainTextEdit, "plainTextEdit_log")

        self.widget_button_clear_output: QPushButton = self.widget_window_main.findChild(QPushButton, "pushButton_clear_output")

        ###
        # Static GUI - Settings Window
        placeholder_artist_song_title_source: QRadioButton = self.widget_window_settings.findChild(QRadioButton, "radioButton_artist_song_title_source_placeholder")
        placeholder_aligned_lyrics_formatting: QRadioButton = self.widget_window_settings.findChild(QRadioButton, "radioButton_aligned_lyrics_formatting_placeholder")
        placeholder_aligned_lyrics_copy_mode: QRadioButton = self.widget_window_settings.findChild(QRadioButton, "radioButton_aligned_lyrics_copy_mode_placeholder")

        widget_button_set_path_NUSAutoLyrixAlign: QToolButton = \
            self.widget_window_settings.findChild(QToolButton, "toolButton_set_path_to_NUSAutoLyrixAlign")
        widget_button_set_path_NUSAutoLyrixAlign_working_directory: QToolButton = \
            self.widget_window_settings.findChild(QToolButton, "toolButton_set_path_to_NUSAutoLyrixAlign_working_directory")
        widget_button_set_path_to_aligned_lyrics_copy: QToolButton = \
            self.widget_window_settings.findChild(QToolButton, "toolButton_set_path_to_aligned_lyrics_copy")

        ################################################################################################################

        ###
        # Dynamic GUI - Main Window
        self.widget_local_data_sources = self._setup_widget_local_data_sources()


        ###
        # Dynamic GUI - Settings Window
        self.widget_artist_song_title_source = WidgetQRadioButtonWithEnum(placeholder_artist_song_title_source, settings.data.input.artist_song_name_source, "Processing/artist_song_name_source", self.q_settings )
        self.widget_aligned_lyrics_formatting = WidgetQRadioButtonWithEnum(placeholder_aligned_lyrics_formatting, settings.data.output.aligned_lyrics_formatting, "Processing/aligned_lyrics_output_mode", self.q_settings )
        self.widget_file_copy_mode = WidgetQRadioButtonWithEnum(placeholder_aligned_lyrics_copy_mode, settings.data.output.aligned_lyrics_file_copy_mode, "Processing/file_copy_mode", self.q_settings )


        ################################################################################################################

        ###
        # Slots and Signals - Main Window
        menu_bar: QMenuBar = self.widget_window_main.menuBar()
        menu_bar.triggered.connect(self.sl_menu_bar_trigger)

        widget_button_start_processing.clicked.connect(self.start_processing)

        def show_settings_window():
            """ Shows the setting window if hidden, raises it to the front if already open. """
            if self.widget_window_settings.isHidden():
                self.widget_window_settings.show()
            else:
                self.widget_window_settings.activateWindow()


        widget_button_settings.clicked.connect(show_settings_window)

        # Set 'Delete' key to remove executable entries if the widget is active
        QtGui.QShortcut(QtGui.QKeySequence("Delete"), self.widget_local_data_sources, self.widget_local_data_sources.remove_selected_items, context=QtCore.Qt.WidgetShortcut)

        def clear_outputs():
            self._clear_processed_songs_table()
            self.widget_log.clear()

        self.widget_button_clear_output.clicked.connect(clear_outputs)
        


        ###
        # Slots and Signals - Settings Window
        def open_directory_select_dialog_and_set_to_line_edit(qlineedit_widget_name: str):
            """ Spawns a QFileDialog set to select a directory and applies the path to the QLineEdit with the given name. """
            qline_edit_widget: QLineEdit = self.widget_window_settings.findChild(QLineEdit, qlineedit_widget_name)
            
            dialog_path = QFileDialog.getExistingDirectory(
                self.widget_window_settings, "Open Directory",
                str(self.path_to_application),
                QFileDialog.Option.ShowDirsOnly | QFileDialog.Option.DontResolveSymlinks
            )
            qline_edit_widget.setText(dialog_path)

        function_set_path_to_NUSAutoLyrixAlign = partial(open_directory_select_dialog_and_set_to_line_edit, "lineEdit_path_to_NUSAutoLyrixAlign")
        widget_button_set_path_NUSAutoLyrixAlign.clicked.connect(function_set_path_to_NUSAutoLyrixAlign)

        function_set_path_to_NUSAutoLyrixAlign_working_directory = partial(open_directory_select_dialog_and_set_to_line_edit, "lineEdit_path_to_NUSAutoLyrixAlign_working_directory")
        widget_button_set_path_NUSAutoLyrixAlign_working_directory.clicked.connect(function_set_path_to_NUSAutoLyrixAlign_working_directory)

        function_set_path_to_aligned_lyrics_copy = partial(open_directory_select_dialog_and_set_to_line_edit, "lineEdit_path_to_aligned_lyrics_copy")
        widget_button_set_path_to_aligned_lyrics_copy.clicked.connect(function_set_path_to_aligned_lyrics_copy)


        def toggle_path_to_aligned_lyrics_copy_widgets():
            lineEdit_path_to_aligned_lyrics_copy: QLineEdit = self.widget_window_settings.findChild(QLineEdit, "lineEdit_path_to_aligned_lyrics_copy")
            copy_mode = self.widget_file_copy_mode.get_selected()
            if copy_mode == FileCopyMode.SeparateDirectory:
                lineEdit_path_to_aligned_lyrics_copy.setDisabled(False)
                widget_button_set_path_to_aligned_lyrics_copy.setDisabled(False)
            else:
                lineEdit_path_to_aligned_lyrics_copy.setDisabled(True)
                widget_button_set_path_to_aligned_lyrics_copy.setDisabled(True)



        self.widget_file_copy_mode.anyClicked.connect(toggle_path_to_aligned_lyrics_copy_widgets)
        toggle_path_to_aligned_lyrics_copy_widgets()

        #Update signal here...

        # self.widget_file_copy_mode.widget_combo_box.currentIndexChanged.connect(toggle_path_to_aligned_lyrics_copy_widgets)
        # toggle_path_to_aligned_lyrics_copy_widgets(0)


        # Iterate through all a menu's actions
        # for action in menu_bar.actions():
        #     do_something = 0
        



    # def _setup_ui(self, path_to_ui_file : str):
    #     """ Loads a Qt .ui interface via the path provided, and sets up static/dynamic widget behavior.
        
    #     The order of work is grouped into 3 categories:
    #         1. Static Gui Elements
    #         2. Dynamic Gui Elements
    #         3. Slots/Signals

    #     Args:
    #         path_to_ui_file: Path to the .ui file to be loaded.
    #     """
    #     ### Static GUI Behavior
    #     #qDebug("helpsors")

    #     self.widget_window_main : QMainWindow = QUiLoader().load(path_to_ui_file)

    #     # Set icon
    #     # https://stackoverflow.com/questions/17034330/how-to-include-resource-file-in-cx-freeze-binary
    #     icon = QIcon("./resources/lyric_manager.ico")
    #     self.widget_window_main.setWindowIcon(icon)

    #     self.widget_songs_processed: QTableWidget = self.widget_window_main.findChild(QTableWidget, "tableWidget_songs_processed")

    #     self.widget_log: QPlainTextEdit = self.widget_window_main.findChild(QPlainTextEdit, "plainTextEdit_log")

    #     self.widget_lyric_sources: QListWidget = self.widget_window_main.findChild(QListWidget, "listWidget_lyricSources")
    #     self.widget_lyric_aligners: QListWidget = self.widget_window_main.findChild(QListWidget, "listWidget_lyricAligners")

    #     self.widget_lyric_aligners.setSelectionBehavior( QAbstractItemView.SelectItems )
    #     self.widget_lyric_aligners.setSelectionMode( QAbstractItemView.SingleSelection )

    #     for key, fetcher in self.factory_lyric_fetcher.builders.items():
    #         self._add_fetcher(key.name)

    #     for key, aligner in self.factory_lyric_aligner.builders.items():
    #         self._add_aligner(key.name)

    #     self.widget_splitter_horizontal: QSplitter = self.widget_window_main.findChild(QSplitter, "splitter_horizontal")
    #     self.widget_splitter_vertical: QSplitter = self.widget_window_main.findChild(QSplitter, "splitter_vertical")

    #     # Oddly, QSplitter's are basically invisible in their default state. We modify it's CSS a tad to make them
    #     # visible.
    #     self.widget_window_main.setStyleSheet("QSplitter::handle { border: 1px outset darkgrey; } ")

    #     self.widget_progress_bar_overall: QProgressBar = self.widget_window_main.findChild(QProgressBar, "progressBar_overall")
    #     self.widget_progress_bar_overall.setValue(0)
    #     self.widget_progress_bar_overall.setFormat("- Ready -")

    #     widget_start_processing = self.widget_window_main.findChild(QPushButton, "pushButton_start_processing")

    #     widget_button_set_path_NUSAutoLyrixAlign: QPushButton = \
    #         self.widget_window_main.findChild(QPushButton, "pushButton_set_path_to_NUSAutoLyrixAlign")
    #     widget_button_set_path_NUSAutoLyrixAlign_working_directory: QPushButton = \
    #         self.widget_window_main.findChild(QPushButton, "pushButton_set_path_to_NUSAutoLyrixAlign_working_directory")
    #     widget_button_set_path_to_aligned_lyrics_copy: QPushButton = \
    #         self.widget_window_main.findChild(QPushButton, "pushButton_set_path_to_aligned_lyrics_copy")

    #     # We obtain the default values for our enum-based ComboBoxes form a default Settings object
    #     settings = Settings()

    #     self.widget_artist_song_name_source = \
    #         self._create_combo_box_enum("comboBox_artist_song_name_source", settings.data.input.artist_song_name_source, "Processing/artist_song_name_source")
    #     self.widget_file_copy_mode = \
    #         self._create_combo_box_enum("comboBox_file_copy_mode", settings.data.output.aligned_lyrics_file_copy_mode, "Processing/file_copy_mode")
    #     self.widget_aligned_lyrics_output_mode = \
    #         self._create_combo_box_enum("comboBox_aligned_lyrics_output_mode", settings.data.output.aligned_lyrics_formatting, "Processing/aligned_lyrics_output_mode")



    #     #################################################
    #     ### Dynamic GUI Behavior
    #     # - Replacing widgets defined via QtDesigner
    #     # - Connecting Signals / Slots
    #     self.widget_local_data_sources = self._setup_widget_local_data_sources()

    #     # Set 'Delete' key to remove executable entries if the widget is active
    #     QtGui.QShortcut(QtGui.QKeySequence("Delete"), self.widget_local_data_sources, self.widget_local_data_sources.remove_selected_items, context=QtCore.Qt.WidgetShortcut)

    #     def open_directory_select_dialog_and_set_to_line_edit(qlineedit_widget_name: str):
    #         """ Spawns a QFileDialog set to select a directory and applies the path to the QLineEdit with the given name. """
    #         qline_edit_widget: QLineEdit = self.widget_window_main.findChild(QLineEdit, qlineedit_widget_name)
            
    #         dialog_path = QFileDialog.getExistingDirectory(
    #             self.widget_window_main, "Open Directory",
    #             str(self.path_to_application),
    #             QFileDialog.Option.ShowDirsOnly | QFileDialog.Option.DontResolveSymlinks
    #         )
    #         qline_edit_widget.setText(dialog_path)

        
    #     def toggle_path_to_aligned_lyrics_copy_widgets(value):
    #         lineEdit_path_to_aligned_lyrics_copy: QLineEdit = self.widget_window_main.findChild(QLineEdit, "lineEdit_path_to_aligned_lyrics_copy")
    #         copy_mode = self.widget_file_copy_mode.get_value_as_enum()
    #         if copy_mode == FileCopyMode.SeparateDirectory:
    #             lineEdit_path_to_aligned_lyrics_copy.setDisabled(False)
    #             widget_button_set_path_to_aligned_lyrics_copy.setDisabled(False)
    #         else:
    #             lineEdit_path_to_aligned_lyrics_copy.setDisabled(True)
    #             widget_button_set_path_to_aligned_lyrics_copy.setDisabled(True)


    #     self.widget_file_copy_mode.widget_combo_box.currentIndexChanged.connect(toggle_path_to_aligned_lyrics_copy_widgets)
    #     toggle_path_to_aligned_lyrics_copy_widgets(0)


    #     ### Slots and signals
    #     widget_start_processing.clicked.connect(self.start_processing)

    #     menu_bar: QMenuBar = self.widget_window_main.menuBar()
    #     menu_bar.triggered.connect(self.sl_menu_bar_trigger)

    #     function_set_path_to_NUSAutoLyrixAlign = partial(open_directory_select_dialog_and_set_to_line_edit, "lineEdit_path_to_NUSAutoLyrixAlign")
    #     widget_button_set_path_NUSAutoLyrixAlign.clicked.connect(function_set_path_to_NUSAutoLyrixAlign)

    #     function_set_path_to_NUSAutoLyrixAlign_working_directory = partial(open_directory_select_dialog_and_set_to_line_edit, "lineEdit_path_to_NUSAutoLyrixAlign_working_directory")
    #     widget_button_set_path_NUSAutoLyrixAlign_working_directory.clicked.connect(function_set_path_to_NUSAutoLyrixAlign_working_directory)

    #     function_set_path_to_aligned_lyrics_copy = partial(open_directory_select_dialog_and_set_to_line_edit, "lineEdit_path_to_aligned_lyrics_copy")
    #     widget_button_set_path_to_aligned_lyrics_copy.clicked.connect(function_set_path_to_aligned_lyrics_copy)


    #     # Iterate through all a menu's actions
    #     # for action in menu_bar.actions():
    #     #     do_something = 0


    def _load_ui_settings(self):
        """ Restores all GUI related settings, e.g. window position, checked settings, selected elements, etc. """
        q_rect_geometry = self.q_settings.value("windowGeometry", self.widget_window_main.geometry())
        self.widget_window_main.setGeometry(q_rect_geometry)

        # Splitters do not yield a 'reasonable' default value at this point in the code (returning [0,0]). Rather than
        # separating out this settings-loading, we opt to manually check if the splitter's values have been previously
        # saved. More boiler-plate code unfortunately, but preferrable to splitting up the load save behavior.
        # I assume it has something to do with Qt having yet to spawn the main window.
        splitter_horizontal_geometry = self.q_settings.value("SplitterHorizontalGeometry", None)
        if splitter_horizontal_geometry is not None:
            # Attempts to type-hint 
            splitter_horizontal_geometry = [int(i) for i in splitter_horizontal_geometry]
            self.widget_splitter_horizontal.setSizes(splitter_horizontal_geometry)

        splitter_vertical_geometry = self.q_settings.value("SplitterVerticalGeometry", None)
        if splitter_vertical_geometry is not None:
            splitter_vertical_geometry = [int(i) for i in splitter_vertical_geometry]
            self.widget_splitter_vertical.setSizes(splitter_vertical_geometry)

        # Tokens / Api Keys
        self.gui_genius_token = self.q_settings.value("TokensApiKeys/GeniusToken", None)
        self.gui_google_custom_search_api_key = self.q_settings.value("TokensApiKeys/GoogleCustomSearchApiKey", None)
        self.gui_google_custom_search_engine_id = self.q_settings.value("TokensApiKeys/GoogleCustomSearchEngineId", None)

        fetcher_types = self.q_settings.value("Processing/FetcherTypes", [LyricFetcherType.LocalFile])
        aligner_type = self.q_settings.value("Processing/AlignerType", LyricAlignerType.Disabled)

        # While QSettings can manage creating an empty list as a default value, if it cannot find a QSettings entry, it
        # stubbornly refuses to save an empty list as anything but '@Invalid()'. Passing "QVariantList" as type hint
        # appears to crash Qt.
        folders_to_process = self.q_settings.value("Processing/FoldersToProcess", None)
        if folders_to_process is not None:
            self.widget_local_data_sources.add_paths(folders_to_process)

        self.gui_path_to_NUSLyrixAutoAlign = self.q_settings.value("Alignment/PathToNUSLyrixAutoAlign", None)
        self.gui_path_to_NUSLyrixAutoAlign_working_directory = self.q_settings.value("Alignment/PathToNUSLyrixAutoAlignWorkingDirectory", None)

        self._load_and_set_checkbox_from_q_settings_or_default("Processing/RecursivelyParseFolders", "checkBox_recursively_parse_folders_to_process")
        self._load_and_set_checkbox_from_q_settings_or_default("Processing/OverwriteExisting", "checkBox_overwrite_existing_generated_files")

        self.lyric_fetchers.set_value(fetcher_types)
        self.lyric_aligners.set_value(aligner_type)

        self.gui_path_to_aligned_lyrics_copy = self.q_settings.value("Processing/PathToAlignedLyricsCopy", None)


    def _save_ui_settings(self):
        """ Updates self.q_settings with all GUI related settings so they'll be properly saved when the program exits. """
        # Although .saveGeometry() and .restoreGeometry() appear to be the preferred approach to saving and
        # restoring window position and size, it appears have issues working across multiple screens.
        # Unfortunately the two functions automatically convert the QRect object to/from byte-code, so the
        # problem isn't easily further diagnosed. Hence, we instead load/save the raw Geometry Rect object.
        self.q_settings.setValue("WindowGeometry", self.widget_window_main.geometry())
        self.q_settings.setValue("SplitterHorizontalGeometry", self.widget_splitter_horizontal.sizes())
        self.q_settings.setValue("SplitterVerticalGeometry", self.widget_splitter_vertical.sizes())

        self.q_settings.setValue("WorkingDirectory", "./WorkingDirectory")

        # Tokens / Api Keys
        self.q_settings.setValue("TokensApiKeys/GeniusToken", self.gui_genius_token)
        self.q_settings.setValue("TokensApiKeys/GoogleCustomSearchApiKey", self.gui_google_custom_search_api_key)
        self.q_settings.setValue("TokensApiKeys/GoogleCustomSearchEngineId", self.gui_google_custom_search_engine_id)

        # Save processing-related settings...
        selected_fetcher_types = self.lyric_fetchers.get_selected()
        selected_aligner_type = self.lyric_aligners.get_selected()
        paths_to_process = self.widget_local_data_sources.get_paths()

        self.q_settings.setValue("Processing/FetcherTypes", selected_fetcher_types)
        self.q_settings.setValue("Processing/AlignerType", selected_aligner_type)

        # Note, if paths_to_process is an empty list, Qt saves "@Invalid()" to disk
        self.q_settings.setValue("Processing/FoldersToProcess", paths_to_process)

        self.q_settings.setValue("Alignment/PathToNUSLyrixAutoAlign", self.gui_path_to_NUSLyrixAutoAlign)
        self.q_settings.setValue("Alignment/PathToNUSLyrixAutoAlignWorkingDirectory", self.gui_path_to_NUSLyrixAutoAlign_working_directory)

        self._save_checkbox_to_q_settings("Processing/RecursivelyParseFolders", "checkBox_recursively_parse_folders_to_process")
        self._save_checkbox_to_q_settings("Processing/OverwriteExisting", "checkBox_overwrite_existing_generated_files")

        self.q_settings.setValue("Processing/PathToAlignedLyricsCopy", self.gui_path_to_aligned_lyrics_copy)

        self.widget_artist_song_title_source.save_setting()
        self.widget_file_copy_mode.save_setting()
        self.widget_aligned_lyrics_formatting.save_setting()


    def start_processing(self):
        """ Starts LyricManager's lyric fetching and alignment.
        
        To maintain similar behaviour between the Command-Line- and Graphical-User-Interface versions, we transfer
        relevant settings to a Settings-object and pass it to the underlying pipeline code in LyricManagerBase.
        """
        selected_fetcher_types = self.lyric_fetchers.get_selected()
        selected_aligner_type = self.lyric_aligners.get_selected()
        paths_to_process = self.widget_local_data_sources.get_checked_paths()
        
        settings = Settings()
        settings.lyric_fetching.sources = selected_fetcher_types
        settings.lyric_fetching.genius_token = self.gui_genius_token
        settings.lyric_fetching.google_custom_search_api_key = self.gui_google_custom_search_api_key
        settings.lyric_fetching.google_custom_search_engine_id = self.gui_google_custom_search_engine_id

        settings.lyric_alignment.method = selected_aligner_type
        settings.lyric_alignment.NUSAutoLyrixAlign_path = Path(self.gui_path_to_NUSLyrixAutoAlign)
        settings.lyric_alignment.NUSAutoLyrixAlign_working_directory = Path(self.gui_path_to_NUSLyrixAutoAlign_working_directory)

        settings.data.input.paths_to_process = paths_to_process
        settings.data.input.recursively_process_paths = self.recursively_parse_folders_to_process
        settings.data.input.folders_to_exclude = []
        settings.data.input.artist_song_name_source = self.widget_artist_song_title_source.get_selected()

        settings.data.output.overwrite_existing_generated_files = self.overwrite_existing_generated_files
        settings.data.output.path_to_working_directory = self.path_to_working_directory
        settings.data.output.path_to_reports = self.path_to_reports
        settings.data.output.aligned_lyrics_file_copy_mode = self.widget_file_copy_mode.get_selected()
        settings.data.output.aligned_lyrics_formatting = self.widget_aligned_lyrics_formatting.get_selected()

        settings.data.output.path_to_output_aligned_lyrics = Path(self.gui_path_to_aligned_lyrics_copy)

        # TODO: Re-visit if passing in this worker in the single-threaded context is the best single threaded approach.
        worker = GuiWorker(None)
        loop_wrapper = ProgressItemGeneratorGUI(worker.signals.progress, worker.signals.task_description)

        if DeveloperOptions.is_multithreading_enabled():
            # Multi-threaded
            worker.set_fn(self.fetch_and_align_lyrics, settings, loop_wrapper)

            # When execution finishes, have the worker pass on the results to this thread to update the process table
            worker.signals.finished.connect(self._update_processed_table)
            
            self._connect_worker_to_gui_progress_bar_widget(worker)

            # thread_pool.start() also accepts PyCallable, but this wouldn't provide built-in signals or added parameters
            # leading to further hidden state.
            self.thread_pool.start(worker)
        else:
            # Single-threaded
            lyric_alignment_tasks = self.fetch_and_align_lyrics(settings, loop_wrapper)
            self._update_processed_table(lyric_alignment_tasks)


    def _connect_worker_to_gui_progress_bar_widget(self, worker: GuiWorker):
        """ Connects the Worker class' signals to the Guis progress bar update function.

        For reasons that are currently unclear, directly passing the Qt progress bar widgets functions into the the
        Worker class' QtCore.Signal's connect() function leads to the progress bar never receiving any updates. However,
        using an inbetween functor, such as a member function or lambda resolves this problem. No idea why...
        """
        func_update_progress_bar_value = lambda value : self.widget_progress_bar_overall.setValue(value)
        func_update_progress_bar_text = lambda text : self.widget_progress_bar_overall.setFormat(f"{text}... %p%")

        #worker.signals.progress.connect(self.widget_progress_bar.setValue) # Doesn't work for some reason...?
        worker.signals.progress.connect(func_update_progress_bar_value)
        worker.signals.task_description.connect(func_update_progress_bar_text)
        

    def _add_fetcher(self, text: str):
        """ Adds a check-box enabled lyric fetcher to the QListWidget containing lyric fetchers. """
        item = QListWidgetItem(text)
    
        item.setFlags(QtCore.Qt.ItemIsUserCheckable | QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable )
        item.setCheckState(QtCore.Qt.Checked)

        self.widget_lyric_sources.addItem(item)


    def _add_aligner(self, text: str):
        """ Adds a radio-button enabled lyric aligner to the QListWidget containing lyric aligners. """

        item = QListWidgetItem(self.widget_lyric_aligners)  # Without this 'parent instantiation' we get nothing in Qt O_o

        radio_button = QRadioButton(text)
    
        self.widget_lyric_aligners.setItemWidget(item, radio_button)

        # TODO: Figure out how to actually get the pointer to this radio button once the list construction is complete
        radio_button.setChecked( True )


    def _clear_processed_songs_table(self):
        # Clear rows without clearing the column names
        # Source: https://forum.qt.io/topic/85189/how-not-to-delete-column-names-in-qtablewidget
        self.widget_songs_processed.model().removeRows(0, self.widget_songs_processed.rowCount())


    def _update_processed_table(self, lyric_align_tasks: list[LyricAlignTask]):
        """ Updates the processed table GUI widget communicating the % of matched lyrics and overall result of the given tasks. """

        self._clear_processed_songs_table()

        self.widget_songs_processed.setRowCount(len(lyric_align_tasks))

        index_filename = 0
        index_progress = 1
        index_note = 2

        for index, task in enumerate(lyric_align_tasks):
            item_filename = QTableWidgetItem(task.filename)

            # How to embed a progress bar
            # https://stackoverflow.com/questions/54285057/how-to-include-a-column-of-progress-bars-within-a-qtableview
            progress_bar = QProgressBar()
            progress_bar.setValue(task.match_result.match_percentage)
            progress_bar.setAlignment(QtCore.Qt.AlignmentFlag.AlignHCenter) # Place progress bar text inside of itself.

            progress_bar_animation_disabled = """
                QProgressBar { border: 1px solid grey; border-radius: 0px; text-align: center; }
                QProgressBar::chunk {background-color: #3add36; width: 1px;}
            """
            progress_bar.setStyleSheet(progress_bar_animation_disabled)

            item_note = QTableWidgetItem(task.get_user_friendly_result())

            self.widget_songs_processed.setItem(index, index_filename, item_filename)
            self.widget_songs_processed.setCellWidget(index, index_progress, progress_bar)
            self.widget_songs_processed.setItem(index, index_note, item_note)




    def show(self):
        """ A pass-through function for QMainWindow.show(). """
        self.widget_window_main.show()

    
    def _setup_widget_local_data_sources(self):
        """ Replaces a specfic QListWidget, with a QListWidgetDragAndDrop, set via QtDesigner in a .ui file.

        This allows us to still rely on QtDesigner to define the position and layout of the QListWidgetDragAndDrop.
        """
        # QListWidget to replace
        widget_list_folders_placeholder: QListWidget = self.widget_window_main.findChild(QListWidget, "listWidget_localDataSources")

        widget_list_local_data_sources = QListWidgetDragAndDrop(accepted_audio_filename_extensions=self.recognized_audio_filename_extensions)
        widget_list_local_data_sources.placeholder_text = "Drag and drop audio files and folders here..."

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
        if origin is self.widget_window_settings:
            if event.type() == QtCore.QEvent.KeyPress:
                if event.key() == QtCore.Qt.Key_Escape:
                    self.widget_window_settings.close()

        if origin is self.widget_window_main:
            if event.type() == QtCore.QEvent.KeyPress:

                # Special case for .close() - If we're closing the application, we should avoid calling super() as the
                # application itself will soon cease to exist.
                if event.key() == QtCore.Qt.Key_Escape:
                    # Expected to pretty much immediately trigger the QtCore.QEvent.Close case below.
                    #self.widget_window_main.close()
                    QApplication.closeAllWindows()

                self.key_press_event(event)
            elif event.type() == QtCore.QEvent.Close:
                
                self._save_ui_settings()

                self.is_running = False

        if self.is_running:
            return super(LyricManagerGraphicUserInterface, self).eventFilter(origin, event)
        
        # If the application has ceased running, we always return False to motivate the handling the event by the
        # rest of the Qt pipeline.
        return False
    
    def key_press_event(self, event):
        """ Placeholder for future key event handling. """
        pass


    def sl_menu_bar_trigger(self, q_action: QAction):
        """ Triggered when a menu selection is made in LyricManager.

        It would preferrable to to directly connect a function to a menu signal. Unfortunately, at the time of writing
        the only approach to get to a menu option's signal is to iterate through all the menu widget's .actions().
        This apparently needs to be executed recursively, i.e. actions within actions for all menu options.

        This 'all actions' trigger is a simpler approach, for now.
        """

        # We intentionally match on a menu options 'objectName' as opposed to it's 'text' (label), as a label may
        # be repeated across the entire menu.
        #tt = q_action.text()
        action_object_name = q_action.objectName()

        if action_object_name == "actionAbout_Qt":
            QApplication.aboutQt()
        elif action_object_name == "actionAbout_LyricManager":
            QMessageBox.about(
                self.widget_window_main,
                f"About LyricManager v {DeveloperOptions.version}",
                (
                    "Developed by Lasse Farnung Laursen.\n"
                    "https://github.com/Gazoo101/lyric-manager\n"
                    "\n"
                    "Awesome Testers:\n"
                    "Robert Santoro\n"
                    "Ryan-Kaye Simmons\n"
                    "Rolf 'shargo' Karlsson"
                )
            )


    def show_dialog_message_box_if_new_version_has_been_released(self):
        """ Presents the user with a dialogue box if there's a new release of LyricManager that the user has yet to be informed of.

        To keep user-pestering to a bare minimum, we keep track of which latest version of LyricManager we're aware of.
        Only if the user has yet to be informed of a new release do we provide them with a dialogue about this.
        
        """
        latest_known_release = self.q_settings.value("LatestKnownRelease", DeveloperOptions.version)
        newer_release = GithubRepositoryVersionCheck.get_newer_version_if_available(latest_known_release)

        # If the latest release is already 'known', even if potentially newer, we don't inform the user
        if newer_release is None:
            return

        message_box = QMessageBox()
        message_box.setIcon(QMessageBox.Icon.Information)
        message_box.setWindowTitle('New version available!')

        # Setting the width of a QMessageBox is an uphill struggle. Apparently a spacer can do the trick, but we manage
        # with setting the CSS in the QMessageBox
        #width = "130"
        #message_box.setStyleSheet("QLabel{width: "+width+"px; min-width: "+width+"px; max-width: "+width+"px;}")

        message_box.setText((
            "Detected newer release of LyricManager!\n"
            "\n"
            f"Your version: {DeveloperOptions.version}\n"
            f"New version: {newer_release}"
            "\n"
            "Would you like to visit Github to download this new release?"
        ))
        message_box.setStandardButtons(QMessageBox.StandardButton.Yes|QMessageBox.StandardButton.No|QMessageBox.StandardButton.Ignore)
        message_box.setDefaultButton(QMessageBox.StandardButton.Yes)

        button_yes = message_box.button(QMessageBox.StandardButton.Yes)
        button_yes.setText('Yes')

        button_ignore = message_box.button(QMessageBox.StandardButton.Ignore)
        button_ignore.setText("No, and don't remind me about this release again.")

        button_no = message_box.button(QMessageBox.StandardButton.No)
        button_no.setText('Maybe later')
        message_box.exec()

        if message_box.clickedButton() == button_yes:
            webbrowser.open("https://github.com/Gazoo101/lyric-manager/releases")
            self.q_settings.setValue("LatestKnownRelease", newer_release)
        elif message_box.clickedButton() == button_no:
            pass # 'No', which is 'Maybe' just closes the Dialog.
        elif message_box.clickedButton() == button_ignore:
            self.q_settings.setValue("LatestKnownRelease", newer_release)



def main():
    try:
        QtCore.QCoreApplication.setAttribute(QtCore.Qt.AA_ShareOpenGLContexts)      # Suppresses a Qt Error
        qt_application = QtWidgets.QApplication(sys.argv)
        application = LyricManagerGraphicUserInterface()
        application.show()

        application.execution_mode()

        application.show_dialog_message_box_if_new_version_has_been_released()

        return_value = qt_application.exec()
        
    except BaseException as e:
        logging.critical(sys.exc_info())
        logging.exception(f"Uncaught Exception: {e}")
        raise e
    
    sys.exit(return_value)

if __name__ == '__main__':
    main()