# -*- coding: utf-8 -*-
"""
Created on Mon Nov 09 14:45:59 2015

@author: wisp10
"""

from PyQt4 import uic
from PyQt4.QtGui import QWidget

uic.compileUiDir('.')
print "Done"

import FunctionGeneratorUi
import numpy as np
import pyqtgraph as pg

import PyDaqMx as daq

from PyQt4.QtCore import QThread, QSettings, pyqtSignal, QString

#from LabWidgets import LabWidget

class DaqThread(QThread):
    error = pyqtSignal(QString)

    def __init__(self, deviceName, channel, minV, maxV, parent=None):
        super(DaqThread, self).__init__(parent)
        self.deviceName = deviceName
        self.channel = channel
        self.old_phase = 0
        self.phase = 0
        self.minV = minV
        self.maxV = maxV

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
        y = self.amplitude * np.sin(phases) + self.offset
        self.old_phase = (phases[-1] + deltaPhase) % (2.*np.pi)
        return y

    def run(self):
        try:
            self.stopRequested = False
            #dev  = daq.Device(self.deviceName)
            aoChannel = daq.AoChannel('%s/%s' % (self.deviceName, self.channel), self.minV, self.maxV)
            aoTask = daq.AoTask('Output')
            aoTask.addChannel(aoChannel)
            maxRate = aoTask.maxSampleClockRate()
            print "Max rate:", maxRate
            timing = daq.Timing(rate=maxRate)
            self.fSample = timing.rate
            tCovered = 0.05
            self.nSamples = int(tCovered * self.fSample)
            self.x = np.arange(0, self.nSamples)
            timing.setSamplesPerChannel(self.nSamples)
            aoTask.configureTiming(timing)

            startUp = True
            while not self.stopRequested:
                samples = self.generateSamples()
                aoTask.writeData(samples)
                if startUp:
                    aoTask.start()
                    startUp = False
            print "Stopping"
            aoTask.writeData(np.asarray([0.]))
            while not aoTask.isDone():
                pass
            aoTask.stop()
            aoTask.clear()
        except Exception, e:
            self.error.emit(str(e))
            print "Exception", e

def square(phase):
    y = np.zeros_like(phase)
    y[phase<np.pi] = -1
    y[phase>=np.pi] = 1
    return y



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

        self.amplitudeSb.valueChanged.connect(self.updateLimits)

        self.restoreSettings()

    def updateLimits(self):
        r = self.aoConfigLayout.voltageRange()
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
        if self.thread is not None:
            self.thread.updateParameters(a, f, np.deg2rad(degree), offset)
        T = 1./f
        t = np.linspace(0, 2*T)
        y = a*np.sin(2.*np.pi*f*t+np.deg2rad(degree))+offset
        self.curve.setData(t, y)

        print "Update waveform"

if __name__ == '__main__':
    from PyQt4.QtGui import QApplication

    app = QApplication([])
    app.setOrganizationDomain('wisp.physics.wisc.edu')
    app.setApplicationName('DAQ Function Generator')
    app.setApplicationVersion('0.1')
    app.setOrganizationName('McCammon X-ray Astro Physics')
    widget = FunctionGeneratorWidget()
    widget.show()
    app.exec_()
