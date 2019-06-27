# -*- coding: utf-8 -*-
"""
Widgets (QWidget derived) providing a silent setValue/setText method that does not emit a valueChanged signal.
Created on Mon Dec 03 15:23:47 2012

@author: Felix Jaeckel <fxjaeckel@gmail.com>
"""

from PyQt4.QtGui import QSpinBox, QDoubleSpinBox, QComboBox, QPushButton, QToolButton, QGroupBox, QCheckBox
from PyQt4.QtCore import pyqtSlot, pyqtSignal
import warnings

class SilentSpinBox(QSpinBox):
    @pyqtSlot(float)
    def setValueSilently(self, value):
        '''Call this slot, if you do not want to generate valueChanged signals'''
        old = self.blockSignals(True)
        self.setValue(value)
        self.blockSignals(old)

class SilentDoubleSpinBox(QDoubleSpinBox):
    @pyqtSlot(float)
    def setValueSilently(self, value):
        '''Call this slot, if you do not want to generate valueChanged signals'''
        old = self.blockSignals(True)
        self.setValue(value)
        self.blockSignals(old)

class SilentToolButton(QToolButton):
    @pyqtSlot(bool)
    def setCheckedSilently(self, checked):
        '''Call this slot, if you do not want to generate currentIndexChange signals'''
        old = self.blockSignals(True)
        self.setChecked(checked)
        self.blockSignals(old)

class SilentPushButton(QPushButton):
    @pyqtSlot(bool)
    def setCheckedSilently(self, checked):
        '''Call this slot, if you do not want to generate currentIndexChange signals'''
        old = self.blockSignals(True)
        self.setChecked(checked)
        self.blockSignals(old)

class SilentCheckBox(QCheckBox):
    @pyqtSlot(bool)
    def setCheckedSilently(self, checked):
        '''Call this slot, if you do not want to generate currentIndexChange signals'''
        old = self.blockSignals(True)
        self.setChecked(checked)
        self.blockSignals(old)

class SilentGroupBox(QGroupBox):
    @pyqtSlot(bool)
    def setCheckedSilently(self, checked):
        '''Call this slot, if you do not want to generate currentIndexChange signals'''
        old = self.blockSignals(True)
        self.setChecked(checked)
        self.blockSignals(old)

class SilentComboBox(QComboBox):
    @pyqtSlot(int)
    def setCurrentIndexSilently(self, index):
        '''Call this slot, if you do not want to generate currentIndexChange signals'''
        old = self.blockSignals(True)
        self.setCurrentIndex(index)
        self.blockSignals(old)

class EnumComboBox(SilentComboBox):
    '''EnumComboBox is intended to be populated from a SettingsEnum. For convenience, it emits signal currentEnumChanged(code) with the enum.Code as the parameter.'''
    currentEnumChanged = pyqtSignal(int)
    def __init__(self, parent = None):
        super(EnumComboBox, self).__init__(parent)
        self.currentIndexChanged.connect(self._emitEnumSignal)

    @pyqtSlot(int)
    def _emitEnumSignal(self, index):
        enumCode = self.itemData(index).toInt()[0]
        self.currentEnumChanged.emit(enumCode)

    def setCurrentEnumSilently(self, enumCode):
        '''The the current enum selection, without generating signals.'''
        index = self.findData(enumCode)
        self.setCurrentIndexSilently(index)
        if index < 0:
            warnings.warn('Item not found in EnumComboBox')

    def populateFromEnum(self, enum):
        '''Populate the combo-box from a SettingsEnum'''
        self.clear()
        for s in enum.strings():
            self.addItem(s, enum.fromString(s).Code)
