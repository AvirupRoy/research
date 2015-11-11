# -*- coding: utf-8 -*-
"""
Created on Tue Nov 10 18:16:06 2015

@author: wisp10
"""

from PyQt4.QtGui import QFormLayout, QComboBox
from PyQt4.QtCore import QSettings, pyqtSignal

import PyDaqMx as daq

class AnalogConfigLayout(QFormLayout):
    rangeChanged = pyqtSignal()

    def __init__(self, settings = None, parent = None):
        super(AnalogConfigLayout, self).__init__(parent)
        print "Constructor parent=", parent
        self.deviceCombo = QComboBox()
        self.deviceCombo.setObjectName('deviceCombo')
        self.addRow('&Device', self.deviceCombo)
        self.channelCombo = QComboBox()
        self.channelCombo.setObjectName('channelCombo')
        self.addRow('&Channel', self.channelCombo)
        self.rangeCombo = QComboBox()
        self.rangeCombo.setObjectName('rangeCombo')
        self.addRow('&Range', self.rangeCombo)
        self._ranges = []
        self.deviceCombo.currentIndexChanged.connect(self.deviceChanged)
        self.populateDevices()
        self.rangeCombo.currentIndexChanged.connect(self.rangeChanged)

    def populateDevices(self):
        self.deviceCombo.clear()
        system = daq.System()
        devices = system.findDevices()
        for dev in devices:
            self.deviceCombo.addItem(dev)

    def deviceChanged(self):
        self.rangeCombo.clear()
        self._ranges = self.ranges()
        for r in self._ranges:
            self.rangeCombo.addItem('%+.2f -> %+.2f V' % (r.min, r.max))
        self.channelCombo.clear()
        for channel in self.channels():
            self.channelCombo.addItem(channel)

    def device(self):
        return str(self.deviceCombo.currentText())

    def channel(self):
        return str(self.channelCombo.currentText())

    def voltageRange(self):
        i = self.rangeCombo.currentIndex()
        print "Current index:", i
        if i >= 0:
            return self._ranges[i]
        else:
            return None

    def restoreSettings(self, s = None):
        if s is None:
            s = QSettings()
        device = s.value('device', '', type=str)
        i = self.deviceCombo.findText(device)
        self.deviceCombo.setCurrentIndex(i)
        channel = s.value('channel', '', type=str)
        i = self.channelCombo.findText(channel)
        self.channelCombo.setCurrentIndex(i)
        voltageRange = s.value('range', '', type=str)
        i = self.rangeCombo.findText(voltageRange)
        self.rangeCombo.setCurrentIndex(i)

    def saveSettings(self, s = None):
        if s is None:
            s = QSettings()
        s.setValue('device', self.device())
        s.setValue('channel', self.channel())
        s.setValue('range', self.rangeCombo.currentText())

class AoConfigLayout(AnalogConfigLayout):
    def __init__(self, settings = None, parent = None):
        print "Parent:", parent
        super(AoConfigLayout, self).__init__(parent=parent)

    def channels(self):
        dev = daq.Device(self.device())
        return dev.findAoChannels()

    def ranges(self):
        dev = daq.Device(self.device())
        return dev.voltageRangesAo()


class AiConfigLayout(AnalogConfigLayout):
    def __init__(self, settings = None, parent = None):
        self.couplingCombo = QComboBox()
        super(AiConfigLayout, self).__init__(parent=parent)
        self.addRow('&Coupling', self.couplingCombo)

    def channels(self):
        dev = daq.Device(self.device())
        return dev.findAiChannels()

    def ranges(self):
        dev = daq.Device(self.device())
        return dev.voltageRangesAi()

    def couplings(self):
        dev = daq.Device(self.device())
        return dev.findAiCouplings()

    def deviceChanged(self):
        super(AiConfigLayout,self).deviceChanged()
        self.couplingCombo.clear()
        for coupling in self.couplings():
            self.couplingCombo.addItem(coupling)

