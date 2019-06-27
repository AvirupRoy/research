# -*- coding: utf-8 -*-
"""
Created on Tue Nov 10 19:33:21 2015

@author: wisp10
"""

from PyQt4 import QtGui, QtDesigner
from analogclock import PyAnalogClock

# See https://wiki.python.org/moin/PyQt/Using_Python_Custom_Widgets_in_Qt_Designer

#_logo_pixmap = QtGui.QPixmap(_logo_16x16_xpm)

#timeZone = QtCore.pyqtProperty("int", getTimeZone, setTimeZone, resetTimeZone)


class PyAnalogClockPlugin(QtDesigner.QPyDesignerCustomWidgetPlugin):

    def __init__(self, parent = None):

        QtDesigner.QPyDesignerCustomWidgetPlugin.__init__(self)

        self.initialized = False

    def initialize(self, core):

        if self.initialized:
            return

        self.initialized = True

    def isInitialized(self):

        return self.initialized

    def createWidget(self, parent):
        return PyAnalogClock(parent)

    def name(self):
        return "PyAnalogClock"

    def group(self):
        return "PyQt Examples"

    def icon(self):
        return QtGui.QIcon(_logo_pixmap)


    def toolTip(self):
        return ""

    def whatsThis(self):
        return ""

   def domXml(self):
        return (
               '<widget class="PyAnalogClock" name=\"analogClock\">\n'
               " <property name=\"toolTip\" >\n"
               "  <string>The current time</string>\n"
               " </property>\n"
               " <property name=\"whatsThis\" >\n"
               "  <string>The analog clock widget displays "
               "the current time.</string>\n"
               " </property>\n"
               "</widget>\n"
               )
    def includeFile(self):
        return "analogclock"

