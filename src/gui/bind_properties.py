from PySide6.QtCore import QObject

# Explain here
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

def bind_property_window_settings(objectName, propertyName):

    def getter(self):
        return self.widget_window_settings.findChild(QObject, objectName).property(propertyName)
        
    def setter(self, value):
        self.widget_window_settings.findChild(QObject, objectName).setProperty(propertyName, value)
    
    return property(getter, setter)


def bind_property_window_main(objectName, propertyName):

    def getter(self):
        return self.widget_window_main.findChild(QObject, objectName).property(propertyName)
        
    def setter(self, value):
        self.widget_window_main.findChild(QObject, objectName).setProperty(propertyName, value)
    
    return property(getter, setter)