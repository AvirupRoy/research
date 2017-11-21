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
A function generator example for PyDaqMx, using PyQt4 and pyqtgraph for the GUI
Continuously generates sample to allow for (almost) live updates to the function.
Created on Mon Nov 09 14:45:59 2015
@author: Felix Jaeckel <fxjaeckel@gmail.com>

"""

from LabWidgets.Utilities import compileUi
compileUi('FunctionGeneratorUi')
import FunctionGeneratorUi

from PyQt4.QtGui import QWidget

import numpy as np
import pyqtgraph as pg
import PyDaqMx as daq

from PyQt4.QtCore import QThread, QSettings, pyqtSignal
try:
    from PyQt4.QtCore import QString
except ImportError:
    QString = str

from scipy import signal
def triangle(phase):
    y = signal.sawtooth(phase, 0.5)
    return y
    
def sawtooth(phase):
    y = signal.sawtooth(phase,0)
    return y
    
def square(phase):
    y = np.empty_like(phase)
    i = np.mod(phase, 2*np.pi) < np.pi
    y[i] = 1
    y[~i] = -1
    return y

class DaqThread(QThread):
    error = pyqtSignal(QString)
    packetGenerated = pyqtSignal(int)
    SupportedWaveforms = ['Sine', 'Triangle', 'Sawtooth', 'Square']
    
    def __init__(self, deviceName, channel, minV, maxV, parent=None):
        super(DaqThread, self).__init__(parent)
        self.deviceName = deviceName
        self.channel = channel
        self.old_phase = 0
        self.phase = 0
        self.minV = minV
        self.maxV = maxV
        self.setWaveform('Sine')
        
    def setWaveform(self, waveform):
        if not waveform in self.SupportedWaveforms:
            raise Exception('Unsupported waveform')
        if waveform == 'Sine':
            self.wave = np.sin
        elif waveform == 'Triangle':
            self.wave = triangle
        elif waveform == 'Sawtooth':
            self.wave = sawtooth
        elif waveform == 'Square':
            self.wave = square

    def updateParameters(self, amplitude, f, phase, offset):
        self.amplitude = amplitude
        self.f = f
        self.old_phase = self.old_phase + (phase - self.phase)
        self.phase = phase
        self.offset = offset

    def stop(self):
        self.stopRequested = True

    def generateSamples(self):
        deltaPhase = 2*np.pi*self.f/self.fSample
        phases = self.old_phase + deltaPhase*self.x
        y = self.amplitude * self.wave(phases) + self.offset
        self.old_phase = (phases[-1] + deltaPhase) % (2.*np.pi)
        return y

    def run(self):
        try:
            self.stopRequested = False
            aoChannel = daq.AoChannel('%s/%s' % (self.deviceName, self.channel), self.minV, self.maxV)
            aoTask = daq.AoTask('Output')
            aoTask.addChannel(aoChannel)
            maxRate = aoTask.maxSampleClockRate()
            print "Max rate:", maxRate
            timing = daq.Timing(rate=maxRate)
            self.fSample = timing.rate
            tCovered = 0.1
            self.nSamples = int(tCovered * self.fSample)
            self.x = np.arange(0, self.nSamples)
            timing.setSamplesPerChannel(self.nSamples)
            aoTask.configureTiming(timing)

            startUp = True
            i = 1
            while not self.stopRequested:
                samples = self.generateSamples()
                aoTask.writeData(samples)
                self.packetGenerated.emit(i)
                i += 1

                if startUp:
                    aoTask.start()
                    startUp = False
            print "Stopping"
            aoTask.writeData(np.asarray([0.]))
            aoTask.stop()
            aoTask.clear()
        except Exception, e:
            self.error.emit(str(e))
            print "Exception", e

from PyDaqMxGui import AoConfigLayout

class FunctionGeneratorWidget(FunctionGeneratorUi.Ui_Form, QWidget):
    def __init__(self, parent = None):
        super(FunctionGeneratorWidget, self).__init__(parent)
        self.setupUi(self)
        self.thread = None
        self.aoConfigLayout = AoConfigLayout(parent=self.aoGroupBox)
        self.aoConfigLayout.rangeChanged.connect(self.updateLimits)

        self.curve = pg.PlotCurveItem()
        self.plot.addItem(self.curve)
        self.plot.setLabel('left', 'voltage', units='V')
        self.plot.setLabel('bottom', 'time', units='s')
        self.updateWaveform()
        self.startPb.clicked.connect(self.startGeneration)

        for control in [self.amplitudeSb, self.frequencySb, self.phaseSb, self.offsetSb]:
            control.valueChanged.connect(self.updateWaveform)
        self.waveformCombo.currentIndexChanged.connect(self.updateWaveform)

        self.amplitudeSb.valueChanged.connect(self.updateLimits)

        self.restoreSettings()

    def updateLimits(self):
        r = self.aoConfigLayout.voltageRange()
        if r is not None:
            vmin = r.min; vmax = r.max
            self.amplitudeSb.setMaximum(min(abs(vmin),abs(vmax)))
            a = self.amplitudeSb.value()
            self.offsetSb.setMaximum(vmax-a)
            self.offsetSb.setMinimum(vmin+a)

    def restoreSettings(self):
        s = QSettings()
        self.amplitudeSb.setValue(s.value('amplitude', 1.0, type=float))
        self.frequencySb.setValue(s.value('frequency', 10.0, type=float))
        self.phaseSb.setValue(s.value('phase', 0.0, type=float))
        self.offsetSb.setValue(s.value('offset', 0.0, type=float))
        self.aoConfigLayout.restoreSettings(s)

    def saveSettings(self):
        s = QSettings()
        s.setValue('amplitude', self.amplitudeSb.value())
        s.setValue('frequency', self.frequencySb.value())
        s.setValue('phase', self.phaseSb.value())
        s.setValue('offset', self.offsetSb.value())
        self.aoConfigLayout.saveSettings(s)

    def closeEvent(self, e):
        if self.thread is not None:
            self.thread.stop()
        self.saveSettings()
        super(FunctionGeneratorWidget, self).closeEvent(e)

    def startGeneration(self):
        vRange = self.aoConfigLayout.voltageRange()
        self.errorLog.clear()
        thread = DaqThread(self.aoConfigLayout.device(), self.aoConfigLayout.channel(), vRange.min,vRange.max, parent=self)
        thread.error.connect(self.errorLog.append)
        thread.packetGenerated.connect(self.chunkCounter.display)
        self.stopPb.clicked.connect(thread.stop)

        self.thread = thread
        self.updateWaveform()
        thread.start()
        self.enableControls(False)
        thread.finished.connect(self.threadFinished)

    def threadFinished(self):
        self.enableControls(True)

    def enableControls(self, enable = True):
        self.startPb.setEnabled(enable)
        self.aoConfigLayout.setEnabled(enable)
        self.stopPb.setEnabled(not enable)

    def updateWaveform(self):
        a = self.amplitudeSb.value()
        f = self.frequencySb.value()
        degree = self.phaseSb.value()
        offset = self.offsetSb.value()
        waveform = self.waveformCombo.currentText()
        if waveform == 'Sine':
            wave = np.sin
        elif waveform == 'Triangle':
            wave = triangle
        elif waveform == 'Sawtooth':
            wave = sawtooth
        elif waveform == 'Square':
            wave = square
        if self.thread is not None:
            self.thread.updateParameters(a, f, np.deg2rad(degree), offset)
            self.thread.setWaveform(waveform)
        T = 1./f
        t = np.linspace(0, 2.*T, 1000)
        y = a*wave(2.*np.pi*f*t+np.deg2rad(degree))+offset
        self.curve.setData(t, y)


if __name__ == '__main__':
    from PyQt4.QtGui import QApplication

    app = QApplication([])
    app.setOrganizationDomain('wisp.physics.wisc.edu')
    app.setApplicationName('DAQ Function Generator')
    app.setApplicationVersion('0.1')
    app.setOrganizationName('McCammon X-ray Astro Physics')
    widget = FunctionGeneratorWidget()
    widget.setWindowTitle('DAQmx Function Generator')
    widget.show()
    app.exec_()
