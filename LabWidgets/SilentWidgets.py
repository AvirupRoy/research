# -*- coding: utf-8 -*-
"""
Created on Mon Dec 03 15:23:47 2012

@author: jaeckel
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

class SiIndicator():
    SI = {1E-15: 'f', 1E-12: 'p', 1E-9: 'n', 1E-6: ''}
    pass

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

class SilentGroupBox(QGroupBox):
    checkStateChanged = pyqtSignal(bool)

    def __init__(self, parent=0):
        QGroupBox.__init__(self)
        self.checkStateChanged.connect(self.onStateChanged)

    @pyqtSlot(bool)
    def setCheckedSilently(self, checked):
        '''Call this slot, if you do not want to generate currentIndexChange signals'''
        old = self.blockSignals(True)
        self.setChecked(checked)
        self.blockSignals(old)

    @pyqtSlot(int)
    def onStateChanged(self,state):
        if state==0:
            self.checkStateChanged.emit(False)
        elif state==2:
            self.checkStateChanged.emit(True)

class SilentCheckBox(QCheckBox):
    checkStateChanged = pyqtSignal(bool)

    def __init__(self, parent=0):
        QCheckBox.__init__(self)
        self.stateChanged.connect(self.onStateChanged)

    @pyqtSlot(bool)
    def setCheckedSilently(self, checked):
        '''Call this slot, if you do not want to generate currentIndexChange signals'''
        old = self.blockSignals(True)
        self.setChecked(checked)
        self.blockSignals(old)

    @pyqtSlot(int)
    def onStateChanged(self,state):
        if state==0:
            self.checkStateChanged.emit(False)
        elif state==2:
            self.checkStateChanged.emit(True)


class SilentComboBox(QComboBox):
    @pyqtSlot(int)
    def setCurrentIndexSilently(self, index):
        '''Call this slot, if you do not want to generate currentIndexChange signals'''
        old = self.blockSignals(True)
        self.setCurrentIndex(index)
        self.blockSignals(old)


class EnumComboBox(SilentComboBox):
    '''EnumComboBox is intended to be populated from a SettingsEnum. For convenience, it emits signal currentEnumChanged(code) with the enum.Code as the parameter.'''
    currentCodeChanged = pyqtSignal(int)
    def __init__(self, parent = None):
        super(EnumComboBox, self).__init__(parent)
        self.currentIndexChanged.connect(self._emitEnumSignal)

    @pyqtSlot(int)
    def _emitEnumSignal(self, index):
        enumCode = self.itemData(index).toInt()[0]
        self.currentCodeChanged.emit(enumCode)
        
    def itemCode(self, index):
        code = self.itemData(index).toInt()[0]
        return code
        
    def currentCode(self):
        i = self.currentIndex()
        return self.itemCode(i)

    def setCurrentCodeSilently(self, enumCode):
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
