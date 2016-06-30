# -*- coding: utf-8 -*-
"""
Created on Fri Dec 04 13:29:25 2015

@author: wisp10
"""

from PyQt4 import QtGui
from PyQt4.QtGui import QAbstractSpinBox, QAbstractButton
from PyQt4.QtCore import QString

def compileUi(baseName):
    '''Compile a *Ui.ui file into a Python *Ui.py file.'''
    from PyQt4 import uic
    uiFileName = '%sUi.ui' % baseName
    pythonFileName = '%sUi.py' % baseName
    
    with open(pythonFileName, 'w') as f:
        print "Compiling UI: ", uiFileName  
        uic.compileUi(uiFileName, f)
        print "Done compiling UI"
    return pythonFileName
        
def compileAndImportUi(baseName):
    import importlib
    pythonFileName = compileUi(baseName)
    print pythonFileName
    moduleName = pythonFileName.split('.py')[0]
    print moduleName
    lib = importlib.import_module(moduleName)
    return lib

def connectAndUpdate(widget, slot):
    '''Connect a widget's valueChanged or checked signals to a slot and also transfer the current state.'''
    if isinstance(widget, QAbstractSpinBox):
        widget.valueChanged.connect(slot)
        v = widget.value()
        slot(v)
    elif isinstance(widget, QAbstractButton):
        widget.toggled.connect(slot)
        v = widget.isChecked()
        slot(v)
    else:
        raise Exception('connectAndUpdate cannot handle %s' % type(widget))

def widgetValue(widget):
    '''A clever little function to obtain the "value" of a widget for any widget of typical types'''
    if isinstance(widget, QtGui.QAbstractSlider) or isinstance(widget, QtGui.QAbstractSpinBox):
        return widget.value()
    elif isinstance(widget, QtGui.QPlainTextEdit):
        return widget.toPlainText()
    elif isinstance(widget, QtGui.QTextEdit) or isinstance(widget, QtGui.QLineEdit):
        return widget.text()
    elif isinstance(widget, QtGui.QComboBox):
        return widget.currentText()
    elif isinstance(widget, QtGui.QAbstractButton):
        return widget.isChecked()
    elif isinstance(widget, QtGui.QGroupBox):
        return widget.isChecked()
    else:
        print"Can't deal with %s" % widget
    
def saveWidgetToSettings(settings, widget, name = None):
    '''Save a widget's value to QSettings. If name is not specified,
    the widgets objectName() will be used as the default key.'''
    if name is None:
        name = widget.objectName()
    settings.setValue(name, widgetValue(widget))
    
def setWidgetValue(widget, value):
    if isinstance(widget, QtGui.QAbstractSlider) or isinstance(widget, QtGui.QSpinBox):
        widget.setValue( value )
    elif isinstance(widget, QtGui.QDoubleSpinBox):
        widget.setValue( value )
    elif isinstance(widget, QtGui.QPlainTextEdit):
        widget.setPlainText( value )
    elif isinstance(widget, QtGui.QTextEdit) or isinstance(widget, QtGui.QLineEdit):
        widget.setText( value )
    elif isinstance(widget, QtGui.QComboBox):
        i = widget.findText( value )
        widget.setCurrentIndex(i)
    elif isinstance(widget, QtGui.QAbstractButton):
        widget.setChecked( value )
    elif isinstance(widget, QtGui.QGroupBox):
        widget.setChecked( value )
    else:
        print"Can't deal with %s" % widget

def restoreWidgetFromSettings(settings, widget, name = None):
    '''Restore a widget's value from QSettings. If name is not specified,
    the widgets objectName() will be used as the default key.'''
    if name is None:
        name = widget.objectName()
    s = settings
    if isinstance(widget, QtGui.QAbstractSlider) or isinstance(widget, QtGui.QSpinBox):
        widget.setValue( s.value(name, widget.value(), type=int) )
    elif isinstance(widget, QtGui.QDoubleSpinBox):
        widget.setValue( s.value(name, widget.value(), type=float) )
    elif isinstance(widget, QtGui.QPlainTextEdit):
        widget.setPlainText( s.value(name, widget.toPlainText(), type=QString) )
    elif isinstance(widget, QtGui.QTextEdit) or isinstance(widget, QtGui.QLineEdit):
        widget.setText( s.value(name, widget.text(), type=QString) )
    elif isinstance(widget, QtGui.QComboBox):
        i = widget.findText( s.value(name, widget.currentText(), type=QString) )
        widget.setCurrentIndex(i)
    elif isinstance(widget, QtGui.QAbstractButton):
        widget.setChecked( s.value(name, widget.isChecked(), type=bool) )
    elif isinstance(widget, QtGui.QGroupBox):
        widget.setChecked( s.value(name, widget.isChecked(), type=bool) )
    else:
        print"Can't deal with %s" % widget
