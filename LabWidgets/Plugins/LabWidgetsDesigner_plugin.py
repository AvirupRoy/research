# -*- coding: utf-8 -*-
"""
Plugins for the Qt Designer to show some of our custom widgets in the palette.
This file needs to be copied to C:\Python27\Lib\site-packages\PyQt4\plugins\designer\python 
to be available system wide for the PyQt plugin loader may find it when starting Qt Designer.
Created on Fri Mar 25 13:05:32 2016

@author: Felix Jaeckel <felix.jaeckel@wisc.edu>
"""

#from PyQt4 import QtCore, QtGui
from PyQt4.QtDesigner import QPyDesignerCustomWidgetPlugin

from LabWidgets.Indicators import SiDoubleSpinBox, LedIndicator, EngineeringIndicator, TemperatureIndicator

group = 'Lab Widgets'

class SiDoubleSpinBoxPlugin(QPyDesignerCustomWidgetPlugin):
    def createWidget(self, parent):
        return SiDoubleSpinBox(parent)

    def name(self):
        return "SiDoubleSpinBox"
        
    def group(self):
        return group
        
    def toolTip(self):
        return "A QDoubleSpinBox with built-in conversion factor to and from SI"
        
    def whatsThis(self):
        return self.toolTip()
        
    def isContainer(self):
        return False

#    def domXml(self):
#        return '<widget class="SiDoubleSpinBox" name="Sb" />\n'
        
    def includeFile(self):
        return "LabWidgets.Indicators"


class LedIndicatorPlugin(QPyDesignerCustomWidgetPlugin):
    def createWidget(self, parent):
        return LedIndicator(parent)

    def name(self):
        return "LedIndicator"

    def group(self):
        return group

    def includeFile(self):
        return "LabWidgets.Indicators"
        
class EngineeringIndicatorPlugin(QPyDesignerCustomWidgetPlugin):
    def createWidget(self, parent):
        return EngineeringIndicator(parent)

    def name(self):
        return "EngineeringIndicator"

    def group(self):
        return group

    def includeFile(self):
        return "LabWidgets.Indicators"

class TemperatureIndicatorPlugin(QPyDesignerCustomWidgetPlugin):
    def createWidget(self, parent):
        return TemperatureIndicator(parent)

    def name(self):
        return "TemperatureIndicator"

    def group(self):
        return group

    def includeFile(self):
        return "LabWidgets.Indicators"
        
if __name__ == '__main__':
    from PyQt4.QtGui import QApplication
    app = QApplication([])
    plugin = SiDoubleSpinBoxPlugin()
    #plugin = LedIndicatorPlugin()
    w = plugin.createWidget(parent=None)
    w.setWindowTitle(plugin.name())
    w.show()
    app.exec_()
