# Python
from enum import Enum

# 3rd Party
from PySide6.QtWidgets import QComboBox
from PySide6.QtCore import QSettings

# 1st Party


class ComboBoxEnum():
    """ Implements QComboBox functionality to represent an Enum-based setting. """

    def __init__(self,
                 widget_combo_box: QComboBox,
                 enum_type: Enum,
                 enum_default_value,
                 settings_name: str,
                 q_settings: QSettings) -> None:
        self.widget_combo_box = widget_combo_box
        self.enum_type = enum_type
        self.settings_name = settings_name
        self.q_settings = q_settings

        for enum_value in enum_type:
            self.widget_combo_box.addItem(enum_value.name)

        # Load settings value
        loaded_enum_value = self.q_settings.value(settings_name, enum_default_value)

        # Set Combo choice
        index = self.widget_combo_box.findText(loaded_enum_value.name)
        self.widget_combo_box.setCurrentIndex(index)


    def save_setting(self):
        """ Saves the currently selected choice as an enum to the QSettings object. """
        text = self.widget_combo_box.currentText()
        current_enum_value = self.enum_type[text]

        self.q_settings.setValue(self.settings_name, current_enum_value)