# -*- coding: utf-8 -*-
"""
A spectrum analyzer window. Independent of hardware, it receives data from the actual DAQ programs
via Zmq interface.
Created on Tue Mar 08 14:35:04 2016
@author: Felix Jaeckel <felix.jaeckel@wisc.edu>
"""

from PyQt4 import QtGui
from PyQt4.QtCore import QSettings, QThread, pyqtSignal
from PyQt4 import uic
import pyqtgraph as pg
import numpy as np
import time
with open('SpectrumAnalyzerUi.py', 'w')  as of:
    uic.compileUi('SpectrumAnalyzerUi.ui', of)

import matplotlib.mlab as mlab
import SpectrumAnalyzerUi as ui

from Zmq.Zmq import ZmqSubscriber
from Zmq.Ports import PubSub

class SpectrumAnalyzerWidget(ui.Ui_Form, QtGui.QWidget):
    WindowFunctions = {'Hanning': mlab.window_hanning, 'Blackman': np.blackman, 'Hamming':np.hamming, 'Bartlett': np.bartlett}
    DetrendFunctions = {'None': mlab.detrend_none, 'Mean': mlab.detrend_mean, 'Linear': mlab.detrend_linear}
    Sources = {'Legacy DAQ': PubSub.LegacyDaqStreaming, 'DAQmx': 0, 'Tektronix Scope': PubSub.TektronixScope}
    
    def __init__(self):
        super(SpectrumAnalyzerWidget, self).__init__()
        self.setupUi(self)
        self.saveWidgets = []
        self.populateUi()
        self.runPb.clicked.connect(self.run)
        self.curve = pg.PlotCurveItem()
        self.waveformPlot.addItem(self.curve)
        self.waveformPlot.setLabel('left', 'voltage', units='V')
        self.waveformPlot.setLabel('bottom', 'time', units='s')
        
        self.curveSpectrum = pg.PlotCurveItem()
        self.spectrumPlot.addItem(self.curveSpectrum)
        self.spectrumPlot.setLabel('left', 'Noise', units='V/rtHz')
        self.spectrumPlot.setLabel('bottom', 'f', units='Hz')
        self.spectrumPlot.setLogMode(x=True, y=True)
        self.restoreSettings()
        self.f = None
        self.subscriber = None
        self.resetPb.clicked.connect(self.reset)
        self.updateChannels()
        self.restoreSettings()
        
    def restoreSettings(self):
        for w in self.saveWidgets:
            pass
        
    def saveSettings(self):
        pass
        
    def populateUi(self):
        self.windowCombo.addItems(self.WindowFunctions.keys())
        self.detrendCombo.addItems(self.DetrendFunctions.keys())
        self.savePb.clicked.connect(self.save)
        self.sourceCombo.addItems(self.Sources.keys())
        self.sourceCombo.currentIndexChanged.connect(self.updateChannels)
        
    def updateChannels(self):
        old = self.channelCombo.currentText()        
        self.channelCombo.clear()
        source = self.sourceCombo.currentText()
        if source == 'Legacy DAQ':
            self.sampleRate = 204800
            self.channelCombo.addItems(['Channel0', 'Channel1', 'Channel2', 'Channel3'])
        elif source == 'Tektronix Scope':
            self.channelCombo.addItems(['CH1', 'CH2', 'CH3', 'CH4'])
            self.sampleRate = 1./(1E-3/1E4)
            
        self.channelCombo.setCurrentIndex(self.channelCombo.findText(old))
        
    def save(self):
        print "Save"
        
    def run(self):
        if self.subscriber is not None:
            self.stopThread()
            return
            
        self.runPb.setText('Stop')
        self.window = self.WindowFunctions[str(self.windowCombo.currentText())]
        self.detrend = self.DetrendFunctions[str(self.detrendCombo.currentText())]
        self.reset()
        source = self.sourceCombo.currentText()
        if source == 'Legacy DAQ':
            subscriber = ZmqSubscriber(host='tcp://wisp10.physics.wisc.edu', port=PubSub.LegacyDaqStreaming)
        elif source == 'Tektronix Scope':
            subscriber = ZmqSubscriber(host='tcp://wisp10.physics.wisc.edu', port=PubSub.TektronixScope)
        subscriber.floatReceived.connect(self.updateFloat)
        subscriber.arrayReceived.connect(self.collectData)
        self.subscriber = subscriber
        subscriber.start()
        subscriber.finished.connect(self.finished)
        
    def stopThread(self):
        if self.subscriber is not None:
            self.subscriber.stop()
            self.subscriber.wait(1000)        
            del self.subscriber
            self.subscriber = None
            
    def finished(self):
        self.runPb.setText('Run')
            
    def updateFloat(self, name, value):
        print name, value
        
    def collectData(self, name, samples):
        #print "Time:", t
        print "Name:", name
        if name != str(self.channelCombo.currentText()):
            return
            
        dt = 1./self.sampleRate
        print "Samples:", samples.shape
        
        t = np.arange(0, len(samples)*dt, dt)
        samples = self.detrend(samples)
        self.curve.setData(x=t,y=samples)

        #nfft = min(self.resolution, len(samples))
        nfft = len(samples)
        (psd, f) = mlab.psd(samples, NFFT=nfft, Fs = self.sampleRate, window=self.window, noverlap=3*nfft/4, detrend=mlab.detrend_none)
        if self.f is not None and f.shape == self.f.shape and np.all(f == self.f):
            if self.averagingCombo.currentText() == 'linear':
                self.averagePsd = (self.psdCount*self.averagePsd + psd)/(self.psdCount+1)
            else:
                alpha = 1./self.decaySb.value()
                self.averagePsd = alpha*psd + (1-alpha)*self.averagePsd
        else:
            self.psdCount = 0
            self.averagePsd = psd
            self.f = f
            
        self.psdCount += 1
        self.curveSpectrum.setData(x=np.log10(f[1:]), y=np.log10(np.sqrt(self.averagePsd[1:])))
        self.countSb.setValue(self.psdCount)
        #self.spectrumPlot.setRange(xRange=[0.1,fmax])

    def reset(self):
        self.f = None
        self.curveSpectrum.setData(x=[], y=[])
        self.countSb.setValue(0)

    def closeEvent(self, e):
        self.stopThread()
        self.saveSettings()
        super(SpectrumAnalyzerWidget, self).closeEvent(e)
        
if __name__ == '__main__':
    from PyQt4.QtGui import QApplication

    app = QApplication([])
    app.setOrganizationDomain('wisp.physics.wisc.edu')
    app.setApplicationName('DAQ Spectrum Analyzer')
    app.setApplicationVersion('0.1')
    app.setOrganizationName('McCammon X-ray Astro Physics')
    widget = SpectrumAnalyzerWidget()
    widget.setWindowTitle('DAQ Spectrum Analyzer')
    widget.show()
    app.exec_()
