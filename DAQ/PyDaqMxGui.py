# -*- coding: utf-8 -*-
#  Copyright (C) 2012-2015 Felix Jaeckel <fxjaeckel@gmail.com>

#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.

#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.

#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""
Qt-derived GUI elements for PyDaqMx

Created on Tue Nov 10 18:16:06 2015
@author: Felix Jaeckel <fxjaeckel@gmail.com>

"""

from PyQt4.QtGui import QFormLayout, QComboBox, QMenu, QAction, QDoubleSpinBox
from PyQt4.QtCore import QSettings, pyqtSignal
from PyQt4.Qt import Qt
import PyDaqMx as daq

class AnalogConfigLayout(QFormLayout):
    rangeChanged = pyqtSignal()
    def __init__(self, showSampleRateSb = False, settings = None, parent = None):
        super(AnalogConfigLayout, self).__init__(parent)
        self.deviceCombo = QComboBox()
        self.deviceCombo.setObjectName('deviceCombo')
        self.addRow('&Device', self.deviceCombo)
        self.channelCombo = QComboBox()
        self.channelCombo.setObjectName('channelCombo')
        self.addRow('&Channel', self.channelCombo)
        self.rangeCombo = QComboBox()
        self.rangeCombo.setObjectName('rangeCombo')
        self.addRow('&Range', self.rangeCombo)
        if showSampleRateSb:
            self.sampleRateSb = QDoubleSpinBox()
            self.sampleRateSb.setSuffix(' kHz')
            self.sampleRateSb.setMinimum(0.001)
            self.sampleRateSb.setDecimals(3)
            self.sampleRateSb.setValue(1)
            
            self.sampleRateSb.setObjectName('sampleRateSb')
            self.addRow('&Sample rate', self.sampleRateSb)
        else:
            self.sampleRateSb = None
            
        self._ranges = []
        self.deviceCombo.currentIndexChanged.connect(self.deviceChanged)
        self.populateDevices()
        self.rangeCombo.currentIndexChanged.connect(self.rangeChanged)
        self.deviceCombo.setContextMenuPolicy(Qt.CustomContextMenu)
        self.deviceCombo.customContextMenuRequested.connect(self.contextMenu)

    def contextMenu(self, point):
        globalPos = self.deviceCombo.mapToGlobal(point)
        menu = QMenu()
        refreshAction = QAction("&Refresh", menu)
        menu.addAction(refreshAction)
        selected = menu.exec_(globalPos)

        if selected == refreshAction:
            self.populateDevices()

    def populateDevices(self):
        self.deviceCombo.clear()
        system = daq.System()
        devices = system.findDevices()
        for dev in devices:
            self.deviceCombo.addItem(dev)

    def deviceChanged(self):
        self.channelCombo.clear()
        for channel in self.channels():
            self.channelCombo.addItem(channel)
        self.rangeCombo.clear()
        self._ranges = self.ranges()
        for r in self._ranges:
            self.rangeCombo.addItem('%+.2f -> %+.2f V' % (r.min, r.max))
        if self.sampleRateSb is not None:
            fmax = self.maxSampleRate()
            self.sampleRateSb.setMaximum(1E-3*fmax)
            
    def maxSampleRate(self):
        raise NotImplementedError

    def device(self):
        t = self.deviceCombo.currentText()
        if len(t):
            return str(t)
        else:
            return None

    def channel(self):
        return str(self.channelCombo.currentText())

    def voltageRange(self):
        i = self.rangeCombo.currentIndex()
        return None if i < 0 else self._ranges[i]

    def restoreSettings(self, s = None):
        if s is None:
            s = QSettings()
        try:
            device = s.value('device', '', type=str)
            i = self.deviceCombo.findText(device)
            self.deviceCombo.setCurrentIndex(i)
        except:
            pass
        
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
    def __init__(self, showSampleRateSb = False, settings = None, parent = None):
        super(AoConfigLayout, self).__init__(showSampleRateSb, settings, parent=parent)

    def channels(self):
        device = self.device()
        if device is None:
            return []
        dev = daq.Device(device)
        return dev.findAoChannels()

    def ranges(self):
        device = self.device()
        if device is None:
            return []
        dev = daq.Device(device)
        return dev.voltageRangesAo()

    def maxSampleRate(self):
        device = self.device()
        if device is None:
            return []
        aoTask = daq.AoTask('SampleRateTestTask')
        aoChannel = daq.AoChannel(device + '/' + self.channels()[0], 0, 1)
        aoTask.addChannel(aoChannel)
        fmax = aoTask.maxSampleClockRate()
        del aoTask
        del aoChannel
        return fmax


class AiConfigLayout(AnalogConfigLayout):
    def __init__(self, showSampleRateSb = False, settings = None, parent = None):
        self.couplingCombo = QComboBox()
        super(AiConfigLayout, self).__init__(showSampleRateSb, settings, parent=parent)
        self.addRow('&Coupling', self.couplingCombo)
        self.terminalCombo = QComboBox()
        self.terminalCombo.addItem('RSE')
        self.terminalCombo.addItem('NRSE')
        self.terminalCombo.addItem('DIFF')
        self.addRow('&Terminal', self.terminalCombo)
        
    def terminalConfiguration(self):
        t = str(self.terminalCombo.currentText())
        tc = daq.AiChannel.TerminalConfiguration
        terminalConfigDict = {'RSE': tc.RSE, 'DIFF': tc.DIFF, 'NRSE': tc.NRSE}
        return terminalConfigDict[t]

    def channels(self):
        device = self.device()
        if device is None:
            return []
        dev = daq.Device(self.device())
        return dev.findAiChannels()
        
    def ranges(self):
        device = self.device()
        if device is None:
            return []
        dev = daq.Device(device)
        return dev.voltageRangesAi()

    def couplings(self):
        device = self.device()
        if device is None:
            return []
        dev = daq.Device(device)
        return dev.findAiCouplings()
        
    def maxSampleRate(self):
        device = self.device()
        if device is None:
            return []
        with daq.AiTask('SampleRateTestTaskAI') as aiTask:
            channelId = self.channels()[0]
            with daq.AiChannel(device + '/' + channelId, 0, 1) as aiChannel:
                aiTask.addChannel(aiChannel)
                fmax = aiTask.maxSampleClockRate()
                return fmax

    def deviceChanged(self):
        super(AiConfigLayout,self).deviceChanged()
        self.couplingCombo.clear()
        for coupling in self.couplings():
            self.couplingCombo.addItem(coupling)

    def saveSettings(self, s = None):
        if s is None:
            s = QSettings()
        super(AiConfigLayout, self).saveSettings(s)
        s.setValue('terminalConfig', self.terminalCombo.currentText())
        s.setValue('coupling', self.couplingCombo.currentText())
        
    def restoreSettings(self, s = None):
        if s is None:
            s = QSettings()
        super(AiConfigLayout, self).restoreSettings(s)

        x = s.value('terminalConfig', '', type=str)
        i = self.terminalCombo.findText(x)
        self.terminalCombo.setCurrentIndex(i)

        x = s.value('coupling', '', type=str)
        i = self.couplingCombo.findText(x)
        self.couplingCombo.setCurrentIndex(i)


if __name__ == '__main__':
    from PyQt4.QtGui import QApplication, QWidget

    app = QApplication([])
    app.setOrganizationDomain('wisp.physics.wisc.edu')
    app.setApplicationName('DAQ Function Generator')
    app.setApplicationVersion('0.1')
    app.setOrganizationName('McCammon X-ray Astro Physics')
    widget = QWidget()
    widget.setWindowTitle('AO Config Layout')
    layout = AiConfigLayout(showSampleRateSb = True)
    widget.setLayout(layout)
    widget.show()
    app.exec_()
 