# -*- coding: utf-8 -*-
"""
Created on Fri Dec 04 13:29:25 2015

@author: wisp10
"""

from PyQt4 import QtGui
from PyQt4.QtGui import QAbstractSpinBox, QAbstractButton
from PyQt4.QtCore import QString

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

def saveWidgetToSettings(settings, widget):
    name = widget.objectName()
    s = settings
    if isinstance(widget, QtGui.QAbstractSlider) or isinstance(widget, QtGui.QAbstractSpinBox):
        s.setValue(name, widget.value())
    elif isinstance(widget, QtGui.QPlainTextEdit):
        s.setValue(name, widget.toPlainText())
    elif isinstance(widget, QtGui.QTextEdit) or isinstance(widget, QtGui.QLineEdit):
        s.setValue(name, widget.text())
    elif isinstance(widget, QtGui.QComboBox):
        s.setValue(name, widget.currentText())
    elif isinstance(widget, QtGui.QAbstractButton):
        s.setValue(name, widget.isChecked())
    elif isinstance(widget, QtGui.QGroupBox):
        s.setValue(name, widget.isChecked())
    else:
        print"Can't deal with %s" % widget

def restoreWidgetFromSettings(settings, widget):
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
