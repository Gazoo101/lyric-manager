# Python
from enum import Enum
from typing import List

# 3rd Party
from PySide6.QtWidgets import QCheckBox, QLayout
from PySide6.QtCore import QSettings

# 1st Party


class WidgetQCheckBoxWithEnum():
    """ Manages tying a given Enum to a series of checkboxes within a group layout. """

    def __init__(self,
                 widget_qcheckbox_placeholder: QCheckBox,
                 enum_type: Enum,
                 enum_default_value: List[Enum],
                 settings_name: str,
                 q_settings: QSettings) -> None:
        """
        Args:
            widget_qcheckbox_placeholder: The placeholder checkbox widget this class will replace with other checkbox
                widgets defined by the provided Enum in enum_type.
            enum_type: The enum type around which this class generates widgets to populate into the GUI.
            enum_default_value: A list containing enums of type enum_type.
            settings_name: The QSettings name to which the selected checkboxes should be tied.
            q_settings: The QSettings object to/from which settings are saved/loaded.
        """
        self.enum_type = enum_type
        self.settings_name = settings_name
        self.q_settings = q_settings

        self.layout: QLayout = widget_qcheckbox_placeholder.parent().layout()

        # Populate GUI layout with all of the values belonging to the provided Enum type.
        for enum_value in enum_type:
            widget_checkbox_to_add = QCheckBox(enum_value.name)
            self.layout.addWidget(widget_checkbox_to_add)

        # This unfortunately isn't deleted 'quickly enough' so we have to consider the placeholder
        widget_qcheckbox_placeholder.deleteLater()

        settings_file_value = self.q_settings.value(settings_name, enum_default_value)
        self.set_value(settings_file_value)


    def get_selected(self) -> List[Enum]:
        """ Returns a list of Enum values selected via the GUI check-boxes. """
        selected_values = []

        # Iterating over widgets like this is not optimal from a performance perspective.
        for index in range(self.layout.count()):
            layout_item = self.layout.itemAt(index)
            the_widget: QCheckBox = layout_item.widget()

            if the_widget.isChecked():
                text = the_widget.text()
                selected_values.append( self.enum_type[text] )
            
        return selected_values


    def save_setting(self) -> Enum:
        """ Saves the currently selected choice as an enum to the QSettings object. """
        self.q_settings.setValue(self.settings_name, self.get_value_as_enum())


    def get_value_as_enum(self):
        """ Returns the currently selected option in the form of an Enum. """
        text = self.widget_combo_box.currentText()
        current_enum_value = self.enum_type[text]

        return current_enum_value


    def set_value(self, value: List[Enum]):
        """ Checks every checkbox that matches the provided Enums in the value parameter. """

        # Iterating over widgets like this is not optimal from a performance perspective.
        for index in range(self.layout.count()):
            layout_item = self.layout.itemAt(index)
            the_widget: QCheckBox = layout_item.widget()

            checkbox_label = the_widget.text()

            # Work-around for placeholder not being deleted yet
            if checkbox_label == "CheckBox":
                continue

            widget_enum_value = self.enum_type[the_widget.text()]

            if widget_enum_value in value:
                the_widget.setChecked(True)

                

    