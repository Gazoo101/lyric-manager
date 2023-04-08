# Python
from enum import Enum

# 3rd Party
from PySide6.QtWidgets import QRadioButton, QLayout
from PySide6.QtCore import QObject, QSettings, Signal

# 1st Party


class WidgetQRadioButtonWithEnum(QObject):
    """ Manages tying a given Enum to a series of radiobuttons within a group layout. """
    anyClicked = Signal()

    def __init__(self,
                 widget_qradiobutton_placeholder: QRadioButton,
                 enum_default_value: Enum,
                 settings_name: str,
                 q_settings: QSettings) -> None:
        """
        Args:
            widget_qradiobutton_placeholder: The placeholder radiobutton widget this class will replace with other
                radiobutton widgets defined by the provided Enum in enum_type.
            enum_default_value: The default enums of type enum_type. / The enum type around which this class generates widgets to populate into the GUI.
            settings_name: The QSettings name to which the selected radio button should be tied.
            q_settings: The QSettings object to/from which settings are saved/loaded.
        """
        QObject.__init__(self)

        self.enum_type = type(enum_default_value)
        self.settings_name = settings_name
        self.q_settings = q_settings

        self.layout: QLayout = widget_qradiobutton_placeholder.parent().layout()

        # Populate GUI layout with all of the values belonging to the provided Enum type.
        for enum_value in self.enum_type:
            widget_radiobutton_to_add = QRadioButton(enum_value.name)
            widget_radiobutton_to_add.clicked.connect(self.anyClicked.emit)

            self.layout.addWidget(widget_radiobutton_to_add)

        widget_qradiobutton_placeholder.deleteLater()


        settings_file_value = self.q_settings.value(settings_name, enum_default_value)
        self.set_value(settings_file_value)



    def get_selected(self) -> Enum:

        # Not ideal for performance reasons
        for index in range(self.layout.count()):
            layout_item = self.layout.itemAt(index)
            the_widget: QRadioButton = layout_item.widget()

            if the_widget.isChecked():
                text = the_widget.text()
                return self.enum_type[text]
            
        return None


    def save_setting(self) -> Enum:
        """ Saves the currently selected choice as an enum to the QSettings object. """
        self.q_settings.setValue(self.settings_name, self.get_selected())


    # def get_value_as_enum(self):
    #     """ Returns the currently selected option in the form of an Enum. """
    #     text = self.widget_combo_box.currentText()
    #     current_enum_value = self.enum_type[text]

    #     return current_enum_value
    

    def set_value(self, value: Enum):
        """ Checks the radio button matching the provided Enum. """

        # Iterating over widgets like this is not optimal from a performance perspective.
        for index in range(self.layout.count()):
            layout_item = self.layout.itemAt(index)
            the_widget: QRadioButton = layout_item.widget()

            if the_widget.text() == value.name:
                the_widget.setChecked(True)

    